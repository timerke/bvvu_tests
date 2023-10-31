import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from testing_system.configreader import ConfigReader
from testing_system.energenie import EnerGenie
from testing_system.logger import add_file_handler
from testing_system.sshclient import SshClient
from testing_system.uiob import NewUiob


class StopTestException(Exception):
    pass


class TestingSystem:
    """
    Class for testing blades of USB hubs for slots.
    """

    WAITING_TIME: int = 30

    def __init__(self, bvvu_host: str, ssh_port: int, ssh_username: str, ssh_password: str, energenie_host: str,
                 energenie_password: str, energenie_socket: int, reboot_number: int, stop_if_fail: bool) -> None:
        """
        :param bvvu_host: IP address of the tested BVVU;
        :param ssh_port: port for connecting to BVVU via ssh;
        :param ssh_username: user login under which to connect to the BVVU via ssh;
        :param ssh_password: password for connecting to BVU via ssh;
        :param energenie_host: IP address of EnerGenie surge protector;
        :param energenie_password: password to connect to the surge protector through LAN;
        :param energenie_socket: surge protector socket number to be controlled (a number from 1 to 4);
        :param reboot_number: number of required BVVU reboots;
        :param stop_if_fail: True if testing needs to be stopped when a module fails.
        """

        self._device: NewUiob = NewUiob(bvvu_host)
        self._power_manager: EnerGenie = EnerGenie(energenie_host, energenie_password, energenie_socket)
        self._reboot_number: int = reboot_number
        self._ssh_client: SshClient = SshClient(bvvu_host, ssh_port, ssh_username, ssh_password)
        self._stop_if_fail: bool = stop_if_fail

    def _do_test(self, reboot: bool = True) -> None:
        """
        :param reboot: if True, then it is required to turn off and turn on the power of the BVVU.
        """

        uiob_result = self._device.check_slots()
        ssh_result = self._ssh_client.check_slots()
        if self._stop_if_fail and (uiob_result or ssh_result):
            raise StopTestException()

        if reboot:
            self._power_manager.turn_on_or_off_power(False)
            time.sleep(1)
            self._power_manager.turn_on_or_off_power(True)
            self._wait_for_reboot()

    def _wait_for_reboot(self) -> None:
        waiting_start_time = datetime.now()
        while not self._device.check_alive():
            if datetime.now() - waiting_start_time > timedelta(minutes=TestingSystem.WAITING_TIME):
                raise TimeoutError(f"BVVU did not reboot within the maximum wait time {TestingSystem.WAITING_TIME} min."
                                   f" Something went wrong. Tests will be completed")
            time.sleep(10)

    def run_tests(self) -> None:
        try:
            self._power_manager.connect()
        except Exception as exc:
            logging.error("Failed to connect to EnerGenie", exc_info=exc)
            return

        info = "stop when module is lost" if self._stop_if_fail else "testing will not stop if the module is lost"
        logging.info("Testing information: %d reboots, %s", self._reboot_number, info)
        test_index = 1
        while test_index <= self._reboot_number:
            try:
                logging.info("Test #%d", test_index)
                self._do_test(test_index < self._reboot_number)
                test_index += 1
            except StopTestException:
                logging.error("Test stopped")
                break
            except Exception as exc:
                logging.error("An error occurred while running tests", exc_info=exc)
                break
        self._power_manager.close_connection()


def run_tests() -> None:
    parser = argparse.ArgumentParser("Script performs a multiple power off of BVVU and gets slot information")
    parser.add_argument("--config", type=str, default="config.ini", help="Configuration file")
    args = parser.parse_args(sys.argv[1:])
    reader = ConfigReader()
    try:
        data = reader.read(args.config)
    except Exception as exc:
        logging.error("Failed to read configuration file '%s'.\n%s", args.config, exc)
        return

    bvvu_host = str(data["BVVU"]["HOST"])
    ssh_port = data["BVVU"]["SSH_PORT"]
    ssh_username = data["BVVU"]["USERNAME"]
    ssh_password = data["BVVU"]["PASSWORD"]

    energenie_host = str(data["ENERGENIE"]["HOST"])
    energenie_password = data["ENERGENIE"]["PASSWORD"]
    energenie_socket = data["ENERGENIE"]["SOCKET"]

    log_file = data["TEST"]["LOG_FILE"]
    reboots = data["TEST"]["REBOOTS"]
    stop = data["TEST"]["STOP"]

    add_file_handler(log_file)
    testing_system = TestingSystem(bvvu_host, ssh_port, ssh_username, ssh_password, energenie_host, energenie_password,
                                   energenie_socket, reboots, stop)
    testing_system.run_tests()
