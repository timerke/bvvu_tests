# Enter:
# DIR_NAME - directory name containing logs;
# DEVICE_NAME - the name of device from which logs were collected.

DIR_NAME=
DEVICE_NAME=
cd ..
./venv/bin/python3 testing_system/analyzer.py $DIR_NAME --device_name $DEVICE_NAME