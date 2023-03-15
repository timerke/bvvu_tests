import argparse
import logging
import os
from datetime import datetime
from typing import Dict, List
from uiobapi import Uiob


def get_and_save_logs(dir_name: str, uiob: Uiob, logs_size: str, logs: Dict[str, Dict[str, List[str]]]) -> None:
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for log_name, logs_and_file_names in logs.items():
        func_name_to_get_log = {"general": "general_logs",
                                "urmc": "tango_urmc_logs",
                                "xinet": "xinet_logs"}.get(log_name)
        func = getattr(uiob.os.journal, func_name_to_get_log, None)
        if func is None:
            raise ValueError(f"Failed to find method to get {log_name} log from uiob")
        new_log = func()
        logging.info("%s logs received", log_name)
        file_name = f"{log_name} {now} {logs_size}.txt" if logs_size else f"{log_name} {now}.txt"
        file_path = os.path.join(dir_name, file_name)
        if not logs_and_file_names:
            logs_and_file_names["logs"] = []
            logs_and_file_names["file_names"] = []
        logs_and_file_names["logs"].append(new_log)
        logs_and_file_names["file_names"].append(file_name)
        save_logs(file_path, new_log)


def get_last_log(logs: str) -> str:
    logs_list = logs.split("\n")
    if not logs_list:
        return ""

    for line in logs_list[::-1]:
        if line:
            return line
    return ""


def make_dir(dir_name: str) -> str:
    dir_path = os.path.join(os.path.curdir, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Script performs a multiple reload of the BVVU and downloads the logs")
    parser.add_argument("--host", type=str, help="IP address of tested BVVU")
    parser.add_argument("--port", type=int, help="Port for ssh connection")
    parser.add_argument("--username", type=str, help="Username for connecting to BVVU via ssh")
    parser.add_argument("--password", type=str, help="Password for connecting to BVVU via ssh")
    parser.add_argument("--reboots", type=int, default=100, help="Number of BVVU reboots")
    return parser.parse_args()


def save_logs(file_path: str, log: str) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(log)
    logging.info("Log saved to file '%s'", file_path)
