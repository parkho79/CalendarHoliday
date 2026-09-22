# CalendarHoliday

MyCalendar 앱(안드로이드 캘린더 앱)이 표시하는 공휴일 데이터의 **단일 소스**입니다. 여기서
생성한 JSON을 커밋·푸시하면 그게 곧 배포입니다 — `main` 브랜치의 `holiday_list_{code}.json`이
`raw.githubusercontent.com`을 통해 MyCalendar 앱에 그대로 서빙됩니다.

## 저장소 역할

- **여기(CalendarHoliday)** — 생성. `update_holidays.py`로 만들고 push하는 곳은 여기뿐입니다.
- **MyCalendar** (`github.com/parkho79/MyCalendar`) — 소비자. 이 저장소가 생성한 데이터를
  두 경로로 받습니다.
  1. **빌드 시점 번들**: MyCalendar 저장소의 `sync_holidays_from_calendarholiday.py`가 여기
     결과물을 복사해서 `app/src/main/assets/holidays/`에 커밋 — APK에 포함되어 오프라인
     최초 실행에도 즉시 표시됨(46개국 합쳐도 gzip 기준 약 24KB).
  2. **런타임 갱신**: 앱의 `HolidayListInstaller`가 `raw.githubusercontent.com/parkho79/
     CalendarHoliday/main/holiday_list_{code}.json`을 ETag 조건부 GET으로 주기적으로 확인해서,
     앱 업데이트 없이도 이미 설치된 사용자에게 최신 데이터를 반영합니다.

과거엔 MyCalendar 저장소에도 별도 생성 스크립트가 있어서 두 저장소 내용이 손으로 맞춰야 하는
상태였고, 실제로 어긋난 적이 있었습니다(2026-09-10, 한국 데이터 8개 항목 차이). 지금은 생성이
여기 한 곳뿐이라 그런 어긋남이 구조적으로 불가능합니다.

## 데이터 생성 방법

`generate_holidays.command`(Mac) 또는 `generate_holidays.bat`(Windows)를 더블클릭하면
python3/`requests` 설치를 확인한 뒤 `update_holidays.py`를 실행하고, 끝나면 **OK/NOK**를
표시하고 아무 키나 누르면 창이 닫힙니다(46개국 전체).

터미널에서 직접 `python3 update_holidays.py`를 실행할 때는 국가 코드를 인자로 줘서 그
나라들만 처리할 수 있습니다(예: `python3 update_holidays.py kr pe`) — 정정 하나 검증하려고
매번 46개국 API를 전부 호출할 필요 없게. 인자 없이 실행하면 기존대로 전체를 처리합니다.

내부적으로:

- **Nager.Date**(date.nager.at, 무료·키 불필요) 지원국 중 38개국은 이걸 우선 사용합니다.
  `global == true && "Public" in types`만 채택해서, 문화적 기념일(밸런타인데이, 부활절 등)이
  섞여 들어오는 걸 막습니다. 단, Nager가 실제로는 전국 공휴일인데 `global: false`로 잘못
  분류해둔 경우가 있음을 2026-09-12에 38개국 전수 확인으로 발견함(영국 New Year's Day, 호주
  Anzac Day) — 이런 것과 Nager 원본에 아예 없는 항목(중국 청명절)은 `holiday_corrections.json`
  으로 보정한다.
- Nager 미지원 또는 데이터 결측 8개국(`tw`, `th`, `my`, `in`, `il`, `sa`, `ae`, `vn`)은
  Google Calendar 공휴일 캘린더 API로 생성합니다. `.google_api_key` 파일(이 저장소 루트,
  git 추적 제외)이나 `GOOGLE_API_KEY` 환경변수에 키가 있어야 합니다. 키가 없으면 이 8개국만
  건너뜁니다. (`vn`은 Nager 자체 지원국이지만 음력 공휴일(뗏, 훙브엉기념일)이 통째로 빠져
  있어 2026-09-11에 여기로 옮김 — 다른 음력 국가(중국/홍콩)는 Nager에 정상 반영되어 있어
  베트남만의 결측으로 확인됨.)
- 두 소스 모두 놓치는 예외(그해에만 지정된 임시공휴일, 특정 대체공휴일 등), 원본이 실제로는
  공휴일이 아닌데 진짜 공휴일과 모든 필드가 동일하게 태깅되어 있어 자동으로 못 거르는 항목,
  특정 연도부터만 제정된 공휴일을 소스가 모든 연도에 동일하게 보여주는 경우, 소스가 특정
  연도 하나만 날짜를 잘못 계산한 경우는 전부 `holiday_corrections.json`에 국가별
  add/remove 규칙으로 등록하면 생성 결과에 자동 반영됩니다(스키마는 파일 안 `_readme` 참고).
  관련된 정정(예: 틀린 날짜 제거 + 올바른 날짜 추가)은 같은 나라 목록에 나란히 등록해서
  하나의 수정으로 같이 관리합니다.
- 특정 주(州)/지역에만 적용되는 공휴일(구글이 이름에 `"(regional holiday)"`라고 표시)은
  `is_public_holiday()`가 자동으로 제외합니다.

생성 후에는:

```
git add -A && git commit -m "..." && git push
```

push하는 순간 **이미 설치된 사용자들에게도** 다음 `updateCheckAll()` 호출 시 반영됩니다.
MyCalendar 앱에 새로 번들할 스냅샷까지 갱신하려면(신규 설치 사용자의 오프라인 최초 경험),
MyCalendar 저장소에서 `python3 sync_holidays_from_calendarholiday.py`를 추가로 실행합니다.

**참고**: 이 동기화를 깜빡해도 조용히 넘어가지 않습니다 — MyCalendar의 릴리스 빌드
(`assembleRelease`/`bundleRelease`)는 `checkHolidayDataFreshness` Gradle 태스크가 이 저장소의
최신 커밋과 MyCalendar에 커밋된 마지막 동기화 커밋을 비교해서, 뒤처져 있으면 빌드 자체를
실패시킵니다. 그러니 여기 push한 뒤 MyCalendar 쪽 동기화를 안 하고 릴리스를 시도하면 그
시점에 바로 알게 됩니다.

## 알아둘 것

- Nager.Date는 대체공휴일이 있으면 **실제로 쉬는 날(효력 발생 날짜) 하나만** 표시합니다.
  원래 고정 날짜는 별도로 표시하지 않습니다. 예전 Google 데이터 방식(원래 날짜 + 대체 날짜를
  각각 표시)과 다르니, "날짜가 이상하다"고 오판하지 말고 실제 요일부터 확인하세요(주말과
  겹치는지).
- `meta.version` 필드는 스키마에만 있고 실제로 비교에 쓰이진 않습니다 — 갱신 여부 판단은
  HTTP ETag(`If-None-Match`)가 전담합니다.
- API 키는 **절대 커밋하지 마세요**. `.gitignore`에 `.google_api_key`가 이미 등록되어
  있습니다.
