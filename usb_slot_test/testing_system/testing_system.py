import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from energenie import EnerGenie
from uiob import NewUiob


class TestingSystem:
    """
    Class for testing blades of USB hubs for slots.
    """

    WAITING_TIME: int = 30

    def __init__(self, bvvu_ip: str, energenie_ip: str, energenie_password: str, energenie_socket_number: int,
                 log_file_name: str, reboot_number: int
                 ) -> None:
        """
        :param bvvu_ip: IP address of the tested BVVU;
        :param energenie_ip: IP address of EnerGenie surge protector;
        :param energenie_password: password to connect to the surge protector through LAN;
        :param energenie_socket_number: surge protector socket number to be controlled (a number from 1 to 4);
        :param log_file_name: file name for logging;
        :param reboot_number: number of required BVVU reboots.
        """

        self._bvvu_ip: str = bvvu_ip
        self._energenie_ip: str = energenie_ip
        self._energenie_password: str = energenie_password
        self._energenie_socket_number: int = energenie_socket_number
        self._log_file_name: str = log_file_name
        self._reboot_number: int = reboot_number
        self._device: NewUiob = NewUiob(bvvu_ip)
        self._power_manager: EnerGenie = EnerGenie(energenie_ip, energenie_password, energenie_socket_number)
        self._init_logger()

    def _do_test(self, reboot: bool = True) -> None:
        """
        :param reboot: if True, then it is required to turn off and turn on the power of the BVVU.
        """

        self._device.check_slots()
        if reboot:
            self._power_manager.turn_on_or_off_power(False)
            time.sleep(1)
            self._power_manager.turn_on_or_off_power(True)
            self._wait_for_reboot()

    def _init_logger(self) -> None:
        logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", level=logging.INFO,
                            datefmt="%Y-%m-%d %H:%M:%S")
        file_handler = logging.FileHandler(self._log_file_name)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt="[%(asctime)s %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    def _wait_for_reboot(self) -> None:
        waiting_start_time = datetime.now()
        while not self._device.check_alive():
            if datetime.now() - waiting_start_time > timedelta(minutes=TestingSystem.WAITING_TIME):
                raise TimeoutError(f"BVVU did not reboot within the maximum wait time {TestingSystem.WAITING_TIME} min."
                                   f" Something went wrong. Tests will be completed")
            time.sleep(10)

    @classmethod
    def parse_input_arguments(cls) -> "TestingSystem":
        parser = argparse.ArgumentParser("Script performs a multiple power off of BVVU and gets slot information")
        parser.add_argument("--bvvu_host", type=str, default="172.16.128.212", help="IP address of tested BVVU")
        parser.add_argument("--energenie_host", type=str, default="172.16.143.140", help="IP address of EnerGenie page")
        parser.add_argument("--log_file", type=str, default="log_test.txt", help="File name to save logs")
        parser.add_argument("--password", type=str, default="1", help="Password for connecting to EnerGenie page")
        parser.add_argument("--reboots", type=int, default=200, help="Number of BVVU reboots")
        parser.add_argument("--socket", type=int, default=1, help="Number of the EnerGenie socket to which the BVVU is"
                                                                  " connected")
        args = parser.parse_args(sys.argv[1:])
        return TestingSystem(bvvu_ip=args.bvvu_host, energenie_ip=args.energenie_host, energenie_password=args.password,
                             energenie_socket_number=args.socket, log_file_name=args.log_file,
                             reboot_number=args.reboots)

    def run_tests(self) -> None:
        self._power_manager.connect()
        test_index = 1
        while test_index <= self._reboot_number:
            try:
                logging.info("Test #%d", test_index)
                self._do_test(test_index < self._reboot_number)
                test_index += 1
            except Exception as exc:
                logging.error("An error occurred while running tests (%s)", exc)
                break
        self._power_manager.close_connection()


if __name__ == "__main__":
    testing_system = TestingSystem.parse_input_arguments()
    testing_system.run_tests()
