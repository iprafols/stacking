"""This module define several functions and variables related to logging"""
import logging
import os
import sys

# define new logger level: PROGRESS
PROGRESS_LEVEL_NUM = 15
logging.addLevelName(PROGRESS_LEVEL_NUM, "PROGRESS")


def progress(self, message, *args, **kws):
    """Function to log with level PROGRESS"""
    if self.isEnabledFor(PROGRESS_LEVEL_NUM):  # pragma: no branch
        # pylint: disable-msg=protected-access
        # this method will be attached to logging.Logger
        self._log(PROGRESS_LEVEL_NUM, message, args, **kws)


logging.Logger.progress = progress

# define new logger level: OK_WARNING
OK_WARNING_LEVEL_NUM = 31
logging.addLevelName(OK_WARNING_LEVEL_NUM, "WARNING OK")


def ok_warning(self, message, *args, **kws):
    """Function to log with level WARNING OK"""
    if self.isEnabledFor(OK_WARNING_LEVEL_NUM):  # pragma: no branch
        # pylint: disable-msg=protected-access
        # this method will be attached to logging.Logger
        self._log(OK_WARNING_LEVEL_NUM, message, args, **kws)


logging.Logger.ok_warning = ok_warning


def reset_logger():
    """This function reset the stacking logger by closing
    and removing its handlers.
    """
    logger = logging.getLogger("stacking")
    handlers = logger.handlers
    for handler in handlers[::-1]:
        handler.close()
        logger.removeHandler(handler)
    logger.addHandler(logging.NullHandler())


def setup_logger(logging_level_console=logging.DEBUG,
                 log_file=None,
                 logging_level_file=logging.DEBUG):
    """This function set up the logger for the package
    picca.delta_extraction

    Arguments
    ---------
    logging_level_console: int or str - Default: logging.DEBUG
    Logging level for the console handler. If str, it should be a Level from
    the logging module (i.e. CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET).
    Additionally, the user-defined levels PROGRESS and WARNING_OK are allowed.

    log_file: str or None
    Log file for logging

    logging_level_file: int or str - Default: logging.DEBUG
    Logging level for the file handler. If str, it should be a Level from
    the logging module (i.e. CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET).
    Additionally, the user-defined level PROGRESS and WARN_OK are allowed.
    Ignored if log_file is None.
    """
    if isinstance(logging_level_console, str):
        if logging_level_console.upper() == "PROGRESS":
            logging_level_console = PROGRESS_LEVEL_NUM
        elif logging_level_console.upper() == "WARN_OK":
            logging_level_console = OK_WARNING_LEVEL_NUM
        else:
            logging_level_console = getattr(logging,
                                            logging_level_console.upper())

    if isinstance(logging_level_file, str):
        if logging_level_file.upper() == "PROGRESS":
            logging_level_file = PROGRESS_LEVEL_NUM
        elif logging_level_file.upper() == "WARN_OK":
            logging_level_file = OK_WARNING_LEVEL_NUM
        else:
            logging_level_file = getattr(logging, logging_level_file.upper())

    logger = logging.getLogger("stacking")
    logger.setLevel(logging.DEBUG)

    # logging formatter
    formatter = logging.Formatter('[%(levelname)s]: %(message)s')

    # create console handler to logs messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging_level_console)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # create file handler which logs messages to file
    if log_file is not None:
        if os.path.exists(log_file):
            newfilename = f'{log_file}.{os.path.getmtime(log_file)}'
            os.rename(log_file, newfilename)
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging_level_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # sets up numba logger
    #logging.getLogger('numba').setLevel(logging.WARNING)
