import argparse
import logging
import os
import re
from datetime import datetime
from typing import List
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


class Analyzer:

    PATTERN = re.compile(r"^\[(.*) INFO\] \[(UIOB|SSH)\] Number of missing modules: (\d+), missing modules: \[(.*)\]$")
    SLOT_NUMBER: int = 16

    def __init__(self) -> None:
        self._ssh_missing_slot_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._ssh_slot_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._uiob_missing_module_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._uiob_module_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]

    def _analyze_log(self, log_file: str) -> None:
        """
        :param log_file: name of file with logs.
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
                    self._get_slots_from_ssh_record(result, log_time)

    @staticmethod
    def _draw_data(enabled: List[List[datetime]], disabled: List[List[datetime]], slot: bool) -> None:
        """
        :param enabled: history of modules in time when they were in working condition;
        :param disabled: history of modules in time when they were inactive;
        :param slot:
        """

        _, axs = plt.subplots(2, 1)
        total_min_x = None
        total_max_x = None
        for index in range(Analyzer.SLOT_NUMBER):
            e_times = enabled[index]
            d_times = disabled[index]
            if not e_times and not d_times:
                continue

            dump_percentage = round(100 * len(d_times) / (len(e_times) + len(d_times)), 2)
            if slot:
                label = f"Слот ttyACM{index} ({dump_percentage}% отвалов)"
            else:
                index += 1
                label = f"Модуль #{index} ({dump_percentage}% отвалов)"
            axs[0].scatter(e_times, len(e_times) * [index])
            axs[1].scatter(d_times, len(d_times) * [index], label=label)

            times = [*e_times, *d_times]
            local_min_x = min(times)
            if total_min_x is None or total_min_x > local_min_x:
                total_min_x = local_min_x
            local_max_x = max(times)
            if total_max_x is None or total_max_x < local_max_x:
                total_max_x = local_max_x

        if slot:
            y_label_1 = "Слоты по ssh"
            y_label_2 = "Отвалившиеся слоты"
        else:
            y_label_1 = "Модули в админке"
            y_label_2 = "Отвалившиеся модули"
        axs[0].set_ylabel(y_label_1)
        axs[1].set_ylabel(y_label_2)

        start_date = get_start_date(*enabled, *disabled)
        for ax in axs:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax.set_xlabel(f"Время {start_date}")
            ax.set_xlim([total_min_x, total_max_x])
            ax.label_outer()
        axs[1].legend(bbox_to_anchor=(0.95, 1), loc="upper left", prop={"size": 8})
        plt.show()

    def _get_modules_from_uiob_record(self, result, log_time: datetime) -> None:
        missing_modules = []
        for module in result.group(4).split(", "):
            if module:
                missing_modules.append(int(module))

        for module_index in range(1, Analyzer.SLOT_NUMBER + 1):
            if module_index in missing_modules:
                self._uiob_missing_module_history[module_index - 1].append(log_time)
            else:
                self._uiob_module_history[module_index - 1].append(log_time)

    def _get_slots_from_ssh_record(self, result, log_time: datetime) -> None:
        missing_slots = []
        pattern = re.compile(r"^'ttyACM(?P<index>\d+)'$")
        for slot in result.group(4).split(", "):
            new_result = pattern.match(slot)
            if new_result and new_result["index"]:
                missing_slots.append(int(new_result["index"]))

        for slot_index in range(Analyzer.SLOT_NUMBER):
            if slot_index in missing_slots:
                self._ssh_missing_slot_history[slot_index].append(log_time)
            else:
                self._ssh_slot_history[slot_index].append(log_time)

    def run(self, log_file: str) -> None:
        """
        :param log_file: name of file with logs.
        """

        self._analyze_log(log_file)
        self._draw_data(self._uiob_module_history, self._uiob_missing_module_history, slot=False)
        self._draw_data(self._ssh_slot_history, self._ssh_missing_slot_history, slot=True)


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
