"""
국가별 공휴일 JSON(holiday_list_{code}.json) 생성 스크립트.

이 저장소(CalendarHoliday)가 공휴일 데이터의 단일 소스다. 여기서 생성 → 커밋 → GitHub push
하면 raw.githubusercontent.com을 통해 MyCalendar 앱이 런타임에 그대로 받아간다. MyCalendar
저장소에는 더 이상 생성 로직이 없고, 앱에 내장할 스냅샷이 필요할 때
`sync_holidays_from_calendarholiday.py`(MyCalendar 저장소)로 이 저장소의 결과물을 복사해간다.

- Nager.Date(date.nager.at)가 지원하는 국가 중 38개국은 Nager를 우선 사용 (global=true &
  Public 타입만 채택 — 문화적 기념일이 섞이지 않은 정제된 데이터).
- Nager 미지원 또는 데이터 결측 8개국(tw, th, my, in, il, sa, ae, vn)은 Google Calendar
  공휴일 캘린더에서 생성. vn은 Nager 자체 지원국이지만 음력 공휴일(뗏, 훙브엉기념일)이
  통째로 빠져있어 여기로 옮김.
- holiday_excludes.json에 등록된 이름과 일치하는 항목은 모든 연도에서 제거(원본이 실제로는
  공휴일이 아닌데 진짜 공휴일과 구분 안 되게 태깅한 경우, 사람이 한 번 확인해서 등록).
- holiday_overrides.json에 등록된 국가/연도별 예외(임시공휴일 등 두 소스 모두 놓치는 항목)를
  마지막에 병합.

API 키는 코드에 넣지 않고 GOOGLE_API_KEY 환경변수 또는 .google_api_key 파일(git 추적 제외)에서
읽는다.
"""
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR  # 이 저장소 루트 = raw.githubusercontent가 서빙하는 경로
OVERRIDES_FILE = SCRIPT_DIR / 'holiday_overrides.json'
EXCLUDES_FILE = SCRIPT_DIR / 'holiday_excludes.json'
API_KEY_FILE = SCRIPT_DIR / '.google_api_key'

START_YEAR = 2015
END_YEAR = 2035

# 국가 자체가 이 연도 이전엔 지금 형태로 존재하지 않았던 경우(소련 해체 등)만 국가 전체를
# 컷오프한다. 단순히 공휴일 한두 개가 최근에 생긴 경우는 국가를 통째로 자르면 멀쩡한 나머지
# 데이터까지 버리게 되므로, 그런 경우는 holiday_excludes.json의 from_year로 개별 처리한다
# (2026-09-20 46개국 역사 조사 결과 — 상세 근거는 refactoring-log.md 참고).
COUNTRY_START_YEAR_OVERRIDES = {
    'ru': 1992,  # 소련 해체(1991.12) 이전엔 "러시아 연방" 자체가 없었음
    'ua': 1991,  # 소련에서 독립(1991.8)
}

# Nager.Date 지원국 중 실제 채택 38개국: 우리 국가코드 -> Nager countryCode
# (vn 제외: Nager에 베트남 음력 공휴일(뗏 연휴, 훙브엉기념일)이 전혀 없어서 Google Calendar로
#  되돌림. 2026-09-11 확인: CN/HK 등 다른 음력 국가는 Nager에도 정상 반영되어 있어 VN만의
#  결측으로 보임.)
NAGER_COUNTRIES = {
    'kr': 'KR', 'jp': 'JP', 'cn': 'CN', 'hk': 'HK', 'id': 'ID',
    'sg': 'SG', 'ph': 'PH', 'au': 'AU', 'nz': 'NZ',
    'us': 'US', 'ca': 'CA', 'mx': 'MX', 'br': 'BR', 'ar': 'AR', 'cl': 'CL',
    'co': 'CO', 'pe': 'PE',
    'gb': 'GB', 'ie': 'IE', 'fr': 'FR', 'de': 'DE', 'at': 'AT', 'ch': 'CH',
    'it': 'IT', 'es': 'ES', 'pt': 'PT', 'nl': 'NL', 'be': 'BE', 'se': 'SE',
    'no': 'NO', 'dk': 'DK', 'fi': 'FI', 'ru': 'RU', 'ua': 'UA', 'pl': 'PL',
    'tr': 'TR',
    'eg': 'EG', 'za': 'ZA',
}

