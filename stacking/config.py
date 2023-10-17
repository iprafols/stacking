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
from stacking.rebin import Rebin
from stacking.stacker import Stacker
from stacking.utils import class_from_string, attribute_from_string
from stacking.writer import Writer

try:
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    STACKING_BASE = THIS_DIR.replace("stacking/stacking", "stacking")
    GIT_HASH = git.Repo(STACKING_BASE).head.object.hexsha
except InvalidGitRepositoryError:  # pragma: no cover
    GIT_HASH = "not known"

accepted_general_options = [
    "overwrite", "logging level console", "logging level file", "log",
    "output directory", "num processors", "run type"
]

accepted_section_options = ["type"]

default_config = {
    "general": {
        "overwrite": False,
        "log": "run.log",
        # New logging level defined in stacking.utils: PROGRESS
        # Numeric value is PROGRESS_LEVEL_NUM defined in utils.py
        "logging level console": "PROGRESS",
        "logging level file": "PROGRESS",
        "num processors": 0,
        "run type": "normal"
    },
    "rebin": {
        "type": "Rebin",
    },
    "run specs": {
        "git hash": GIT_HASH,
        "timestamp": str(datetime.now()),
    },
    "writer": {},
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

    output_directory: str
    Name of the directory where the deltas will be saved

    overwrite: bool
    If True, overwrite a previous run in the saved in the same output
    directory. Does not have any effect if the folder `output_directory` does not
    exist.

    reader: (class, configparser.SectionProxy)
    Class should be a child of Reader and the SectionProxy should contain a
    configuration section with the parameters necessary to initialize it

    run_type: str
    Run type (e.g normal, merge stack). See stacking_interface.py for more details

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
        self.output_directory = None
        self.run_type = None
        self.__format_general_section()

        # other sections
        self.reader = self.__format_section("reader", "readers", Reader)
        self.normalizer = self.__format_section("normalizer", "normalizers",
                                                Normalizer)
        self.stacker = self.__format_section("stacker", "stackers", Stacker)
        self.writer = self.__select_writer()

        # rebinning arguments
        _, self.rebin_args = self.__format_section("rebin", ".", Rebin)

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
            raise ConfigError(f"Missing section [{section_name}]")
        section = self.config[section_name]

        # first load the data class
        name = section.get("type")
        if name is None:
            raise ConfigError(f"In section [{section_name}], variable 'type' "
                              "is required")
        try:
            (loaded_type, default_args, accepted_options,
             required_options) = class_from_string(name, modules_folder)
        except ImportError as error:
            raise ConfigError(
                f"In section [{section_name}], error loading class {name}, "
                f"module could not be loaded") from error
        except AttributeError as error:
            raise ConfigError(
                f"In section [{section_name}], error loading class {name}, "
                f"module did not contain requested class") from error

        # this should not happen unless new features are wrongly coded
        if not issubclass(loaded_type, check_type):  # pragma: no cover
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
        # add output directory if necesssary
        if "output directory" in accepted_options and "output directory" not in section:
            section["output directory"] = self.output_directory
        # add overwrite if necesssary
        if "overwrite" in accepted_options and "overwrite" not in section:
            section["overwrite"] = f"{self.overwrite}"
        # add log directory if necessary
        if "log directory" in accepted_options and "log directory" not in section:
            section["log directory"] = f"{self.output_directory}log/"

        # update the section adding the default choices when necessary
        for key, value in default_args.items():
            if key not in section:
                section[key] = str(value)

        # check that required options are passed
        for key in required_options:
            if key not in section:
                raise ConfigError(
                    f"Missing required option '{key}' in section [{section_name}]. "
                    "Please review the configuration file. Note that the required "
                    "options might change depending on the class being loaded.")

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

        self.output_directory = section.get("output directory")
        if self.output_directory is None:
            raise ConfigError(
                "Missing variable 'output directory' in section [general]")
        if not self.output_directory.endswith("/"):
            self.output_directory += "/"

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
        self.log = self.output_directory + "log/" + self.log
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

        self.run_type = section.get("run type")
        # this should never be true as the general section is loaded in the
        # default dictionary
        if self.run_type is None:  # pragma: no cover
            raise ConfigError(
                "Missing variable 'run type' in section [general]")

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

    def __select_writer(self):
        """Select the appropriate writer

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
        stacker_type, _ = self.stacker
        stacker_module = stacker_type.__module__

        # find writer associated with the selected Stacker
        try:
            associated_writer = attribute_from_string("ASSOCIATED_WRITER",
                                                      stacker_module)
        # this should not happen unless new stackers are wrongly coded
        except AttributeError as error:  # pragma: no cover
            raise ConfigError(
                "Error finding writer associated with selected Stacker, "
                f"missing attribute 'associated_writer' in module {stacker_module} "
            ) from error

        # this should never be true as the general section is loaded in the
        # default dictionary
        if "writer" not in self.config:  # pragma: no cover
            raise ConfigError("Missing section [writer]")
        section = self.config["writer"]
        # add writer type
        if "type" in section:
            raise ConfigError(
                "Section [writer] does not accept argument 'type'. "
                "This should be defined in the 'ASSOCIATED_WRITER' attribute "
                "of the selected Stacker")
        self.config["writer"]["type"] = associated_writer

        return self.__format_section("writer", "writers", Writer)

    def initialize_folders(self):
        """Initialize output folders

        Raise
        -----
        ConfigError if the output path was already used and the
        overwrite is not selected
        """
        if not os.path.exists(f"{self.output_directory}/.config.ini"):
            os.makedirs(self.output_directory, exist_ok=True)
            os.makedirs(self.output_directory + "stack/", exist_ok=True)
            os.makedirs(self.output_directory + "log/", exist_ok=True)
            self.write_config()
        elif self.overwrite:
            os.makedirs(self.output_directory + "stack/", exist_ok=True)
            os.makedirs(self.output_directory + "log/", exist_ok=True)
            self.write_config()
        else:
            raise ConfigError("Specified folder contains a previous run. "
                              "Pass overwrite option in configuration file "
                              "in order to ignore the previous run or "
                              "change the output path variable to point "
                              f"elsewhere. Folder: {self.output_directory}")

    def write_config(self):
        """This function writes the configuration options for later
        usages. The file is saved under the name .config.ini and in
        the self.output_directory folder
        """
        outname = f"{self.output_directory}/.config.ini"
        if os.path.exists(outname):
            newname = f"{outname}.{os.path.getmtime(outname)}"
            os.rename(outname, newname)
        with open(outname, 'w', encoding="utf-8") as config_file:
            self.config.write(config_file)
