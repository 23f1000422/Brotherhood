@echo off
cd /d "d:\Brotherhood"
call .venv\Scripts\activate
streamlit run streamlit_app.py
pause
