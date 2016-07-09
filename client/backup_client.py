# coding=utf-8
import logging

from app import app


def create_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("backup")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler("test.log")

    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


if __name__ == '__main__':
    app.LOGGER = create_logger()
    app.run(debug=True, host='0.0.0.0')
