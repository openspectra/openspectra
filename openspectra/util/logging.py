import logging
import logging.config as lc
import os
from pathlib import Path

from yaml import load


class Logger:

    __logger:logging.Logger = None

    @staticmethod
    def __initialize():
        path: str = os.path.abspath(os.path.dirname(__file__))
        file: str = os.path.join(path, "logging.conf")

        if file is not None and len(file) > 0:
            config_file: Path = Path(file)

            if config_file.exists() and config_file.is_file():
                conf = load(config_file.open("r"))
                lc.dictConfig(conf)
                Logger.__logger = logging.getLogger("openSpectra")
            else:
                Logger.__default_initialize()
        else:
            Logger.__default_initialize()

    @staticmethod
    def __default_initialize():
        #TODO
        pass

    @staticmethod
    def logger(name:str) -> logging.Logger:
        # TODO thread safety??
        if Logger.__logger is None:
            Logger.__initialize()

        return Logger.__logger.getChild(name)
