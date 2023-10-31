import logging
from uiobapi import Uiob


class NewUiob(Uiob):
    """
    Class for working with BVVU.
    """

    def __init__(self, ip_address: str = None) -> None:
        """
        :param ip_address: IP address of the tested BVVU.
        """

        self._ip_address: str = ip_address
        super().__init__(self._ip_address)
        logging.info("IP address of the BVVU: %s", self._ip_address)

    def check_slots(self) -> bool:
        """
        :return: True if there are missing modules.
        """

        missing_modules = []
        slot_info = self.slot.get_slots_info()
        for slot_index, info in enumerate(slot_info, start=1):
            if info is None:
                missing_modules.append(slot_index)
        missing_module_number = len(missing_modules)
        logging.info("[UIOB] Number of missing modules: %d, missing modules: %s", missing_module_number,
                     missing_modules)
        return missing_module_number != 0
