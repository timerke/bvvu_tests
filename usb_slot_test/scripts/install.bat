cd ..
set PYTHON=C:\Python\Python37\python.exe
if exist venv rd /s/q venv
%PYTHON% -m venv venv
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip cache remove *
venv\Scripts\python -m pip install -r requirements.txt
pause