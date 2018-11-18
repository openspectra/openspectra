import logging
import logging.config as lc
import os
from pathlib import Path

from yaml import load


class Logger:

    __logger:logging.Logger = None

    @staticmethod
    def __initialize():
        # TODO set this from config options
        logging.raiseExceptions = True

        path: str = os.path.abspath(os.path.dirname(__file__))
        file: str = os.path.join(path, "config/logging.conf")

        if file is not None and len(file) > 0:
            config_file: Path = Path(file)

            if config_file.exists() and config_file.is_file():
                conf = load(config_file.open("r"))
                lc.dictConfig(conf)
                Logger.__logger = logging.getLogger("openSpectra")
                logger = Logger.logger("Logger")
                logger.info("Logger initialize from default configuration, %s", file)
            else:
                Logger.__fallback_initialize()
        else:
            Logger.__fallback_initialize()

    @staticmethod
    def __fallback_initialize():
        logging.basicConfig(format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s", level=logging.DEBUG)
        Logger.__logger = logging.getLogger("openSpectra")
        logger = Logger.logger("Logger")
        logger.info("Could not find default logger configuration file, using fallback config.")

    @staticmethod
    def logger(name:str) -> logging.Logger:
        # TODO thread safety??
        if Logger.__logger is None:
            Logger.__initialize()

        return Logger.__logger.getChild(name)
