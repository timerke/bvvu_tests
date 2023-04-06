import logging
from enum import auto, Enum
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys


class Page(Enum):
    CONTROL = auto
    LOGIN = auto()
    UNKNOWN = auto()


class EnerGenie:

    ON_OFF_BUTTON: str = "onoffbtn"
    PASSWORD_NAME: str = "pw"
    SOCKET_ID: str = "stCont0"

    def __init__(self, ip_address: str, password: str) -> None:
        self._driver: webdriver.Chrome = None
        self._ip_address: str = ip_address
        self._password: str = password

    @property
    def url(self) -> str:
        return f"http://{self._ip_address}"

    def _check_page(self) -> Page:
        pages = {EnerGenie.PASSWORD_NAME: Page.LOGIN,
                 EnerGenie.SOCKET_ID: Page.CONTROL}
        for element_id_or_name, page in pages.items():
            for find_by in ("id", "name"):
                try:
                    method = getattr(self._driver, f"find_element_by_{find_by}", None)
                    if method:
                        method(element_id_or_name)
                except NoSuchElementException:
                    pass
                else:
                    return page

    def _enter_password(self) -> None:
        password_element = self._driver.find_element_by_name("pw")
        password_element.send_keys(self._password)
        password_element.send_keys(Keys.RETURN)

    def close_connection(self) -> None:
        self._driver.close()
        logging.info("Page closed")

    def connect(self) -> None:
        self._driver = webdriver.Chrome(ChromeDriverManager().install())
        self._driver.get(self.url)
        current_page = self._check_page()
        if current_page == Page.LOGIN:
            self._enter_password()
        elif current_page == Page.UNKNOWN:
            raise ConnectionError("Failed to load power management page")
        logging.info("Power management page loaded")

    def turn_on_or_off_power(self, turn_on: bool) -> None:
        """
        :param turn_on: if True, the power will be turned on.
        """

        socket_element = self._driver.find_element_by_id(EnerGenie.SOCKET_ID)
        on_off_button = socket_element.find_element_by_class_name(EnerGenie.ON_OFF_BUTTON)
        button_function = on_off_button.text.lower()
        if (button_function == "on" and turn_on) or (button_function == "off" and not turn_on):
            on_off_button.click()
            logging.info("Power turned %s", button_function)
