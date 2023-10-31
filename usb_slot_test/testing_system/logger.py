import logging


def add_file_handler(file_path: str) -> None:
    """
    :param file_path: path to the file where to save logs.
    """

    logging.info("Logs will be saved to a file '%s'", file_path)
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="[%(asctime)s %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)


def set_logger() -> None:
    logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S")
