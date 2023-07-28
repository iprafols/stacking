""" Basic structure for writers """

from stacking.errors import WriterError

accepted_options = ["output directory"]
required_options = ["output directory"]


class Writer:
    """Abstract class to write the results

    Methods
    -------
    __init__
    __parse_config
    write_results

    Attributes
    ----------
    output_directory: str
    The output directory
    """

    def __init__(self, config):
        """Initialize class instance"""

        self.output_directory = None
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
        self.output_directory = config.get("output directory")
        if self.output_directory is None:
            raise WriterError(
                "Missing argument 'output directory' required by Writer")

    def write_results(self):
        """Write the results

        Raise
        -----
        WriterError if function was not overloaded by child class
        """
        raise WriterError(
            "Method 'write_results' was not overloaded by child class")
