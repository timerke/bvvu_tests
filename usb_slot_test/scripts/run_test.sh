# Enter:
# BVVU_HOST - IP address of the device under test;
# ENERGENIE_HOST - IP address of EnerGenie LAN Power Manager;
# LOG_FILE - file name for logs;
# PASSWORD - password for connecting to EnerGenie LAN Power Manager;
# REBOOTS - number of BVVU reboots.

HOST=
ENERGENIE_HOST=
LOG_FILE=
PASSWORD=
REBOOTS=
cd ..
./venv/bin/python3 testing_system/testing_system.py --bvvu_host $BVVU_HOST --energenie_host $ENERGENIE_HOST --log_file $LOG_FILE --password $PASSWORD --reboots $REBOOTS