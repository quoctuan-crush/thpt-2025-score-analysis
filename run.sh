#!/bin/sh
set -eu
cd -- "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PYTHONUTF8=1
venv_python="$PWD/.venv-portable/bin/python"

if [ ! -x "$venv_python" ]; then
    if [ -e .venv-portable ]; then
        echo 'The .venv-portable environment cannot run on this computer.' >&2
        echo 'Rename or remove only .venv-portable, then run this script again.' >&2
        exit 1
    fi
    if command -v python3.13 >/dev/null 2>&1; then
        python_cmd=python3.13
    elif command -v python3.12 >/dev/null 2>&1; then
        python_cmd=python3.12
    elif command -v python3 >/dev/null 2>&1; then
        python_cmd=python3
        echo 'Python 3.12 or 3.13 was not found; using the default Python 3.'
        echo 'For best compatibility, install Python 3.12 or 3.13 if dependencies fail.'
    else
        echo 'Python 3 was not found. Install Python 3.12 or 3.13 and try again.' >&2
        exit 1
    fi
    echo 'Creating a Python environment for this computer...'
    if ! "$python_cmd" -m venv .venv-portable; then
        echo 'Could not create the environment. Install the Python venv package and try again.' >&2
        exit 1
    fi
fi

if ! "$venv_python" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    echo 'The .venv-portable environment is invalid or uses Python older than 3.10.' >&2
    echo 'Rename or remove only .venv-portable, then run this script again.' >&2
    exit 1
fi
if ! "$venv_python" -c 'import tkinter' >/dev/null 2>&1; then
    echo 'Tkinter is unavailable. Install the Tkinter package for your Python installation.' >&2
    exit 1
fi
echo 'Checking project dependencies...'
if ! "$venv_python" -m pip install --disable-pip-version-check -r "$PWD/requirements.txt"; then
    echo 'Dependency installation failed. Check your internet connection and Python installation.' >&2
    exit 1
fi
echo 'Checking local data...'
if ! "$venv_python" -m database.ensure_data; then
    echo 'Data preparation failed. See the details above.' >&2
    exit 1
fi
echo 'Starting application...'
exec "$venv_python" "$PWD/main.py"
