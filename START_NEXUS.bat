@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto done
python -m streamlit run streamlit_app.py
:done
pause
