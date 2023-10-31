import logging
from typing import List
from paramiko import AutoAddPolicy, SSHClient


class SshClient:

    COMMAND: str = "ls /dev/ximc"
    SLOT_NUMBER: int = 16

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """
        :param host: host of the remote machine to which to connect via ssh;
        :param port: port of the remote machine;
        :param username: login of user in the remote machine;
        :param password: password of user in  the remote machine.
        """

        self._host: str = host
        self._password: str = password
        self._port: int = port
        self._ssh: SSHClient = SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.set_missing_host_key_policy(AutoAddPolicy())
        self._username: str = username

    def check_slots(self) -> bool:
        """
        :return: True if there are missing modules.
        """

        self._ssh.connect(self._host, self._port, self._username, self._password)
        slots = set(self.exec_command(SshClient.COMMAND))
        required_slots = set([f"{i:0>8}" for i in range(1, SshClient.SLOT_NUMBER + 1)])
        missing_modules = sorted(required_slots.difference(slots))
        missing_module_number = len(missing_modules)
        logging.info("[SSH] Number of missing modules: %d, missing modules: %s", missing_module_number,
                     missing_modules)

        return len(missing_modules) != 0

    def exec_command(self, command: str, sudo: bool = False) -> List[str]:
        """
        :param command: command to be executed over ssh;
        :param sudo:
        :return: lines from the result of the command.
        """

        stdin, stdout, _ = self._ssh.exec_command(command, get_pty=True)
        if sudo:
            stdin.write(self._password + "\n")
            stdin.flush()
        stdout_lines = []
        for line in iter(stdout.readline, ""):
            line = line.strip("\n\r")
            lines = [i for i in line.split(" ") if i]
            for line in lines:
                stdout_lines.extend([i for i in line.split("\t") if i])
        return stdout_lines
