#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import logging
import logging.config as lc
import os
from pathlib import Path
from typing import Union, Dict

import numpy as np
from yaml import load, FullLoader


class Singleton(type):
    """A metaclass that can used to turn your class in a Singleton"""
    __instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]


class LogMessage(object):
    def __init__(self, fmt, args):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


class Logger(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger._log(level, LogMessage(msg, args), (), **kwargs)


class LogHelper:

    __logger:Logger = None

    @staticmethod
    def __initialize():
        # TODO set this from config options
        logging.raiseExceptions = True

        path:str = os.path.abspath(os.path.dirname(__file__))
        file:str = os.path.join(path, "config/logging.conf")

        if file is not None and len(file) > 0:
            config_file:Path = Path(file)

            if config_file.exists() and config_file.is_file():
                conf = load(config_file.open("r"), Loader=FullLoader)
                lc.dictConfig(conf)
                LogHelper.__logger = Logger(logging.getLogger("openSpectra"))
                logger = LogHelper.logger("Logger")
                logger.info("Logger initialize from default configuration, {0}", file)
            else:
                LogHelper.__fallback_initialize()
        else:
            LogHelper.__fallback_initialize()

    @staticmethod
    def __fallback_initialize():
        logging.basicConfig(format="{asctime} [{levelname}] [{name}] {message}",
            style="{", level=logging.DEBUG)
        LogHelper.__logger = logging.getLogger("openSpectra")
        logger = LogHelper.logger("Logger")
        logger.info("Could not find default logger configuration file, using fallback config.")

    @staticmethod
    def logger(name:str) -> logging.Logger:
        if LogHelper.__logger is None:
            LogHelper.__initialize()

        return Logger(logging.getLogger("openSpectra").getChild(name))


class OpenSpectraDataTypes:

    Floats = (np.float32, np.float64,)
    Ints = (np.uint8, np.int16, np.int32, np.uint16,np.uint32, np.int64, np.uint64)
    Complexes = (np.complex64, np.complex128)


class OpenSpectraProperties:

    __LOG: Logger = LogHelper.logger("OpenSpectraProperties")
    __properties = None

    def __init__(self):
        self.__prop_map:Dict[str, Union[str, int, float, bool]] = dict()
        self.__load_properties()

    def __load_properties(self, file_name:str=None):
        file:str = file_name
        if file_name is None:
            path: str = os.path.abspath(os.path.dirname(__file__))
            file: str = os.path.join(path, "config/openspectra.properties")

        if file is not None and len(file) > 0:
            config_file: Path = Path(file)
            if config_file.exists() and config_file.is_file():
                OpenSpectraProperties.__LOG.info("Loading configuration properties from {}".format(config_file))

                with config_file.open() as properties_file:
                    for line in properties_file:
                        line = line.strip()
                        # ignore # as a comment
                        if not line.startswith("#") and len(line) > 0:
                            nv_pair = line.split('=')
                            if len(nv_pair) == 2:
                                name: str = nv_pair[0]
                                value: Union[str, int, float] = OpenSpectraProperties.__get_typed_value(nv_pair[1])
                                self.__prop_map[name] = value
                                OpenSpectraProperties.__LOG.info("name: {}, value: {}".format(name, value))
                            else:
                                OpenSpectraProperties.__LOG.warning("Ignore malformed line [{}] in file {}".
                                    format(line, file))
            else:
                OpenSpectraProperties.__LOG.error("Failed to load configuration file {}, exists {}, is file {}".
                    format(file, config_file.exists(), config_file.is_file()))

    def __get_property_value(self, name:str) -> Union[str, int, float, bool]:
        return self.__prop_map.get(name)

    @staticmethod
    def __get_typed_value(value:str) -> Union[str, int, float, bool]:
        result:Union[str, int, float] = None
        if all(s.isalpha() or s.isspace() for s in value):
            if value == "True":
                result = True
            elif value == "False":
                result = False
            else:
                result = value
        elif value.count(".") == 1:
            try:
                result = float(value)
            except ValueError:
                result = value
        elif value.isdigit():
            try:
                result = int(value)
            except ValueError:
                result = value

        return result

    @staticmethod
    def __get_instance():
        if OpenSpectraProperties.__properties is None:
            OpenSpectraProperties.__properties = OpenSpectraProperties()

        return OpenSpectraProperties.__properties

    @staticmethod
    def get_property(name:str, defalut:Union[str, int, float, bool]=None) -> Union[str, int, float, bool]:
        result = OpenSpectraProperties.__get_instance().__get_property_value(name)
        if result is None:
            return defalut
        else:
            return result

    @staticmethod
    def add_properties(file_name:str):
        """Add properties in addition to the default properties over writing any duplicates"""
        OpenSpectraProperties.__get_instance().__load_properties(file_name)
