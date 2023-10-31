import ipaddress
from configparser import ConfigParser
from typing import Any, Dict, List


class MissingOption(Exception):

    def __init__(self, section: str, option: str) -> None:
        self.option: str = option
        self.section: str = section


class ConfigReader:

    STRUCTURE = {"BVVU": {"HOST": {"converter": ipaddress.ip_address}},
                 "TEST": {"LOG_FILE": {"converter": str,
                                       "default": "log_file.txt"},
                          "REBOOTS": {"converter": int,
                                      "default": 200},
                          "STOP": {"converter": bool,
                                   "default": False}},
                 "ENERGENIE": {"HOST": {"converter": ipaddress.ip_address},
                               "PASSWORD": {"converter": str},
                               "SOCKET": {"converter": int}}}

    def __init__(self) -> None:
        self._errors: List[Exception] = []

    def _check_errors(self) -> None:
        if not self._errors:
            return

        missing_options = {}
        for error in self._errors:
            if isinstance(error, MissingOption):
                if error.section not in missing_options:
                    missing_options[error.section] = set()
                missing_options[error.section].add(error.option)
        error_info = []
        for section, options in missing_options.items():
            info = f"It was not possible to read the options in the section '{section}': {', '.join(options)}"
            error_info.append(info)
        raise ValueError("\n".join(error_info))

    def _parse_section(self, parser: ConfigParser, section: str) -> Dict[str, Any]:
        data = {}
        for item_name, item_data in ConfigReader.STRUCTURE[section].items():
            try:
                converter = item_data.get("converter", str)
                if converter == int:
                    value = parser.getint(section, item_name)
                elif converter == float:
                    value = parser.getfloat(section, item_name)
                elif converter == bool:
                    value = parser.getboolean(section, item_name)
                else:
                    value = converter(parser.get(section, item_name))
            except Exception:
                if "default" in item_data:
                    value = item_data["default"]
                else:
                    value = None
                    self._errors.append(MissingOption(section, item_name))
            data[item_name] = value
        return data

    def read(self, config_path: str) -> Dict[str, Dict[str, Any]]:
        parser = ConfigParser()
        parser.read(config_path)
        data = {section: self._parse_section(parser, section) for section in ConfigReader.STRUCTURE}
        self._check_errors()
        return data
