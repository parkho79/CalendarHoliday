import requests
import json
import os
import urllib.parse

# 💡 여기에 발급받은 Google API Key를 입력하세요.
API_KEY = 'AIzaSyAX2iIktJEYN0GBya4B6KGb5EudVyynXPk'

# 지원할 국가 및 캘린더 ID 설정 (국가코드(소문자)를 키로 사용)
CALENDARS = {
    # 아시아 / 태평양
    'kr': {'id': 'ko.south_korea#holiday@group.v.calendar.google.com'},
    'jp': {'id': 'ja.japanese#holiday@group.v.calendar.google.com'},
    'cn': {'id': 'zh.china#holiday@group.v.calendar.google.com'},
    'tw': {'id': 'zh-tw.taiwan#holiday@group.v.calendar.google.com'},
    'hk': {'id': 'zh-hk.hong_kong#holiday@group.v.calendar.google.com'},
    'vn': {'id': 'vi.vietnamese#holiday@group.v.calendar.google.com'},
    'th': {'id': 'th.th#holiday@group.v.calendar.google.com'},
    'id': {'id': 'id.indonesian#holiday@group.v.calendar.google.com'},
    'my': {'id': 'ms.malaysian#holiday@group.v.calendar.google.com'},
    'sg': {'id': 'en.singapore#holiday@group.v.calendar.google.com'},
    'ph': {'id': 'en.philippines#holiday@group.v.calendar.google.com'},
    'in': {'id': 'en.indian#holiday@group.v.calendar.google.com'},
    'au': {'id': 'en.australian#holiday@group.v.calendar.google.com'},
    'nz': {'id': 'en.new_zealand#holiday@group.v.calendar.google.com'},

    # 북미 / 남미
    'us': {'id': 'en.usa#holiday@group.v.calendar.google.com'},
    'ca': {'id': 'en.canadian#holiday@group.v.calendar.google.com'},
    'mx': {'id': 'es.mexican#holiday@group.v.calendar.google.com'},
    'br': {'id': 'pt.brazilian#holiday@group.v.calendar.google.com'},
    'ar': {'id': 'es.argentina#holiday@group.v.calendar.google.com'},
    'cl': {'id': 'es.chilean#holiday@group.v.calendar.google.com'},
    'co': {'id': 'es.colombian#holiday@group.v.calendar.google.com'},
    'pe': {'id': 'es.peruvian#holiday@group.v.calendar.google.com'},

    # 유럽
    'gb': {'id': 'en.uk#holiday@group.v.calendar.google.com'},
    'ie': {'id': 'en.irish#holiday@group.v.calendar.google.com'},
    'fr': {'id': 'fr.french#holiday@group.v.calendar.google.com'},
    'de': {'id': 'de.german#holiday@group.v.calendar.google.com'},
    'at': {'id': 'de.austrian#holiday@group.v.calendar.google.com'},
    'ch': {'id': 'de.swiss#holiday@group.v.calendar.google.com'},
    'it': {'id': 'it.italian#holiday@group.v.calendar.google.com'},
    'es': {'id': 'es.spain#holiday@group.v.calendar.google.com'},
    'pt': {'id': 'pt.portuguese#holiday@group.v.calendar.google.com'},
    'nl': {'id': 'nl.dutch#holiday@group.v.calendar.google.com'},
    'be': {'id': 'nl.belgian#holiday@group.v.calendar.google.com'},
    'se': {'id': 'sv.swedish#holiday@group.v.calendar.google.com'},
    'no': {'id': 'no.norwegian#holiday@group.v.calendar.google.com'},
    'dk': {'id': 'da.danish#holiday@group.v.calendar.google.com'},
    'fi': {'id': 'fi.finnish#holiday@group.v.calendar.google.com'},
    'ru': {'id': 'ru.russian#holiday@group.v.calendar.google.com'},
    'ua': {'id': 'uk.ukrainian#holiday@group.v.calendar.google.com'},
    'pl': {'id': 'pl.polish#holiday@group.v.calendar.google.com'},
    'tr': {'id': 'tr.turkish#holiday@group.v.calendar.google.com'},

    # 중동 / 아프리카
    'il': {'id': 'iw.jewish#holiday@group.v.calendar.google.com'},
    'sa': {'id': 'ar.saudiarabian#holiday@group.v.calendar.google.com'},
    'ae': {'id': 'ar.uae#holiday@group.v.calendar.google.com'},
    'eg': {'id': 'ar.egyptian#holiday@group.v.calendar.google.com'},
    'za': {'id': 'en.sa#holiday@group.v.calendar.google.com'},
}

