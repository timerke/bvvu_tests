import logging
import time
from typing import Dict, List
from uiobapi import Uiob
import utils as ut
from ssh import SshClient


logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", level=logging.INFO)


class TestFailed(RuntimeError):
    pass


class TestingSystem:

    _MAX_REBOOT_TIME: int = 10 * 60

    def __init__(self, host: str, port: int, username: str, password: str, reboots: int) -> None:
        """
        :param host: IP address of tested device;
        :param port: port for ssh connection;
        :param username: username for connecting to BVVU via ssh;
        :param password: password for connecting to BVVU via ssh;
        :param reboots: number of BVVU reboots.
        """

        self._host: str = host
        self._logs: Dict[str, Dict[str, List[str]]] = {"general": {},
                                                       "urmc": {},
                                                       "xinet": {}}
        self._password: str = password
        self._port: str = port
        self._reboots: int = reboots
        self._username: str = username

    @staticmethod
    def _check_log(log_name: str, list_of_file_names: List[str], list_of_logs: List[str]) -> None:
        if len(list_of_logs) > 1:
            last_log = ut.get_last_log(list_of_logs[-2])
            logging.info("Checking %s log for last record '%s'", log_name, last_log)
            if last_log not in list_of_logs[-1]:
                raise TestFailed(f"Last record '{last_log}' from '{list_of_file_names[-2]}' not found in "
                                 f"'{list_of_file_names[-1]}'")
        logging.info("%s log checked", log_name)

    def _do_test(self, dir_name: str, uiob: Uiob) -> None:
        """
        Method performs downloading logs and rebooting.
        :param dir_name: directory for saving logs;
        :param uiob: object to communicate with BVVU device.
        """

        ssh_client = SshClient(self._host, self._port, self._username, self._password)
        logs_size = ssh_client.get_size_of_logs()
        ut.get_and_save_logs(dir_name, uiob, logs_size, self._logs)
        for log_name, log_and_file_names in self._logs.items():
            try:
                self._check_log(log_name, log_and_file_names["file_names"], log_and_file_names["logs"])
            except Exception as exc:
                logging.error(exc)

        uiob.os.reboot()
        logging.info("Reboot")
        logging.info("Wait for BVVU is up...")
        reboot_at = time.time()
        while not uiob.check_alive() and time.time() < reboot_at + self._MAX_REBOOT_TIME:
            time.sleep(10)
        if not uiob.check_alive():
            raise TestFailed("It seems like BVVU admin panel is dead")

        logging.info("BVVU admin panel is online again")

    def run_test(self) -> None:
        """
        Method starts test with multiple reload and downloads the logs.
        """

        uiob: Uiob = Uiob(self._host)
        dir_name: str = ut.make_dir(self._host)
        test_index = 0
        while test_index < self._reboots:
            logging.info("TEST #%d", test_index)
            self._do_test(dir_name, uiob)
            test_index += 1
        logging.info("Test passed")


def run() -> None:
    args = ut.parse_args()
    testing_system = TestingSystem(args.host, args.port, args.username, args.password, args.reboots)
    testing_system.run_test()


if __name__ == "__main__":
    run()
