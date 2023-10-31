import argparse
import logging
import os
import re
from datetime import datetime
from typing import List, Optional, Tuple
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


class Analyzer:

    PATTERN = re.compile(r"^\[(.*) INFO\] \[(UIOB|SSH)\] Number of missing modules: (\d+), missing modules: \[(.*)\]$")
    SLOT_NUMBER: int = 16

    def __init__(self) -> None:
        self._ssh_modules_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._ssh_missing_modules_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._uiob_modules_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._uiob_missing_modules_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]

    def _analyze_log(self, log_file: str) -> Optional[Tuple[List[List[datetime]], List[List[datetime]]]]:
        """
        :param log_file: name of file with logs.
        :return: two lists. In the first list - history of modules in time when they were in working condition.
        In the second list - history of modules in time when they were inactive.
        """

        if not os.path.exists(log_file):
            logging.error("File '%s' does not exist", log_file)
            return

        with open(log_file, "r", encoding="utf-8") as file:
            log = file.read().split("\n")

        for record in log:
            result = Analyzer.PATTERN.match(record)
            if result:
                log_time = datetime.strptime(result.group(1), "%Y-%m-%d %H:%M:%S")
                if "UIOB" in record:
                    self._get_modules_from_uiob_record(result, log_time)
                elif "SSH" in record:
                    self._get_modules_from_ssh_record(result, log_time)

    @staticmethod
    def _draw_data(enabled: List[List[datetime]], disabled: List[List[datetime]], is_uiob: bool) -> None:
        """
        :param enabled: history of modules in time when they were in working condition;
        :param disabled: history of modules in time when they were inactive;
        :param is_uiob:
        """

        _, (ax_1, ax_2) = plt.subplots(2, 1)
        for module_index in range(1, 17):
            e_times = enabled[module_index - 1]
            d_times = disabled[module_index - 1]
            dump_percentage = round(100 * len(d_times) / (len(e_times) + len(d_times)), 2)
            ax_1.scatter(e_times, len(e_times) * [module_index])
            ax_2.scatter(d_times, len(d_times) * [module_index],
                         label=f"Модуль #{module_index} (отваливается {dump_percentage}%)")

        start_date = get_start_date(*enabled, *disabled)
        for ax in (ax_1, ax_2):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax.set_xlabel(f"Время {start_date}")
        ax_1.set_ylabel("Модули в админке" if is_uiob else "Модули по ssh")
        ax_2.set_ylabel("Отвалившиеся модули")
        ax.legend()
        plt.show()

    def _get_modules_from_ssh_record(self, result, log_time) -> None:
        missing_modules = []
        pattern = re.compile(r"^'ttyACM(?P<index>\d+)'$")
        for module in result.group(4).split(", "):
            new_result = pattern.match(module)
            if new_result:
                print(new_result["index"])
                try:
                    missing_modules.append(int(new_result["index"]))
                except Exception:
                    pass

        for module_index in range(Analyzer.SLOT_NUMBER):
            if module_index in missing_modules:
                self._ssh_missing_modules_history[module_index].append(log_time)
            else:
                self._ssh_modules_history[module_index].append(log_time)

    def _get_modules_from_uiob_record(self, result, log_time) -> None:
        missing_modules = []
        for module in result.group(4).split(", "):
            try:
                missing_modules.append(int(module))
            except Exception:
                pass

        for module_index in range(1, 17):
            if module_index in missing_modules:
                self._uiob_missing_modules_history[module_index - 1].append(log_time)
            else:
                self._uiob_modules_history[module_index - 1].append(log_time)

    def run(self, log_file: str) -> None:
        """
        :param log_file: name of file with logs.
        """

        self._analyze_log(log_file)
        self._draw_data(self._uiob_modules_history, self._uiob_missing_modules_history, True)
        self._draw_data(self._ssh_modules_history, self._ssh_missing_modules_history, False)


def get_start_date(*args) -> str:
    """
    :param args: lists with datetimes.
    :return: smallest date from the lists.
    """

    start_datetime = None
    for data in args:
        if start_datetime is None or (data and start_datetime > data[0]):
            start_datetime = data[0]
    return start_datetime.strftime("%d.%m.%Y")


def run_analyzer() -> None:
    parser = argparse.ArgumentParser("Script to analyze log")
    parser.add_argument("log_file", type=str, help="Name of file with log")
    args = parser.parse_args()

    analyzer = Analyzer()
    analyzer.run(args.log_file)
