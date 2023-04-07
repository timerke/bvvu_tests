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

    def check_slots(self) -> None:
        disabled_modules = []
        slot_info = self.slot.get_slots_info()
        for slot_index, info in enumerate(slot_info, start=1):
            if info is None:
                disabled_modules.append(slot_index)
        logging.info("Number of disabled modules: %d, disabled modules: %s", len(disabled_modules), disabled_modules)
