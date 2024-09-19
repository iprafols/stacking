""" Basic structure for writers """

from stacking.errors import WriterError

accepted_options = {
    # option: description
    "output directory": "Directory to save the results. **Type: str**",
    "output file": "Filename to save the results. **Type: str**",
    "overwrite": "Overwrite the output file if it exists. **Type: bool**"
}
required_options = ["output directory", "output file"]
defaults = {}

ACCEPTED_SAVE_FORMATS = ["fits", "fits.gz"]


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
        if not self.output_directory.endswith("/"):
            self.output_directory += "/"

        self.output_file = config.get("output file")
        if self.output_file is None:
            raise WriterError(
                "Missing argument 'output file' required by Writer")
        if "/" in self.output_file:
            raise WriterError(
                "Variable 'output file' should not incude folders. "
                f"Found: {self.output_file}")
        format_ok = False
        for save_format in ACCEPTED_SAVE_FORMATS:
            if self.output_file.endswith(save_format):
                format_ok = True
                break
        if not format_ok:
            raise WriterError(
                "Invalid extension for 'output file'. Expected one of " +
                " ".join(ACCEPTED_SAVE_FORMATS) +
                f" Given filename: {self.output_file}")

        self.overwrite = config.getboolean("overwrite")
        if self.overwrite is None:
            raise WriterError("Missing argument 'overwrite' required by Writer")

    def write_results(self, stacker):
        """Write the results

        Arguments
        ---------
        stacker: Stacker
        The used stacker

        Raise
        -----
        WriterError if function was not overloaded by child class
        """
        raise WriterError(
            "Method 'write_results' was not overloaded by child class")
