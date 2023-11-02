import logging
import time
from enum import auto, Enum
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Page(Enum):
    CONTROL = auto
    LOGIN = auto()
    UNKNOWN = auto()


class EnerGenie:
    """
    Class for remote power management of the EnerGenie surge protector.
    """

    ON_OFF_BUTTON: str = "onoffbtn"
    PASSWORD_NAME: str = "pw"
    SOCKET_ID: str = "stCont{}"
    TIMEOUT: float = 10

    def __init__(self, ip_address: str, password: str, socket_number: int) -> None:
        """
        :param ip_address: IP address of EnerGenie surge protector;
        :param password: password to connect to the surge protector through LAN;
        :param socket_number: surge protector socket number to be controlled (a number from 1 to 4).
        """

        self._driver: webdriver.Chrome = None
        self._ip_address: str = ip_address
        self._password: str = password
        if not isinstance(socket_number, int) or socket_number < 1 or socket_number > 4:
            raise ValueError("The socket number must be an integer between 1 and 4 inclusive")
        self._socket: int = socket_number
        self._socket_number: str = EnerGenie.SOCKET_ID.format(socket_number - 1)

    @property
    def url(self) -> str:
        """
        :return: EnerGenie page address.
        """

        return f"http://{self._ip_address}"

    def _check_logged_in(self) -> None:
        start_time = time.monotonic()
        while time.monotonic() - start_time < EnerGenie.TIMEOUT:
            try:
                self._driver.find_element(By.ID, self._socket_number)
                break
            except NoSuchElementException:
                pass
        else:
            raise RuntimeError("Failed to login")

    def _check_page(self) -> Page:
        """
        :return: network filter page that opens when connected.
        """

        pages = {Page.LOGIN: (By.NAME, EnerGenie.PASSWORD_NAME),
                 Page.CONTROL: (By.ID, self._socket_number)}
        for page, (selector_type, value) in pages.items():
            try:
                self._driver.find_element(selector_type, value)
            except NoSuchElementException:
                pass
            else:
                return page
        return Page.UNKNOWN

    def _enter_password(self) -> None:
        password_element = self._driver.find_element(By.NAME, "pw")
        password_element.send_keys(self._password)
        password_element.send_keys(Keys.RETURN)

    def close_connection(self) -> None:
        self._driver.close()
        logging.info("Page closed")

    def connect(self) -> None:
        self._driver = webdriver.Chrome()
        self._driver.get(self.url)
        current_page = self._check_page()
        if current_page == Page.LOGIN:
            self._enter_password()
            self._check_logged_in()
        elif current_page == Page.UNKNOWN:
            raise ConnectionError("Failed to load power management page")
        logging.info("EnerGenie power management page loaded %s, socket = %d", self.url, self._socket)

    def turn_on_or_off_power(self, turn_on: bool) -> None:
        """
        :param turn_on: if True, the power will be turned on.
        """

        socket_element = self._driver.find_element(By.ID, self._socket_number)
        on_off_button = socket_element.find_element(By.CLASS_NAME, EnerGenie.ON_OFF_BUTTON)
        button_function = on_off_button.text.lower()
        if (button_function == "on" and turn_on) or (button_function == "off" and not turn_on):
            on_off_button.click()
            logging.info("Power turned %s", button_function)
