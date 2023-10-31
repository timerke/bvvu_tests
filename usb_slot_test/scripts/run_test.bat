Rem Enter:
Rem CONFIG - configuration file for tests.

set CONFIG=config.ini
cd ..
venv\scripts\python run.py --config %CONFIG%
pause