# Nager 미지원(또는 데이터 결측으로 제외) 8개국: Google Calendar 방식
GOOGLE_ONLY_CALENDARS = {
    'tw': {'id': 'zh-tw.taiwan#holiday@group.v.calendar.google.com'},
    'th': {'id': 'th.th#holiday@group.v.calendar.google.com'},
    'my': {'id': 'en.malaysia#holiday@group.v.calendar.google.com'},
    'in': {'id': 'en.indian#holiday@group.v.calendar.google.com'},
    'il': {'id': 'iw.jewish#holiday@group.v.calendar.google.com'},
    'vn': {'id': 'vi.vietnamese#holiday@group.v.calendar.google.com'},
    'sa': {'id': 'ar.saudiarabian#holiday@group.v.calendar.google.com'},
    'ae': {'id': 'ar.ae#holiday@group.v.calendar.google.com'},
}


def load_google_api_key():
    env_key = os.environ.get('GOOGLE_API_KEY', '').strip()
    if env_key:
        return env_key
    if API_KEY_FILE.is_file():
        key = API_KEY_FILE.read_text(encoding='utf-8').strip()
        if key:
            return key
    return None


def load_overrides():
    if not OVERRIDES_FILE.is_file():
        return {}
    with open(OVERRIDES_FILE, encoding='utf-8') as f:
        return json.load(f)


def load_excludes():
    if not EXCLUDES_FILE.is_file():
        return {}
    with open(EXCLUDES_FILE, encoding='utf-8') as f:
        return json.load(f)


def apply_excludes(holidays_by_year, exclude_rules):
    """국가 원본 소스가 실제로는 공휴일이 아닌데 같은 방식으로 태깅해버린 항목, 또는 실제로는
    특정 연도부터 제정된 공휴일인데 소스가 모든 연도에 동일하게 보여주는 항목(예: 독일 통일의
    날은 1990년부터인데 소스는 1976년에도 보여줌)을 걷어낸다. 각 항목은 이름 문자열(모든
    연도에서 제거) 또는 {"name": ..., "from_year": N}(그 연도부터는 유지, 이전 연도에서만
    제거) 둘 다 가능 (holiday_excludes.json 참고)."""
    if not exclude_rules:
        return
    always_exclude = set()
    from_year_by_name = {}
    for rule in exclude_rules:
        if isinstance(rule, str):
            always_exclude.add(rule)
        else:
            from_year_by_name[rule['name']] = rule['from_year']

    for year, entries in holidays_by_year.items():
        year_int = int(year)
        holidays_by_year[year] = [
            h for h in entries
            if h['name'] not in always_exclude
            and not (h['name'] in from_year_by_name and year_int < from_year_by_name[h['name']])
        ]


def apply_overrides(holidays_by_year, country_overrides):
    for year, extra_list in country_overrides.items():
        existing = holidays_by_year.setdefault(year, [])
        seen = {(h['date'], h['name']) for h in existing}
        for extra in extra_list:
            key = (extra['date'], extra['name'])
            if key not in seen:
                existing.append(extra)
                seen.add(key)
        existing.sort(key=lambda h: h['date'])


def load_committed_holidays(country_code):
    """이전에 커밋된 결과물을 읽어온다(없으면 빈 dict) — 이번 조회가 빈 응답으로 와서
    덮어쓰기 전에 비교할 기준."""
    path = OUTPUT_DIR / f'holiday_list_{country_code}.json'
    if not path.is_file():
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f).get('holidays', {})


