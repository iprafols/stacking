""" Basic structure for readers """

from stacking.errors import ReaderError

accepted_options = ["input directory"]
required_options = ["input directory"]
defaults = {}


class Reader:
    """Abstract class to define the readers skeleton

    Methods
    -------
    __init__
    __parse_config

    Attributes
    ----------
    input_directory: str
    The input directory

    spectra: list of Spectrum
    The read spectra
    """

    def __init__(self, config):
        """Initialize class instance"""
        self.spectra = []
        # catalogue should be a table with metadata for each spectrum
        # ordering should be maintained between spectra and catalogue
        self.catalogue = None

        self.input_directory = None
        self.__parse_config(config)

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        ReaderError upon missing required variables
        """
        self.input_directory = config.get("input directory")
        if self.input_directory is None:
            raise ReaderError(
                "Missing argument 'input directory' required by Reader")

    def read_data(self):
        """Read the data

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        raise ReaderError(
            "Method 'read_data' was not overloaded by child class")
