Rem Enter:
Rem DIR_NAME - directory name containing logs;
Rem DEVICE_NAME - the name of device from which logs were collected.

set DIR_NAME=
set DEVICE_NAME=
cd ..
venv\scripts\python testing_system\analyzer.py %DIR_NAME% --device_name %DEVICE_NAME%
pause