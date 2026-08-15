@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo DiTuS Kablo Analizor - Sanal Ortam Kurulumu
echo ============================================================

if exist ".venv\Scripts\python.exe" goto INSTALL

echo [1/4] Uygun Python surumu araniyor...
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        echo Python 3.12 bulundu.
        py -3.12 -m venv .venv
        goto CHECK_VENV
    )
    py -3.11 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        echo Python 3.11 bulundu.
        py -3.11 -m venv .venv
        goto CHECK_VENV
    )
)

where python >nul 2>nul
if errorlevel 1 goto NO_PYTHON
python -c "import sys; assert sys.version_info[:2] in [(3,11),(3,12)], 'Python 3.11 veya 3.12 gerekli'" >nul 2>nul
if errorlevel 1 goto BAD_PYTHON
python -m venv .venv

goto CHECK_VENV

:CHECK_VENV
if not exist ".venv\Scripts\python.exe" goto VENV_FAILED

:INSTALL
echo [2/4] pip, setuptools ve wheel guncelleniyor...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto INSTALL_FAILED

echo [3/4] Uygulama paketleri kuruluyor...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto INSTALL_FAILED

echo [4/4] Yerel DiTuS paketi editable modda kaydediliyor...
".venv\Scripts\python.exe" -m pip install --no-deps -e .
if errorlevel 1 goto INSTALL_FAILED

echo.
echo Kurulum tamamlandi.
echo Uygulamayi run_windows.bat ile baslatabilirsiniz.
echo.
pause
exit /b 0

:NO_PYTHON
echo HATA: Python bulunamadi.
echo 64-bit Python 3.12 kurun ve "Add Python to PATH" secenegini etkinlestirin.
pause
exit /b 1

:BAD_PYTHON
echo HATA: Python 3.11 veya 3.12 gerekli.
echo Onerilen surum: 64-bit Python 3.12.
pause
exit /b 1

:VENV_FAILED
echo HATA: .venv olusturulamadi.
pause
exit /b 1

:INSTALL_FAILED
echo HATA: Paket kurulumu basarisiz oldu.
echo Internet baglantisini ve proxy/kurum agi ayarlarini kontrol edin.
pause
exit /b 1
