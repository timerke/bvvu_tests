Rem Enter:
Rem BVVU_HOST - IP address of the device under test;
Rem ENERGENIE_HOST - IP address of EnerGenie LAN Power Manager;
Rem LOG_FILE - file name for logs;
Rem PASSWORD - password for connecting to EnerGenie LAN Power Manager;
Rem REBOOTS - number of BVVU reboots.

set BVVU_HOST=
set ENERGENIE_HOST=
set LOG_FILE=
set PASSWORD=
set REBOOTS=
cd ..
venv\scripts\python testing_system\testing_system.py --bvvu_host %BVVU_HOST% --energenie_host %ENERGENIE_HOST% --log_file %LOG_FILE% --password %PASSWORD% --reboots %REBOOTS%
pause