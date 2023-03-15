# Enter:
# HOST - IP address of the device under test;
# PORT - port for ssh connection;
# USERNAME - username for connecting to BVVU via ssh;
# PASSWORD - password for connecting to BVVU via ssh;
# NUMBER - number of BVVU reboots.

HOST=
PORT=
USERNAME=
PASSWORD=
REBOOTS=
cd ..
./venv/bin/python3 testing_system/testing_system.py --host $HOST --port $PORT --username $USERNAME --password $PASSWORD --reboots $REBOOTS