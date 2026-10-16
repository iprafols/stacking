"""This module defines the class SblaInSimReader to read SBLA data"""
from concurrent.futures import ThreadPoolExecutor
import logging
import multiprocessing

from astropy.table import Table
import numpy as np
import fitsio

from stacking.errors import ReaderError
from stacking.reader import (Reader, defaults, accepted_options,
                             required_options)
from stacking.spectrum import Spectrum
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(
    accepted_options,
    {
        # option: description
        "sbla catalogue":
            "Filename of the SBLA catalogue. **Type: str**",
        "num processors":
            "Number of processors to use. **Type: int**",
        "vel sbla":
            ("Spectral velocity used for SBLA detection. **Type: float**"),
        "z min": (
            "Minimum redshift. SBLA with redshifts lower than z_min will be discarded. "
            "**Type: float**"),
        "z max": (
            "Maximum redshift. SBLA with redshifts higher than or equal to z_max will be "
            "discarded. **Type: float**"),
    })

defaults = update_default_options(defaults, {
    "num processors": 0,
    "z max": 10.0,
    "z min": 0.0,
})

required_options = update_required_options(required_options, [
    "sbla catalogue",
    "sbla vel",
])

SUPPORTED_READING_MODES = ["spplate", "spec"]


class SblaInSimReader(Reader):
    """Reads SBLA spectra formatted by code SBLA in sim (https://github.com/iprafols/SBLA_in_sim) 
    and formats its data as a list of Spectrum instances.

    Methods
    -------
    (see Reader in stacking/reader.py)
    __init__
    __parse_config
    read_data
    read_drq_catalogue
    read_from_spec
    read_from_spplate
    read_spall
    trim_catalogue

    Attributes
    ----------
    (see Reader in stacking/data.py)

    logger: logging.Logger
    Logger object

    num_processors: int
    Number of processors to use. If 0, the number of processors will be set 
    to half of the available processors in the system
    
    sbla_filename: str
    Filename of the SBLA catalogue

    sbla_vel: float
    Spectral velocity used for SBLA detection
    
    z_max: float
    Maximum redshift. Quasars with redshifts higher than or equal to
    z_max will be discarded

    z_min: float
    Minimum redshift. Quasars with redshifts lower than z_min will be
    discarded
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        ReaderError if the selected reading mode is not supported
        """
        self.logger = logging.getLogger(__name__)
        super().__init__(config)

        # load variables from config
        self.num_processors = None
        self.sbla_filename = None
        self.sbla_vel = None
        self.z_max = None
        self.z_min = None
        self.__parse_config(config)

        # data structure
        self.catalogue = None
        self.spectra = []

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        ReaderError upon missing required variables
        ReaderError if the reading mode is not supported
        """
        self.sbla_filename = config.get("sbla catalogue")
        if self.sbla_filename is None:
            raise ReaderError(
                "Missing argument 'sbla catalogue' required by SblaInSimReader")

        self.num_processors = config.getint("num processors")
        if self.num_processors is None:
            raise ReaderError(
                "Missing argument 'num processors' required by SblaInSimReader")
        if self.num_processors < 0:
            raise ReaderError(
                "Invalid value for 'num processors'. Expected a non-negative integer. "
                f"Found: {self.num_processors}")
        if self.num_processors == 0:
            self.num_processors = max(1, multiprocessing.cpu_count() // 2)

        self.vel_sbla = config.getfloat("vel sbla")
        if self.vel_sbla is None:
            raise ReaderError(
                "Missing argument 'vel sbla' required by SblaInSimReader")

        self.z_max = config.getfloat("z max")
        if self.z_max is None:
            raise ReaderError(
                "Missing argument 'z max' required by SblaInSimReader")

        self.z_min = config.getfloat("z min")
        if self.z_min is None:
            raise ReaderError(
                "Missing argument 'z min' required by SblaInSimReader")

    def read_data(self):
        """Read the data

        Return
        ------
        spectra: list of Spectrum
        The list of spectra
        """
        # load SBLA Catalogue
        self.catalogue = self.read_sbla_catalogue()

        # trim catalogue if necessary
        self.trim_catalogue()

        # read data
        self.read_spectra()

        if len(self.spectra) == 0:
            raise ReaderError(
                "No spectra were read, check the logs for more details")

        return self.spectra

    def read_sbla_catalogue(self):
        """Read the SBLA Catalogue

        Raise
        -----
        ReaderError when no valid column for redshift is found when reading
        the catalogue
        ReaderError when 'BI max' is passed but HDU does not contain BI_CIV
        field
        """
        self.logger.progress("Reading SBLA catalogue from %s",
                             self.sbla_filename)
        catalogue = Table.read(self.sbla_filename)

        keep_columns = ['NAME', 'GROUP', 'Z', "VEL_SBLA", "NOISE"]
        # Redshift
        if 'Z' not in catalogue.colnames:
            raise ReaderError(
                "Error in reading SBLA Catalogue. No valid column for "
                f"redshift found in {self.sbla_filename}")

        ## Sanity checks
        keep_rows = np.ones(len(catalogue), dtype=bool)
        self.logger.progress("start : nb object in cat = %d",
                             np.sum(keep_rows))

        keep_rows &= catalogue['Z'] >= self.z_min
        self.logger.progress("and z >= %.2f: nb object in cat = %d",
                             self.z_min, np.sum(keep_rows))
        keep_rows &= catalogue['Z'] < self.z_max
        self.logger.progress("and z < %.2f: nb object in cat = %d",
                             self.z_max, np.sum(keep_rows))

        keep_rows &= np.isclose(catalogue['VEL_SBLA'], self.vel_sbla)
        self.logger.progress(
            "and ve_sbla == %.0f: nb object in cat = %d",
            self.vel_sbla, np.sum(keep_rows))

        catalogue.keep_columns(keep_columns)
        catalogue = catalogue[keep_rows]

        return catalogue

    def read_spectra(self):
        """Read the spectra and formats its data as Spectrum instances"""
        self.logger.progress("Reading %d objects", len(self.catalogue))

        rows = list(self.catalogue)
        if len(rows) == 0:
            return

        max_workers = min(self.num_processors, len(rows))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            spectra = executor.map(self._read_single_spectrum, rows)
            self.spectra.extend(
                spectrum for spectrum in spectra if spectrum is not None)

    def _read_single_spectrum(self, row):
        """Read one spectrum row and return a Spectrum instance or None."""
        name = row["NAME"]
        group = row["GROUP"]
        has_noise = row["NOISE"]

        if has_noise:
            filename = (
                f"{self.input_directory}/{group//10:01d}/{group:02d}/{name}_spec.fits.gz"
            )
        else:
            filename = (
                f"{self.input_directory}/{group//10:01d}/{group:02d}/{name}_spec_nonoise.fits"
            )

        try:
            hdul = fitsio.FITS(filename)
        except IOError:
            self.logger.warning("Error reading %s. Ignoring file", filename)
            return None

        try:
            wavelength = np.array(hdul[1]["WAVELENGTH"][:], dtype=np.float64)
            flux = np.array(hdul[1]["FLUX"][:], dtype=np.float64)
            ivar = np.array(hdul[1]["IVAR"][:], dtype=np.float64)
        finally:
            hdul.close()

        self.logger.progress("Read %s", filename)
        return Spectrum(name, flux, ivar, wavelength, row["Z"])
