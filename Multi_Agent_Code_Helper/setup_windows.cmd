@echo off
setlocal
python --version >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Dependencies installed. Edit .env and add your NVIDIA and Pinecone keys.
echo Ensure CODEBASE_PATH points to the cloned Naive_RAG repository.
echo Then run: .\.venv\Scripts\python.exe -m code_helper.index_codebase
echo Then run: .\.venv\Scripts\adk.exe run code_helper
pause
