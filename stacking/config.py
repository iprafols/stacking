"""This module defines the Config class.
This class is responsible for managing the options selected for the user and
contains the default configuration.
"""
from configparser import ConfigParser
import os
from datetime import datetime
import git
from git.exc import InvalidGitRepositoryError

# stacking imports
from stacking.errors import ConfigError
from stacking.logging_utils import setup_logger
from stacking.normalizer import Normalizer
from stacking.reader import Reader
from stacking.stacker import Stacker
from stacking.utils import class_from_string

try:
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    PICCA_BASE = THIS_DIR.split("py/picca")[0]
    GIT_HASH = git.Repo(PICCA_BASE).head.object.hexsha
except InvalidGitRepositoryError:  # pragma: no cover
    GIT_HASH = "not known"

accepted_general_options = [
    "overwrite", "logging level console", "logging level file", "log",
    "out dir", "num processors"
]

accepted_section_options = ["type", "module name"]

default_config = {
    "general": {
        "overwrite": False,
        "log": "run.log",
        # New logging level defined in stacking.utils: PROGRESS
        # Numeric value is PROGRESS_LEVEL_NUM defined in utils.py
        "logging level console": "PROGRESS",
        "logging level file": "PROGRESS",
        "num processors": 0,
    },
    "run specs": {
        "git hash": GIT_HASH,
        "timestamp": str(datetime.now()),
    }
}


