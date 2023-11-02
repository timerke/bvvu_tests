import logging
import re
from typing import Optional, Set
from paramiko import AutoAddPolicy, SSHClient


class SshClient:

    FILE_BEFORE_USBRESET: str = "/home/before_usbreset.txt"
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

    @staticmethod
    def _check_missing(modules: Set[str], required_modules: Set[str], label: str) -> bool:
        """
        :param modules: set of modules found on the system in the /dev directory;
        :param required_modules:
        :param label:
        :return: True if there are missing modules.
        """

        missing_modules = sorted(required_modules.difference(modules))
        missing_module_number = len(missing_modules)
        logging.info("[%s] Number of missing modules: %d, missing modules: %s", label, missing_module_number,
                     missing_modules)
        return len(missing_modules) != 0

    @staticmethod
    def _get_modules_from_command_output(command_output: str) -> Set[str]:
        """
        :param command_output: string command output.
        :return: the set of modules found in the command output.
        """

        modules = set()
        for line in command_output.split("\n"):
            line = line.strip("\n\r")
            words = [i for i in line.split(" ") if i]
            for word in words:
                modules.update([i for i in word.split("\t") if i])
        return modules

    def _get_modules_from_file(self, text: str) -> Optional[Set[str]]:
        """
        :param text: file content.
        :return: the set of modules found in the file content.
        """

        lines = text.split("\n")
        reboot_number = self._get_reboot_number(lines[0]) if len(lines) > 0 else None
        if isinstance(reboot_number, int):
            logging.info("Reboot number from '%s' file = %d", SshClient.FILE_BEFORE_USBRESET, reboot_number)
        else:
            logging.warning("Failed to get reboot number from '%s' file", SshClient.FILE_BEFORE_USBRESET)

        if len(lines) > 2 and "modules" in lines[1]:
            return self._get_modules_from_command_output("\n".join(lines[2:]))
        logging.warning("'%s' file is not written correctly", SshClient.FILE_BEFORE_USBRESET)
        return None

    @staticmethod
    def _get_reboot_number(line: str) -> Optional[int]:
        """
        :param line: string from which to get the reboot number.
        :return: reboot number.
        """

        result = re.match(r"^reboot_number=(?P<reboot_number>\d+).*$", line)
        if result:
            try:
                return int(result["reboot_number"])
            except ValueError:
                pass
        return None

    def check_modules(self) -> bool:
        """
        :return: True if there are missing modules in /dev or /dev/ximc.
        """

        command_output = self.exec_command(f"cat {SshClient.FILE_BEFORE_USBRESET}")
        modules = self._get_modules_from_file(command_output)
        if modules is not None:
            required_modules = {f"{i:0>8}" for i in range(1, SshClient.SLOT_NUMBER + 1)}
            self._check_missing(modules, required_modules, "SSH_BEFORE")

        command_output = self.exec_command("ls /dev | grep ttyACM")
        modules = self._get_modules_from_command_output(command_output)
        required_modules = {f"ttyACM{i}" for i in range(SshClient.SLOT_NUMBER)}
        result_dev = self._check_missing(modules, required_modules, "SSH_DEV")

        command_output = self.exec_command("ls /dev/ximc")
        modules = self._get_modules_from_command_output(command_output)
        required_modules = {f"{i:0>8}" for i in range(1, SshClient.SLOT_NUMBER + 1)}
        result_dev_ximc = self._check_missing(modules, required_modules, "SSH_DEV_XIMC")
        return result_dev or result_dev_ximc

    def connect(self) -> None:
        self._ssh.connect(self._host, self._port, self._username, self._password)

    def exec_command(self, command: str, sudo: bool = False) -> str:
        """
        :param command: command to be executed over ssh;
        :param sudo:
        :return: string command output.
        """

        stdin, stdout, _ = self._ssh.exec_command(command, get_pty=True)
        if sudo:
            stdin.write(self._password + "\n")
            stdin.flush()
        return "".join(iter(stdout.readline, ""))
