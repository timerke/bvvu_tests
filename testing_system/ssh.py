import logging
import re
import socket
import time
from typing import Dict
import paramiko


class SshClient:

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """
        :param host: IP address of device;
        :param port: port for ssh connection;
        :param username: username for connecting to BVVU via ssh;
        :param password: password for connecting to BVVU via ssh.
        """

        self._host: str = host
        self._port: int = port
        self._username: str = username
        self._password: str = password

        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(hostname=self._host, port=self._port, username=self._username, password=self._password,
                             look_for_keys=False, allow_agent=False)
        self._init()

    def _init(self) -> None:
        max_bytes = 60000
        short_pause = 1
        with self._client.invoke_shell() as ssh:
            ssh.send("enable\n")
            time.sleep(short_pause)
            ssh.send("terminal length 0\n")
            time.sleep(short_pause)
            ssh.recv(max_bytes)

    def get_size_of_logs(self) -> str:
        command = "journalctl --disk-usage"
        try:
            output = self.run_commands(command)[command].replace("\r", "")
            lines = output.split("\n")
            result = re.search(r"^.* (\d+\.?\d*[a-zA-Z]) .*$", lines[-2])
            if result:
                return result.group(1)
            logging.warning("Failed to parse journal size in BVVU")
        except Exception as exc:
            logging.error("Failed to get journal size from BVVU (%s)", exc)
        return ""

    def run_commands(self, *commands) -> Dict[str, str]:
        max_bytes = 60000
        with self._client.invoke_shell() as ssh:
            result = {}
            for command in commands:
                ssh.send(f"{command}\n")
                ssh.settimeout(5)

                output = ""
                while True:
                    try:
                        part = ssh.recv(max_bytes).decode("utf-8")
                        output += part
                        time.sleep(0.5)
                    except socket.timeout:
                        break
                result[command] = output

            return result
