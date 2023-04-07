import argparse
import logging
import os
import re
from datetime import datetime
from typing import List, Optional, Tuple
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")


def analyze_log(log_file_name: str) -> Optional[Tuple[List[List[datetime]], List[List[datetime]]]]:
    """
    Function analyzes logs from a given file.
    :param log_file_name: name of file with logs.
    :return: two lists. In the first list - history of modules in time when they were in working condition.
    In the second list - history of modules in time when they were inactive.
    """

    if not os.path.exists(log_file_name):
        logging.error("File '%s' does not exist", log_file_name)
        return

    with open(log_file_name, "r", encoding="utf-8") as file:
        log = file.read().split("\n")

    enabled_modules_history = [[] for _ in range(16)]
    disabled_modules_history = [[] for _ in range(16)]
    pattern = re.compile(r"^\[(.*) INFO\] Number of disabled modules: (\d+), disabled modules: \[(.*)\]$")
    for record in log:
        result = pattern.match(record)
        if result:
            log_time = datetime.strptime(result.group(1), "%Y-%m-%d %H:%M:%S")
            disabled_modules = list(map(int, result.group(3).split(", ")))
            for module_index in range(1, 17):
                if module_index in disabled_modules:
                    disabled_modules_history[module_index - 1].append(log_time)
                else:
                    enabled_modules_history[module_index - 1].append(log_time)
    return enabled_modules_history, disabled_modules_history


def draw_data(enabled: List[List[datetime]], disabled: List[List[datetime]]) -> None:
    """
    Function visualizes data about disabled and enabled modules in BVVU device.
    :param enabled: history of modules in time when they were in working condition;
    :param disabled: history of modules in time when they were inactive.
    """

    _, (ax_1, ax_2) = plt.subplots(2, 1)
    for module_index in range(1, 17):
        times = enabled[module_index - 1]
        ax_1.scatter(times, len(times) * [module_index])
        times = disabled[module_index - 1]
        ax_2.scatter(times, len(times) * [module_index])
    for ax in (ax_1, ax_2):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.set_xlabel("Время")
    ax_1.set_ylabel("Модули в админке")
    ax_2.set_ylabel("Отвалившиеся модули")
    ax.legend()
    plt.show()


def get_start_date(*args) -> str:
    """

    :param args:
    :return:
    """


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Script to analyze log")
    parser.add_argument("log_file", type=str, help="Name of file with log")
    args = parser.parse_args()
    history = analyze_log(os.path.join(os.path.curdir, args.log_file))
    if history:
        draw_data(*history)