START_YEAR = 2021
END_YEAR = 2035
OUTPUT_DIR = '/'

def is_public_holiday(event, calendar_id):
    """
    구글 캘린더의 이벤트가 진짜 '공휴일(Public Holiday)'인지 판별합니다.
    글로벌 언어에 대응하여 법정 기념일(Observance)을 필터링합니다.
    """
    desc = event.get('description', '').strip()

    # 1. 한국 캘린더('ko.')의 경우 가장 명확하게 '공휴일' 텍스트만 허용
    if calendar_id.startswith('ko.'):
        return desc == '공휴일'

    # 2. 타국가의 경우: 기념일은 구글이 "Observance\nTo hide observances..." 처럼
    # 항상 줄바꿈(\n)을 포함한 숨기기 안내 문구를 넣습니다.
    # 진짜 공휴일은 보통 "Public holiday", "祝日" 등 1줄로만 표기됩니다.
    if '\n' in desc:
        return False

    # 3. 추가 방어 로직 (1줄짜리 기념일 키워드 방어)
    desc_lower = desc.lower()
    ignore_keywords = ['observance', '기념일', 'season', '記念日']
    for kw in ignore_keywords:
        if kw == desc_lower:
            return False

    return True

def fetch_holidays(calendar_id, year):
    safe_calendar_id = urllib.parse.quote(calendar_id)
    url = f'https://www.googleapis.com/calendar/v3/calendars/{safe_calendar_id}/events'
    params = {
        'key': API_KEY,
        'timeMin': f'{year}-01-01T00:00:00Z',
        'timeMax': f'{year}-12-31T23:59:59Z',
        'singleEvents': 'true',
        'orderBy': 'startTime',
        'maxResults': '2500'  # 💡 데이터 누락 방지를 위해 최대치 설정
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get('items', [])

def generate_json(country_code, config):
    print(f"Fetching data for Country: {country_code.upper()}...")

    holidays_by_year = {}
    for year in range(START_YEAR, END_YEAR + 1):
        try:
            events = fetch_holidays(config['id'], year)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  👉 [건너뜀] 지원하지 않는 캘린더 ID입니다: {config['id']}")
                return # 에러난 국가는 파일 생성 없이 종료하고 다음 국가로 넘어감
            raise # 404 이외의 에러(401 인증 에러 등)는 그대로 발생시킴

        year_holidays = []

        for event in events:
            # 💡 [핵심] 진짜 공휴일이 아니면 스킵합니다.
            if not is_public_holiday(event, config['id']):
                continue

            start_date = event['start'].get('date')
            if not start_date: continue

            summary = event.get('summary', '').replace('"', '\\"')
            year_holidays.append({"date": start_date[5:], "name": summary})

        holidays_by_year[str(year)] = year_holidays

    lines = []
    lines.append('{')
    lines.append('  "meta": {')
    lines.append(f'    "country": "{country_code.upper()}",')
    lines.append('    "version": 1')
    lines.append('  },')
    lines.append('  "holidays": {')

    years = list(holidays_by_year.keys())
    for i, year in enumerate(years):
        lines.append(f'    "{year}": [')
        days = holidays_by_year[year]
        for j, day in enumerate(days):
            comma = "," if j < len(days) - 1 else ""
            lines.append(f'      {{ "date": "{day["date"]}", "name": "{day["name"]}" }}{comma}')

        year_comma = "," if i < len(years) - 1 else ""
        lines.append(f'    ]{year_comma}')

    lines.append('  }')
    lines.append('}')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # 파일명을 국가코드 기반으로 생성 (예: holiday_list_kr.json)
    file_path = os.path.join(OUTPUT_DIR, f'holiday_list_{country_code}.json')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Saved: {file_path}")

def main():
    if API_KEY == 'YOUR_GOOGLE_API_KEY':
        print("⚠️ API_KEY를 먼저 입력해주세요.")
        return

    for country_code, config in CALENDARS.items():
        generate_json(country_code, config)

if __name__ == '__main__':
    main()