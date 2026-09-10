#!/bin/bash
cd "$(dirname "$0")"

echo "=================================================="
echo " 공휴일 데이터 생성 스크립트 (update_holidays.py)"
echo "=================================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ python3를 찾을 수 없습니다. https://www.python.org 에서 설치 후 다시 실행하세요."
    RESULT=1
else
    if ! python3 -c "import requests" >/dev/null 2>&1; then
        echo "❌ 'requests' 패키지가 없습니다. 아래 명령으로 설치 후 다시 실행하세요:"
        echo "   pip3 install requests"
        RESULT=1
    else
        python3 update_holidays.py
        RESULT=$?
    fi
fi

echo
echo "=================================================="
if [ "$RESULT" -eq 0 ]; then
    echo " 결과: OK"
else
    echo " 결과: NOK (위 로그를 확인하세요)"
fi
echo "=================================================="
echo
echo "다음 단계: git add -A && git commit && git push 로 반영하세요."
echo "아무 키나 누르면 창이 닫힙니다..."
read -n 1 -s -r

if [ "$TERM_PROGRAM" = "Apple_Terminal" ]; then
    osascript -e 'tell application "Terminal" to close (first window whose tty is "'"$(tty)"'")' >/dev/null 2>&1 &
fi
exit "$RESULT"
