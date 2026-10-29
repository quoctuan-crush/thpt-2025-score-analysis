@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "VENV_PY=%CD%\.venv-portable\Scripts\python.exe"

if exist "%VENV_PY%" goto check_venv
if exist ".venv-portable" goto invalid_venv

echo Creating a Python environment for this computer...
where py >nul 2>&1
if errorlevel 1 goto try_python
py -3.13 -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_py313
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_py312
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_py_fallback

:try_python
where python >nul 2>&1
if errorlevel 1 goto no_python
echo Python 3.12 or 3.13 was not found via the launcher; using python from PATH.
echo For best compatibility, install Python 3.12 or 3.13 if dependencies fail.
python -m venv ".venv-portable"
goto venv_created

:create_py313
echo Using Python 3.13.
py -3.13 -m venv ".venv-portable"
goto venv_created

:create_py312
echo Using Python 3.12.
py -3.12 -m venv ".venv-portable"
goto venv_created

:create_py_fallback
echo Python 3.12 or 3.13 was not found; using the default Python 3 version.
echo For best compatibility, install Python 3.12 or 3.13 if dependencies fail.
py -3 -m venv ".venv-portable"

:venv_created
if errorlevel 1 goto venv_error

:check_venv
"%VENV_PY%" -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if errorlevel 1 goto invalid_venv
"%VENV_PY%" -c "import tkinter" >nul 2>&1
if errorlevel 1 goto no_tk

echo Checking project dependencies...
"%VENV_PY%" -m pip install --disable-pip-version-check -r "%CD%\requirements.txt"
if errorlevel 1 goto install_error

echo Checking local data...
"%VENV_PY%" -m database.ensure_data
if errorlevel 1 goto data_error

echo Starting application...
"%VENV_PY%" "%CD%\main.py"
if errorlevel 1 goto app_error
exit /b 0

:no_python
echo Python 3 was not found. Install Python 3.10 or newer, then try again.
goto failed
:venv_error
echo Could not create the Python environment. Check the Python installation.
goto failed
:invalid_venv
echo The .venv-portable environment is missing or cannot run on this computer.
echo Rename or remove only .venv-portable, then run this file again.
goto failed
:no_tk
echo Tkinter is unavailable. Reinstall Python with the Tcl/Tk component enabled.
goto failed
:install_error
echo Dependency installation failed. Check your internet connection and Python installation.
goto failed
:data_error
echo Data preparation failed. See the details above.
goto failed
:app_error
echo The application stopped with an error. See the details above.
:failed
pause
exit /b 1
