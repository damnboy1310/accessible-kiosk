@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title 버거킹 접근성 키오스크

cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
set "SERVE=.venv\Scripts\waitress-serve.exe"
set "PORT=8000"
set "URL=http://127.0.0.1:%PORT%"

echo ==========================================
echo   버거킹 접근성 키오스크
echo ==========================================
echo.

REM ---------- 1) 최신 코드 ----------
where git >nul 2>&1
if not errorlevel 1 (
    echo [1/4] 최신 코드 받는 중...
    git pull --ff-only
) else (
    echo [1/4] git 없음 - 코드 업데이트 건너뜀
)

REM ---------- 2) 가상환경 + 의존성 ----------
if not exist "%PY%" (
    echo [2/4] 가상환경 생성 중...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [오류] Python을 찾을 수 없습니다.
        echo        python.org에서 설치할 때 "Add python.exe to PATH"를 체크하세요.
        pause
        exit /b 1
    )
)
echo [2/4] 의존성 확인 중...
"%PY%" -m pip install --quiet --disable-pip-version-check -r requirements-web.txt
if errorlevel 1 (
    echo [오류] 의존성 설치 실패
    pause
    exit /b 1
)

REM ---------- 3) 환경변수 ----------
if not exist ".env" (
    echo.
    echo [알림] .env 파일이 없습니다. .env.example을 복사합니다.
    echo        메모장이 열리면 ANTHROPIC_API_KEY를 넣고 저장하세요.
    echo        API 키 없이 데모만 돌리려면 KIOSK_LLM_MODE=mock 으로 두면 됩니다.
    echo.
    copy /y .env.example .env >nul
    notepad .env
)

REM ---------- 4) 서버 기동 ----------
echo [3/4] 서버 시작 ^(%URL%^)...
start "kiosk-server" /min "%SERVE%" --host=127.0.0.1 --port=%PORT% web.app:app

set /a TRIES=0
:waitloop
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try{Invoke-WebRequest -Uri '%URL%/' -UseBasicParsing -TimeoutSec 2 ^| Out-Null; exit 0}catch{exit 1}" >nul 2>&1
if not errorlevel 1 goto ready
set /a TRIES+=1
if !TRIES! GEQ 30 (
    echo [오류] 서버가 30초 안에 응답하지 않았습니다.
    pause
    exit /b 1
)
goto waitloop

:ready
echo [4/4] 키오스크 브라우저 실행...

set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" (
    echo [오류] Microsoft Edge를 찾을 수 없습니다.
    pause
    exit /b 1
)

start "" "%EDGE%" --kiosk "%URL%" --edge-kiosk-type=fullscreen --no-first-run ^
    --disable-pinch --overscroll-history-navigation=0 ^
    --noerrdialogs --disable-session-crashed-bubble

echo.
echo 실행 완료.
echo   - 키오스크 종료: Alt + F4
echo   - 이 창을 닫으면 서버도 함께 종료됩니다.
echo.
pause

taskkill /fi "WINDOWTITLE eq kiosk-server*" /f >nul 2>&1
endlocal
