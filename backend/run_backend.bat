:: Create an isolated Python environment
python -m venv .venv

:: Windows PowerShell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

:: Run the backend tests
.\.venv\Scripts\python.exe -m pytest tests/ -v

:: Start the API
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000