import argparse
import logging
import os
import re
from datetime import datetime
from typing import List
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


class Analyzer:

    PATTERN = re.compile(r"^\[(.*) INFO\] \[(UIOB|SSH_DEV|SSH_DEV_XIMC)\] Number of missing modules: (\d+), "
                         r"missing modules: \[(.*)\]$")
    SLOT_NUMBER: int = 16

    def __init__(self) -> None:
        self._ssh_dev_missing_slot_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._ssh_dev_slot_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._ssh_dev_ximc_missing_slot_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
        self._ssh_dev_ximc_slot_history: List[List[datetime]] = [[] for _ in range(Analyzer.SLOT_NUMBER)]
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
                if "[UIOB]" in record:
                    self._get_modules_from_record(result, log_time, self._uiob_module_history,
                                                  self._uiob_missing_module_history)
                elif "[SSH_DEV]" in record:
                    self._get_slots_from_ssh_record(result, log_time)
                elif "[SSH_DEV_XIMC]" in record:
                    self._get_modules_from_record(result, log_time, self._ssh_dev_ximc_slot_history,
                                                  self._ssh_dev_ximc_missing_slot_history)

    @staticmethod
    def _draw_data(enabled: List[List[datetime]], disabled: List[List[datetime]], legend_format: str,
                   y_labels: List[str]) -> None:
        """
        :param enabled: history of modules in time when they were in working condition;
        :param disabled: history of modules in time when they were inactive;
        :param slot:
        """

        fig, axs = plt.subplots(2, 1)
        total_min_x = None
        total_max_x = None
        for index in range(Analyzer.SLOT_NUMBER):
            e_times = enabled[index]
            d_times = disabled[index]
            if not e_times and not d_times:
                continue

            dump_percentage = round(100 * len(d_times) / (len(e_times) + len(d_times)), 2)
            index += 1
            axs[0].scatter(e_times, len(e_times) * [index], label=legend_format.format(index=index,
                                                                                       dump_percentage=dump_percentage))
            axs[1].scatter(d_times, len(d_times) * [index])

            times = [*e_times, *d_times]
            local_min_x = min(times)
            if total_min_x is None or total_min_x > local_min_x:
                total_min_x = local_min_x
            local_max_x = max(times)
            if total_max_x is None or total_max_x < local_max_x:
                total_max_x = local_max_x

        for i, y_label in enumerate(y_labels):
            axs[i].set_ylabel(y_label)

        start_date = get_start_date(*enabled, *disabled)
        for ax in axs:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax.set_xlabel(f"Время {start_date}")
            ax.set_xlim([total_min_x, total_max_x])
            ax.set_ylim([0, Analyzer.SLOT_NUMBER + 1])
            ax.label_outer()
        axs[0].legend(bbox_to_anchor=(0.1, 1.3), loc="upper left", ncol=4)
        plt.show()

    @staticmethod
    def _get_modules_from_record(result, log_time: datetime, history: List[List[datetime]],
                                 missing_history: List[List[datetime]]) -> None:
        missing_modules = []
        for module in result.group(4).split(", "):
            if module:
                module = module.strip("'")
                missing_modules.append(int(module))

        for module_index in range(1, Analyzer.SLOT_NUMBER + 1):
            if module_index in missing_modules:
                missing_history[module_index - 1].append(log_time)
            else:
                history[module_index - 1].append(log_time)

    def _get_slots_from_ssh_record(self, result, log_time: datetime) -> None:
        missing_slots = []
        pattern = re.compile(r"^'ttyACM(?P<index>\d+)'$")
        for slot in result.group(4).split(", "):
            new_result = pattern.match(slot)
            if new_result:
                missing_slots.append(int(new_result["index"]))

        for slot_index in range(Analyzer.SLOT_NUMBER):
            if slot_index in missing_slots:
                self._ssh_dev_missing_slot_history[slot_index].append(log_time)
            else:
                self._ssh_dev_slot_history[slot_index].append(log_time)

    def run(self, log_file: str) -> None:
        """
        :param log_file: name of file with logs.
        """

        self._analyze_log(log_file)
        self._draw_data(self._uiob_module_history, self._uiob_missing_module_history,
                        legend_format="Модуль #{index} ({dump_percentage}% отвалов)",
                        y_labels=["Модули в админке", "Отвалившиеся модули"])
        self._draw_data(self._ssh_dev_ximc_slot_history, self._ssh_dev_ximc_missing_slot_history,
                        legend_format="Слот #{index} ({dump_percentage}% отвалов)",
                        y_labels=["Слоты по ssh (/dev/ximc)", "Отвалившиеся слоты"])
        self._draw_data(self._ssh_dev_ximc_slot_history, self._ssh_dev_ximc_missing_slot_history,
                        legend_format="Слот ttyACM{index} ({dump_percentage}% отвалов)",
                        y_labels=["Слоты по ssh (/dev)", "Отвалившиеся слоты"])


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
