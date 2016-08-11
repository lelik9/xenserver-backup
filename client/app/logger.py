# coding=utf-8
import logging


def create_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("backup_restore")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler("test.log")

    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


logger = create_logger()