def restore_empty_years(country_code, holidays_by_year):
    """소스가 '그 해엔 진짜 공휴일이 없다'와 '그 해 데이터를 못 준다'(연도 범위 밖, 일시적
    실패 등)를 구분하지 않고 둘 다 빈 배열로 응답하는 경우가 있다. 새로 받은 값이 비어 있는데
    이전에 커밋된 값엔 데이터가 있었다면, 실제로 공휴일이 없어진 게 아니라 이번 조회가 그 해
    데이터를 못 준 것으로 보고 기존 값을 유지한다(덮어쓰기로 인한 데이터 유실 방지)."""
    committed = load_committed_holidays(country_code)
    restored_years = []
    for year, entries in holidays_by_year.items():
        if not entries and committed.get(year):
            holidays_by_year[year] = committed[year]
            restored_years.append(year)
    if restored_years:
        print(f'  ℹ️ 빈 응답이라 기존 데이터 유지: {", ".join(restored_years)}')


def _escape(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')


def write_json(country_code, holidays_by_year):
    """휴일 한 건 = 한 줄 형식으로 사람이 보기 편하게 저장."""
    lines = [
        '{',
        '  "meta": {',
        f'    "country": "{country_code.upper()}",',
        '    "version": 1',
        '  },',
        '  "holidays": {',
    ]

    years = list(holidays_by_year.keys())
    for i, year in enumerate(years):
        lines.append(f'    "{year}": [')
        days = holidays_by_year[year]
        for j, day in enumerate(days):
            comma = ',' if j < len(days) - 1 else ''
            lines.append(
                f'      {{ "date": "{_escape(day["date"])}", "name": "{_escape(day["name"])}" }}{comma}'
            )
        year_comma = ',' if i < len(years) - 1 else ''
        lines.append(f'    ]{year_comma}')

    lines.append('  }')
    lines.append('}')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f'holiday_list_{country_code}.json'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')
    return path


# --- Nager.Date 소스 ---

def fetch_nager_year(nager_code, year):
    url = f'https://date.nager.at/api/v3/PublicHolidays/{year}/{nager_code}'
    response = requests.get(url, timeout=15)
    if response.status_code == 204:
        return []  # 해당 연도 데이터 없음(주로 먼 미래)
    response.raise_for_status()
    result = []
    for item in response.json():
        if not item.get('global', False):
            continue
        if 'Public' not in item.get('types', []):
            continue
        date = item.get('date', '')  # "YYYY-MM-DD"
        name = item.get('localName') or item.get('name', '')
        if len(date) == 10:
            result.append({'date': date[5:], 'name': name})
    return result


def build_nager_holidays(nager_code, start_year=START_YEAR):
    holidays_by_year = {}
    for year in range(start_year, END_YEAR + 1):
        try:
            holidays_by_year[str(year)] = fetch_nager_year(nager_code, year)
        except requests.exceptions.RequestException as e:
            print(f'  ⚠️ {year}년 조회 실패, 빈 목록으로 처리: {e}')
            holidays_by_year[str(year)] = []
        time.sleep(0.15)
    return holidays_by_year


# --- Google Calendar 소스 (Nager 미지원 국가 전용) ---

def is_public_holiday(event, calendar_id):
    """구글 캘린더 이벤트가 진짜 '공휴일'인지 판별 (기념일/옵저번스/지역 한정 공휴일 제외)."""
    summary = event.get('summary', '')

    # 특정 주(州)/지역에만 적용되는 공휴일은 구글이 이름에 "(regional holiday)"를 붙인다
    # (말레이시아, 미국 등 여러 나라 캘린더에서 공통으로 쓰는 표기 — 2026-09-11 확인).
    # 앱 스키마엔 지역 구분이 없어 전국 공휴일처럼 보이게 되므로 아예 제외한다.
    if 'regional holiday' in summary.lower():
        return False

    desc = event.get('description', '').strip()

    if calendar_id.startswith('ko.'):
        return desc == '공휴일'

    # 기념일은 구글이 줄바꿈을 포함한 "숨기기 안내" 문구를 넣는다.
    if '\n' in desc:
        return False

    desc_lower = desc.lower()
    ignore_keywords = ['observance', '기념일', 'season', '記念日']
    return desc_lower not in ignore_keywords


def fetch_google_events(calendar_id, year, api_key):
    safe_calendar_id = urllib.parse.quote(calendar_id)
    url = f'https://www.googleapis.com/calendar/v3/calendars/{safe_calendar_id}/events'
    params = {
        'key': api_key,
        'timeMin': f'{year}-01-01T00:00:00Z',
        'timeMax': f'{year}-12-31T23:59:59Z',
        'singleEvents': 'true',
        'orderBy': 'startTime',
        'maxResults': '2500',
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json().get('items', [])


def build_google_holidays(calendar_id, api_key):
    """Nager 미지원 국가용. 지원하지 않는 캘린더 ID면 None 반환."""
    holidays_by_year = {}
    for year in range(START_YEAR, END_YEAR + 1):
        try:
            events = fetch_google_events(calendar_id, year, api_key)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise
        year_holidays = []
        for event in events:
            if not is_public_holiday(event, calendar_id):
                continue
            start_date = event['start'].get('date')
            if not start_date:
                continue
            summary = event.get('summary', '')
            year_holidays.append({'date': start_date[5:], 'name': summary})
        holidays_by_year[str(year)] = year_holidays
        time.sleep(0.1)
    return holidays_by_year


def main():
    overrides = load_overrides()
    excludes = load_excludes()
    ok_countries = []
    failed_countries = []

    for code, nager_code in NAGER_COUNTRIES.items():
        print(f'[Nager] {code.upper()} 조회 중...')
        try:
            # max() — COUNTRY_START_YEAR_OVERRIDES는 "이 나라는 이 연도보다 앞설 수 없다"는
            # 하한선이라, 전역 START_YEAR가 그 값보다 나중이면(예: 2015 > 1992) 전역값을
            # 따라야 한다. 그냥 override 우선이면 전역 START_YEAR를 낮췄을 때 이 나라만
            # 도로 옛날로 튀는 버그가 생김.
            country_start_year = max(START_YEAR, COUNTRY_START_YEAR_OVERRIDES.get(code, START_YEAR))
            holidays_by_year = build_nager_holidays(nager_code, country_start_year)
            restore_empty_years(code, holidays_by_year)
            apply_excludes(holidays_by_year, excludes.get(code, []))
            apply_overrides(holidays_by_year, overrides.get(code, {}))
            path = write_json(code, holidays_by_year)
            ok_countries.append(code)
            print(f'  ✅ 저장: {path}')
        except Exception as e:
            failed_countries.append(code)
            print(f'  ❌ 실패: {e}')

    api_key = load_google_api_key()
    if GOOGLE_ONLY_CALENDARS and api_key is None:
        print()
        print('⚠️ Google API 키를 찾을 수 없어 나머지 7개국은 건너뜁니다.')
        print(f'   GOOGLE_API_KEY 환경변수를 설정하거나 {API_KEY_FILE.name} 파일에 키를 저장하세요.')
        failed_countries.extend(GOOGLE_ONLY_CALENDARS.keys())
    else:
        for code, config in GOOGLE_ONLY_CALENDARS.items():
            print(f'[Google] {code.upper()} 조회 중...')
            try:
                holidays_by_year = build_google_holidays(config['id'], api_key)
                if holidays_by_year is None:
                    print(f'  ⏭️ 건너뜀: 지원하지 않는 캘린더 ID ({config["id"]})')
                    failed_countries.append(code)
                    continue
                restore_empty_years(code, holidays_by_year)
                apply_excludes(holidays_by_year, excludes.get(code, []))
                apply_overrides(holidays_by_year, overrides.get(code, {}))
                path = write_json(code, holidays_by_year)
                ok_countries.append(code)
                print(f'  ✅ 저장: {path}')
            except Exception as e:
                failed_countries.append(code)
                print(f'  ❌ 실패: {e}')

    print()
    print(f'성공 {len(ok_countries)}개국 / 실패 {len(failed_countries)}개국')
    if failed_countries:
        print('실패한 국가:', ', '.join(c.upper() for c in failed_countries))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
