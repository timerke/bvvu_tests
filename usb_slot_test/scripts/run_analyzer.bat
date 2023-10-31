Rem Enter:
Rem LOG_FILE - name of file with log.

set LOG_FILE=log_test.txt
cd ..
venv\scripts\python run_analyzer.py %LOG_FILE%
pause