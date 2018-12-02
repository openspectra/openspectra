import logging
import logging.config as lc
import os
from pathlib import Path

import numpy as np
from yaml import load


class LogHelper:

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
                LogHelper.__logger = logging.getLogger("openSpectra")
                logger = LogHelper.logger("Logger")
                logger.info("Logger initialize from default configuration, %s", file)
            else:
                LogHelper.__fallback_initialize()
        else:
            LogHelper.__fallback_initialize()

    @staticmethod
    def __fallback_initialize():
        logging.basicConfig(format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s", level=logging.DEBUG)
        LogHelper.__logger = logging.getLogger("openSpectra")
        logger = LogHelper.logger("Logger")
        logger.info("Could not find default logger configuration file, using fallback config.")

    @staticmethod
    def logger(name:str) -> logging.Logger:
        # TODO thread safety??
        if LogHelper.__logger is None:
            LogHelper.__initialize()

        return LogHelper.__logger.getChild(name)


class OpenSpectraDataTypes:

    Floats = (np.float32, np.float64,)
    Ints = (np.uint8, np.int16, np.int32, np.uint16,np.uint32, np.int64, np.uint64)
    Complexes = (np.complex64, np.complex128)


class OpenSpectraProperties:

    FloatBins = 512