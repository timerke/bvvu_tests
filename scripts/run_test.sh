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
NUMBER=
cd ..
./venv/bin/python3 testing_system/testings_system.py --host $HOST --port $PORT --username $USERNAME --password $PASSWORD --number $NUMBER