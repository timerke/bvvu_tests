import argparse
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")


def analyze_logs_in_dir(dir_name: str) -> Optional[Dict[str, List]]:
    """
    Function analyzes logs from a given directory. Function creates a dictionary with data for three types of log:
    'general', 'urmc', 'xinet'.
    :param dir_name: directory name.
    :return: dictionary with data for three types of log.
    """

    if not os.path.exists(dir_name):
        logging.error("Directory '%s' does not exist", dir_name)
        return

    total_data = {}
    for log_type in ("general", "urmc", "xinet"):
        log_data = []
        for data_from_file_name in get_data_from_file_name(dir_name, log_type):
            data_from_file_name["log"] = read_file(os.path.join(dir_name, data_from_file_name["file_name"]))
            log_data.append(data_from_file_name)
        check_logs(log_type, log_data)
        total_data[log_type] = log_data
    return total_data


def check_logs(log_name: str, list_of_logs: List[Dict[str, Any]]) -> None:
    """
    Function checks logging journals. The check is done like this. The last record from the journal with number i
    is taken. It is checked whether this record is in the journal with number i+1. The absence of a record means
    the loss.
    :param log_name: log type (may be 'general', 'urmc' and 'xinet') to check;
    :param list_of_logs: log data list.
    """

    logging.info("")
    logging.info("%s log checking...", log_name)
    for index in range(len(list_of_logs) - 1):
        first_file_name = list_of_logs[index]["file_name"]
        if len(list_of_logs[index]["log"]) == 0:
            logging.debug("File '%s' is empty", first_file_name)
            continue
        last_record = list_of_logs[index]["log"][-1]
        second_file_name = list_of_logs[index + 1]["file_name"]
        next_log = list_of_logs[index + 1]["log"]
        if last_record not in next_log:
            logging.error("Last record '%s' from '%s' not found in '%s'", last_record, first_file_name,
                          second_file_name)
            list_of_logs[index + 1]["loss"] = True
        else:
            logging.debug("Last record from '%s' found in '%s'", first_file_name, second_file_name)
            list_of_logs[index + 1]["loss"] = False
    logging.info("Checking %s log completed", log_name)


def draw_data(data: Dict[str, List[Dict[str, Any]]], device_name: str = "") -> None:
    """
    Function visualizes data about the loss of records in the logs.
    :param data: dictionary with data for three types of log;
    :param device_name: name of device that owns the collected data.
    """

    total_log_size_over_time = {"datetime": [],
                                "size": []}
    log_loss_cases = {}
    for log_type, log_type_data in data.items():
        log_loss_cases[log_type] = {"datetime": [],
                                    "size": []}
        for item in log_type_data:
            if log_type == "general":
                total_log_size_over_time["datetime"].append(item["datetime"])
                total_log_size_over_time["size"].append(item["size"])
            if item.get("loss", False):
                log_loss_cases[log_type]["datetime"].append(item["datetime"])
                log_loss_cases[log_type]["size"].append(item["size"])

    number_of_cases_without_loss_at_all = 0
    for item in total_log_size_over_time["datetime"]:
        item_good = True
        for log_type_data in log_loss_cases.values():
            if item in log_type_data["datetime"]:
                item_good = False
                break
        if item_good:
            number_of_cases_without_loss_at_all += 1
    total_number_of_cases = len(total_log_size_over_time["datetime"])

    _, ax = plt.subplots()
    ax.scatter(total_log_size_over_time["datetime"], total_log_size_over_time["size"], facecolors="none",
               edgecolors="black")
    colors = {"general": "red",
              "urmc": "blue",
              "xinet": "green"}
    for log_type, log_type_data in log_loss_cases.items():
        number = len(log_type_data["size"])
        percentage = 100 * number / total_number_of_cases
        ax.scatter(log_type_data["datetime"], log_type_data["size"], c=colors[log_type], alpha=0.5,
                   label=f"{log_type} ({number}/{total_number_of_cases} = {percentage:.1f}%)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel(f"Время ({get_start_date(total_log_size_over_time)})")
    ax.set_ylabel("Размер журналов, Мбайт")
    ax.set_title(f"Потери записей в журналах БВВУ{f' {device_name}' if device_name else ''}\n"
                 f"(всего журналов - {total_number_of_cases}, журналов без потерь - "
                 f"{number_of_cases_without_loss_at_all}, "
                 f"{number_of_cases_without_loss_at_all / total_number_of_cases * 100:.1f}%)")
    ax.legend()
    plt.show()


def get_data_from_file_name(dir_name: str, log_type: str) -> Generator[Dict[str, Any], None, None]:
    """
    Function extracts useful information from the filename.
    :param dir_name: directory where files are stored;
    :param log_type: type of log file belongs to.
    :return: generator with dictionary with filename, date and time of log was saved and full log size.
    """

    pattern = re.compile(rf"{log_type} (\d+-\d+-\d+_\d+-\d+-\d+) (.*[kKMG])\.txt")
    for file_name in os.listdir(dir_name):
        result = pattern.search(file_name)
        if result:
            multiplier = {"M": 1,
                          "G": 1024,
                          "K": 0.00097656}.get(result.group(2)[-1].upper(), 1)
            yield {"file_name": file_name,
                   "datetime": datetime.strptime(result.group(1), "%Y-%m-%d_%H-%M-%S"),
                   "size": multiplier * float(result.group(2)[:-1])}


def get_start_date(data: Dict[str, List[Any]]) -> str:
    return data["datetime"][0].strftime("%d.%m.%Y")


def read_file(file_path: str) -> List[str]:
    """
    Function reads file.
    :param file_path: path to file.
    :return: list with lines from file.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return [log for log in file.read().split("\n") if log]


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Script to analyze logs")
    parser.add_argument("dir_name", type=str, help="Directory name containing logs")
    parser.add_argument("--device_name", type=str, default="", help="The name of device from which logs were collected")
    args = parser.parse_args()

    draw_data(analyze_logs_in_dir(os.path.join(os.path.curdir, args.dir_name)), args.device_name)
