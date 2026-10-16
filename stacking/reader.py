""" Basic structure for readers """
import logging

from stacking.errors import ReaderError

accepted_options = {
    # option: description
    "input directory":
        "Directory containing the spectra. **Type: str**",
    "max num spec": (
        "Maximum number of spectra to load. None for no maximum. Multiple spectra "
        "comming from the same line of sight are not counted here. **Type: int or None**"
    ),
    "skip N first spec":
        "Skip the N first spectra in the catalogue. **Type: int**",
}
required_options = ["input directory"]
defaults = {
    "skip N first spec": 0,
}


class Reader:
    """Abstract class to define the readers skeleton

    Methods
    -------
    __init__
    __parse_config

    Attributes
    ----------
    catalogue: astropy.table.Table
    Metadata associated with the spectra. Ordering should be maintained
    between spectra and catalogue

    input_directory: str
    The input directory

    spectra: list of Spectrum
    The read spectra. Ordering should be maintained
    between spectra and catalogue
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        self.logger = logging.getLogger(__name__)
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

        self.max_num_spec = config.getint("max num spec")

        self.skip_n_first_spec = config.getint("skip N first spec")
        if self.skip_n_first_spec is None:
            raise ReaderError(
                "Missing argument 'skip N first spec' required by Reader")

    def read_data(self):
        """Read the data

        Return
        ------
        spectra: list of Spectrum
        The list of spectra

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        raise ReaderError(
            "Method 'read_data' was not overloaded by child class")

    def trim_catalogue(self):
        """Trim the catalogue by removing the first N rows and limiting its
        size to M entries.

        N is stored in ``self.skip_n_first_spec`` and M is stored in
        ``self.max_num_spec``. If ``self.max_num_spec`` is None, then do not
        limit by size.

        Raise
        -----
        ReaderError if the child class did not initialize required attributes.
        """
        if not hasattr(self, "skip_n_first_spec"):
            raise ReaderError(
                "Reader child class must define attribute 'skip_n_first_spec' "
                "before calling 'trim_catalogue'")
        if not hasattr(self, "max_num_spec"):
            raise ReaderError(
                "Reader child class must define attribute 'max_num_spec' "
                "before calling 'trim_catalogue'")

        if self.max_num_spec is None and self.skip_n_first_spec > 0:
            self.logger.progress(
                f"Dropping first {self.skip_n_first_spec} objects in the catalogue"
            )
            self.catalogue = self.catalogue[self.skip_n_first_spec:]
        else:
            if self.skip_n_first_spec > 0:
                self.logger.progress(
                    f"Dropping first {self.skip_n_first_spec} objects in the catalogue\n"
                    f"Cutting at {self.max_num_spec} objects in the catalogue")
                self.catalogue = self.catalogue[self.skip_n_first_spec:self.
                                                skip_n_first_spec +
                                                self.max_num_spec]
            else:
                self.logger.progress(
                    f"Cutting at {self.max_num_spec} objects in the catalogue")
                self.catalogue = self.catalogue[:self.max_num_spec]