class Config:
    """Class to manage the configuration file

    Methods
    -------
    __init__
    __format_general_section
    __parse_environ_variables
    initialize_folders
    write_config

    Attributes
    ---------
    config: ConfigParser
    A ConfigParser instance with the user configuration

    log: str or None
    Name of the log file. None for no log file

    logger: logging.Logger
    Logger object

    logging_level_console: str
    Level of console logging. Messages with lower priorities will not be logged.
    Accepted values are (in order of priority) NOTSET, DEBUG, PROGRESS, INFO,
    WARNING, WARNING_OK, ERROR, CRITICAL.

    logging_level_file: str
    Level of file logging. Messages with lower priorities will not be logged.
    Accepted values are (in order of priority) NOTSET, DEBUG, PROGRESS, INFO,
    WARNING, WARNING_OK, ERROR, CRITICAL.

    normalizer: (class, configparser.SectionProxy)
    Class should be a child of Normalizer and the SectionProxy should contain a
    configuration section with the parameters necessary to initialize it

    num_processors: int
    Number of processors to use for multiprocessing-enabled tasks (will be passed
    downstream to relevant classes like e.g. ExpectedFlux or Data)

    out_dir: str
    Name of the directory where the deltas will be saved

    overwrite: bool
    If True, overwrite a previous run in the saved in the same output
    directory. Does not have any effect if the folder `out_dir` does not
    exist.

    reader: (class, configparser.SectionProxy)
    Class should be a child of Reader and the SectionProxy should contain a
    configuration section with the parameters necessary to initialize it

    stacker: (class, configparser.SectionProxy)
    Class should be a child of Stacker and the SectionProxy should contain a
    configuration section with the parameters necessary to initialize it
    """

    def __init__(self, filename):
        """Initializes class instance

        Arguments
        ---------
        filename: str
        Name of the config file
        """
        self.config = ConfigParser()
        # with this we allow options to use capital letters
        self.config.optionxform = lambda option: option
        # load default configuration
        self.config.read_dict(default_config)
        # now read the configuration file
        if os.path.isfile(filename):
            self.config.read(filename)
        else:
            raise ConfigError(f"Config file not found: {filename}")

        # parse the environ variables
        self.__parse_environ_variables()

        # format the sections
        # general section
        self.overwrite = None
        self.log = None
        self.logging_level_console = None
        self.logging_level_file = None
        self.num_processors = None
        self.out_dir = None
        self.__format_general_section()

        # other sections
        self.reader = self.__format_section("reader", "readers", Reader)
        self.normalizer = self.__format_section("normalizer", "normalizers",
                                                Normalizer)
        self.stacker = self.__format_section("stacker", "stackers", Stacker)

        # initialize folders where data will be saved
        self.initialize_folders()

        # setup logger
        setup_logger(logging_level_console=self.logging_level_console,
                     log_file=self.log,
                     logging_level_file=self.logging_level_file)

    def __format_section(self, section_name, modules_folder, check_type):
        """Format the a section of the parser into usable data

        Arguments
        ---------
        section_name: str
        The name of the section

        modules_folder: str
        Default folder to search for modules

        check_type: class
        Type of the class that should be loaded

        Return
        ------
        loaded_type: class
        The loaded class

        section: configparser.SectionProxy
        Parsed options to initialize loaded class

        Raise
        -----
        ConfigError if the config file is not correct
        """
        if section_name not in self.config:
            raise ConfigError("Missing section [data]")
        section = self.config["section_name"]

        # first load the data class
        name = section.get("type")
        if name is None:
            raise ConfigError(f"In section [{section_name}], variable 'type' "
                              "is required")
        module_name = section.get("module name")
        try:
            (loaded_type, default_args,
             accepted_options) = class_from_string(name, module_name,
                                                   modules_folder)
        except ImportError as error:
            raise ConfigError(
                f"Error loading class {name}, "
                f"module {module_name} could not be loaded") from error
        except AttributeError as error:
            raise ConfigError(
                f"Error loading class {name}, "
                f"module {module_name} did not contain requested class"
            ) from error

        if not issubclass(loaded_type, check_type):
            raise ConfigError(
                f"Error loading class {loaded_type.__name__}. "
                f"This class should inherit from {check_type.__name__} but "
                "it does not. Please check for correct inheritance "
                "pattern.")

        # check that arguments are valid
        accepted_options += accepted_section_options.copy()
        for key in section:
            if key not in accepted_options:
                raise ConfigError(
                    f"Unrecognised option in section [{section_name}]. "
                    f"Found: '{key}'. Accepted options are {accepted_options}")

        # add num processors if necesssary
        if "num processors" in accepted_options and "num processors" not in section:
            section["num processors"] = str(self.num_processors)

        # update the section adding the default choices when necessary
        for key, value in default_args.items():
            if key not in section:
                section[key] = str(value)

        # finally add the information to self.data
        return (loaded_type, section)

    def __format_general_section(self):
        """Format the general section of the parser into usable data

        Raise
        -----
        ConfigError if the config file is not correct
        """
        # this should never be true as the general section is loaded in the
        # default dictionary
        if "general" not in self.config:  # pragma: no cover
            raise ConfigError("Missing section [general]")
        section = self.config["general"]

        # check that arguments are valid
        for key in section.keys():
            if key not in accepted_general_options:
                raise ConfigError("Unrecognised option in section [general]. "
                                  f"Found: '{key}'. Accepted options are "
                                  f"{accepted_general_options}")

        self.out_dir = section.get("out dir")
        if self.out_dir is None:
            raise ConfigError("Missing variable 'out dir' in section [general]")
        if not self.out_dir.endswith("/"):
            self.out_dir += "/"

        self.overwrite = section.getboolean("overwrite")
        # this should never be true as the general section is loaded in the
        # default dictionary
        if self.overwrite is None:  # pragma: no cover
            raise ConfigError(
                "Missing variable 'overwrite' in section [general]")

        self.log = section.get("log")
        # this should never be true as the general section is loaded in the
        # default dictionary
        if self.log is None:  # pragma: no cover
            raise ConfigError("Missing variable 'log' in section [general]")
        if "/" in self.log:
            raise ConfigError(
                "Variable 'log' in section [general] should not incude folders. "
                f"Found: {self.log}")
        self.log = self.out_dir + "Log/" + self.log
        section["log"] = self.log

        self.logging_level_console = section.get("logging level console")
        # this should never be true as the general section is loaded in the
        # default dictionary
        if self.logging_level_console is None:  # pragma: no cover
            raise ConfigError(
                "Missing variable 'logging level console' in section [general]")
        self.logging_level_console = self.logging_level_console.upper()

        self.logging_level_file = section.get("logging level file")
        # this should never be true as the general section is loaded in the
        # default dictionary
        if self.logging_level_file is None:  # pragma: no cover
            raise ConfigError(
                "In section 'logging level file' in section [general]")
        self.logging_level_file = self.logging_level_file.upper()

        self.num_processors = section.getint("num processors")
        # this should never be true as the general section is loaded in the
        # default dictionary
        if self.num_processors is None:  # pragma: no cover
            raise ConfigError(
                "Missing variable 'num processors' in section [general]")

    def __parse_environ_variables(self):
        """Read all variables and replaces the enviroment variables for their
        actual values. This assumes that enviroment variables are only used
        at the beggining of the paths.

        Raise
        -----
        ConfigError if an environ variable was not defined
        """
        for section in self.config:
            for key, value in self.config[section].items():
                if value.startswith("$"):
                    pos = value.find("/")
                    if os.getenv(value[1:pos]) is None:
                        raise ConfigError(
                            f"In section [{section}], undefined "
                            f"environment variable {value[1:pos]} "
                            "was found")
                    self.config[section][key] = value.replace(
                        value[:pos], os.getenv(value[1:pos]))

    def initialize_folders(self):
        """Initialize output folders

        Raise
        -----
        ConfigError if the output path was already used and the
        overwrite is not selected
        """
        if not os.path.exists(f"{self.out_dir}/.config.ini"):
            os.makedirs(self.out_dir, exist_ok=True)
            os.makedirs(self.out_dir + "stack/", exist_ok=True)
            os.makedirs(self.out_dir + "log/", exist_ok=True)
            self.write_config()
        elif self.overwrite:
            os.makedirs(self.out_dir + "stack/", exist_ok=True)
            os.makedirs(self.out_dir + "log/", exist_ok=True)
            self.write_config()
        else:
            raise ConfigError("Specified folder contains a previous run. "
                              "Pass overwrite option in configuration file "
                              "in order to ignore the previous run or "
                              "change the output path variable to point "
                              f"elsewhere. Folder: {self.out_dir}")

    def write_config(self):
        """This function writes the configuration options for later
        usages. The file is saved under the name .config.ini and in
        the self.out_dir folder
        """
        outname = f"{self.out_dir}/.config.ini"
        if os.path.exists(outname):
            newname = f"{outname}.{os.path.getmtime(outname)}"
            os.rename(outname, newname)
        with open(outname, 'w', encoding="utf-8") as config_file:
            self.config.write(config_file)
