Rem Enter:
Rem HOST - IP address of the device under test;
Rem PORT - port for ssh connection;
Rem USERNAME - username for connecting to BVVU via ssh;
Rem PASSWORD - password for connecting to BVVU via ssh;
Rem NUMBER - number of BVVU reboots.

set HOST=
set PORT=
set USERNAME=
set PASSWORD=
set REBOOTS=
cd ..
venv\scripts\python testing_system\testing_system.py --host %HOST% --port %PORT% --username %USERNAME% --password %PASSWORD% --reboots %REBOOTS%
pause