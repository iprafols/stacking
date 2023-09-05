"""This module defines the class Dr16Reader to read SDSS data"""
import os
import glob
import logging
import time

import numpy as np
import fitsio
from astropy.table import Table, join

from stacking.errors import ReaderError
from stacking.reader import (Reader, defaults, accepted_options,
                             required_options)
from stacking.spectrum import Spectrum
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options, [
    "best obs", "drq catalogue", "keep BAL", "max Balnicity Index", "read mode",
    "spAll", "z min", "z max"
])

defaults = update_default_options(
    defaults, {
        "best obs": False,
        "keep BAL": False,
        "read mode": "spplate",
        "z max": 10.0,
        "z min": 0.0,
    })

required_options = update_required_options(required_options, [
    "drq catalogue",
])

SUPPORTED_READING_MODES = ["spplate", "spec"]


class Dr16Reader(Reader):
    """Reads the spectra from SDSS DR16 and formats its data as a list of
    Spectrum instances.

    Methods
    -------
    (see Reader in stacking/reader.py)
    __init__
    __parse_config
    read_from_spec
    read_from_spplate

    Attributes
    ----------
    (see Reader in stacking/data.py)

    best_obs: bool
    If True, reads only the best observation for quasars with repeated
    observations

    max_balnicity_index: float or None
    Maximum value allowed for the Balnicity Index to keep the quasar.
    None for no maximum

    drq_filename: str
    Filename of the DRQ catalogue

    keep_bal: bool
    If False, remove the quasars flagged as having a Broad Absorption
    Line. Ignored if max_balnicity_index is not None

    logger: logging.Logger
    Logger object

    read_mode: str
    Reading mode. Currently supported reading modes are "spplate" and "spec"

    spall: str
    Path to the spAll file required for multiple observations

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
        self.best_obs = None
        self.drq_filename = None
        self.keep_bal = None
        self.max_balnicity_index = None
        self.read_mode = None
        self.spall = None
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
        self.best_obs = config.getboolean("best obs")
        if self.best_obs is None:
            raise ReaderError(
                "Missing argument 'best obs' required by Dr16Reader")

        self.max_balnicity_index = config.getfloat("max Balnicity Index")

        self.drq_filename = config.get("drq catalogue")
        if self.drq_filename is None:
            raise ReaderError(
                "Missing argument 'drq catalogue' required by Dr16Reader")

        self.keep_bal = config.getboolean("keep BAL")
        if self.keep_bal is None:
            raise ReaderError(
                "Missing argument 'keep BAL' required by Dr16Reader")

        self.read_mode = config.get("read mode")
        if self.read_mode is None:
            raise ReaderError(
                "Missing argument 'read mode' required by Dr16Reader")
        if self.read_mode not in SUPPORTED_READING_MODES:
            raise ReaderError(
                f"Error reading data in Dr16Reader. Read mode {self.read_mode} is not "
                "supported. Supported reading modes are " +
                " ".join(SUPPORTED_READING_MODES))

        if self.best_obs:
            self.spall = None
        else:
            self.spall = config.get("spAll")
            if self.spall is None:
                self.logger.warning(
                    "Missing argument 'spAll' required by Dr16Reader. Looking "
                    "for spAll in input directory...")

                # this should never occur as the existence of the input directory
                # is checked in the class parent (Reader)
                # this is left here to avoid unexpected behaviour in case that
                # class changes
                if config.get("input directory") is None:  # pragma: no cover
                    self.logger.error(
                        "'spAll' file not found. If you didn't want to load the "
                        "spAll file you should pass the option 'best obs = True'. "
                        "Quiting...")
                    raise ReaderError(
                        "Missing argument 'spAll' required by Dr16Reader")
                folder = config.get("input directory")
                folder = folder.replace("spectra",
                                        "").replace("lite",
                                                    "").replace("full", "")
                filenames = glob.glob(f"{folder}/spAll-*.fits")
                if len(filenames) > 1:
                    self.logger.error(
                        "Found multiple 'spAll' files. Quiting...")
                    for filename in filenames:
                        self.logger.error("found: %s", filename)
                    raise ReaderError(
                        "Missing argument 'spAll' required by Dr16Reader")
                if len(filenames) == 0:
                    self.logger.error(
                        "'spAll' file not found. If you didn't want to load the "
                        "spAll file you should pass the option 'best obs = True'. "
                        "Quiting...")
                    raise ReaderError(
                        "Missing argument 'spAll' required by Dr16Reader")
                self.spall = filenames[0]
                self.logger.ok_warning(
                    "'spAll' file found. Contining with normal execution")

        self.z_max = config.getfloat("z max")
        if self.z_max is None:
            raise ReaderError("Missing argument 'z max' required by Dr16Reader")

        self.z_min = config.getfloat("z min")
        if self.z_min is None:
            raise ReaderError("Missing argument 'z min' required by Dr16Reader")

    def read_data(self):
        """Read the data

        Return
        ------
        spectra: list of Spectrum
        The list of spectra
        """
        # load DRQ Catalogue
        self.catalogue = self.read_drq_catalogue()
        # if using multiple observations load the information from spAll file
        if not self.best_obs:
            self.read_spall()

        # read data
        # TODO: parallelize this
        if self.read_mode == "spplate":
            self.read_from_spplate()
        elif self.read_mode == "spec":
            self.read_from_spec()
        # this should never enter unless new reading modes are not properly added
        else:  # pragma: no cover
            raise ReaderError(
                f"Don't know what to do with reading mode {self.read_mode}. "
                "This is one of the supported reading modes, but maybe it "
                "was not properly coded. If you did the change yourself, check "
                "that you added the behaviour of the new mode to method `read_data`. "
                "Otherwise contact 'stacking' developpers.")

        if len(self.spectra) == 0:
            raise ReaderError(
                "No spectra were read, check the logs for more details")

        return self.spectra

    def read_drq_catalogue(self):
        """Read the DRQ Catalogue

        Raise
        -----
        ReaderError when no valid column for redshift is found when reading
        the catalogue
        ReaderError when 'BI max' is passed but HDU does not contain BI_CIV
        field
        """
        self.logger.progress("Reading DRQ catalogue from %s", self.drq_filename)
        catalogue = Table.read(self.drq_filename, hdu="CATALOG")

        keep_columns = ['Z', 'THING_ID', 'PLATE', 'MJD', 'FIBERID']
        # Redshift
        if 'Z' not in catalogue.colnames:
            if 'Z_VI' in catalogue.colnames:
                catalogue.rename_column('Z_VI', 'Z')
                self.logger.progress(
                    "Z not found (new DRQ >= DRQ14 style), using Z_VI (DRQ <= DRQ12)"
                )
            else:
                raise ReaderError(
                    "Error in reading DRQ Catalogue. No valid column for "
                    f"redshift found in {self.drq_filename}")

        ## Sanity checks
        keep_rows = np.ones(len(catalogue), dtype=bool)
        self.logger.progress("start                 : nb object in cat = %d",
                             np.sum(keep_rows))
        keep_rows &= catalogue["THING_ID"] > 0
        self.logger.progress("and THING_ID > 0      : nb object in cat = %d",
                             np.sum(keep_rows))
        keep_rows &= catalogue['RA'] != catalogue['DEC']
        self.logger.progress("and ra != dec         : nb object in cat = %d",
                             np.sum(keep_rows))
        keep_rows &= catalogue['RA'] != 0.
        self.logger.progress("and ra != 0.          : nb object in cat = %d",
                             np.sum(keep_rows))
        keep_rows &= catalogue['DEC'] != 0.
        self.logger.progress("and dec != 0.         : nb object in cat = %d",
                             np.sum(keep_rows))

        ## Redshift range
        keep_rows &= catalogue['Z'] >= self.z_min
        self.logger.progress("and z >= %.2f        : nb object in cat = %d",
                             self.z_min, np.sum(keep_rows))
        keep_rows &= catalogue['Z'] < self.z_max
        self.logger.progress("and z < %.2f         : nb object in cat = %d",
                             self.z_min, np.sum(keep_rows))

        ## BAL visual
        if not self.keep_bal and self.max_balnicity_index is None:
            if 'BAL_FLAG_VI' in catalogue.colnames:
                keep_rows &= catalogue['BAL_FLAG_VI'] == 0
                self.logger.progress(
                    "and BAL_FLAG_VI == 0  : nb object in cat = %d",
                    np.sum(keep_rows))
                keep_columns += ['BAL_FLAG_VI']
            else:
                self.logger.warning("BAL_FLAG_VI not found in %s",
                                    self.drq_filename)
                self.logger.ok_warning("Ignoring")

        ## BAL CIV
        if self.max_balnicity_index is not None:
            if 'BI_CIV' in catalogue.colnames:
                balnicity_index = catalogue['BI_CIV']
                keep_rows &= balnicity_index <= self.max_balnicity_index
                self.logger.progress(
                    "and BI_CIV <= %.2f  : nb object in cat = %d",
                    self.max_balnicity_index, np.sum(keep_rows))
                keep_columns += ['BI_CIV']
            else:
                raise ReaderError(
                    "Error in reading DRQ Catalogue. 'BI max' was passed but "
                    "field BI_CIV was not present in the HDU")

        catalogue.keep_columns(keep_columns)
        # Inhterited this from picca, but not sure we actually need it so I'm
        # commenting it for now
        #keep_rows = np.where(keep_rows)[0]
        catalogue = catalogue[keep_rows]

        return catalogue

    def read_from_spec(self):
        """Read the spectra and formats its data as Spectrum instances"""
        self.logger.progress("Reading %d objects", len(self.catalogue))

        for row in self.catalogue:
            thingid = row["THING_ID"]
            plate = row["PLATE"]
            mjd = row["MJD"]
            fiberid = row["FIBERID"]

            filename = (f"{self.input_directory}/{plate}/spec-{plate}-{mjd}-"
                        f"{fiberid:04d}.fits")
            try:
                hdul = fitsio.FITS(filename)
            except IOError:
                self.logger.warning("Error reading %s. Ignoring file", filename)
                continue
            self.logger.progress("Read %s", filename)

            wavelength = 10**np.array(hdul[1]["loglam"][:], dtype=np.float64)
            flux = np.array(hdul[1]["flux"][:], dtype=np.float64)
            ivar = (np.array(hdul[1]["ivar"][:], dtype=np.float64) *
                    hdul[1]["and_mask"][:] == 0)

            self.spectra.append(Spectrum(thingid, flux, ivar, wavelength))

    def read_from_spplate(self):
        """Read the spectra and formats its data as Spectrum instances."""
        grouped_catalogue = self.catalogue.group_by(["PLATE", "MJD"])
        num_objects = self.catalogue["THING_ID"].size
        self.logger.progress("reading %d plates", len(grouped_catalogue.groups))

        num_read_total = 0
        for (plate, mjd), group in zip(grouped_catalogue.groups.keys,
                                       grouped_catalogue.groups):
            spplate = f"{self.input_directory}/{plate}/spPlate-{plate:04d}-{mjd}.fits"
            try:
                hdul = fitsio.FITS(spplate)
                header = hdul[0].read_header()
            except IOError:
                self.logger.warning("Error reading %s. Ignoring file", spplate)
                continue

            start_time = time.time()

            coeff0 = header["COEFF0"]
            coeff1 = header["COEFF1"]

            flux = hdul[0].read()
            ivar = hdul[1].read() * (hdul[2].read() == 0)
            log_lambda = coeff0 + coeff1 * np.arange(flux.shape[1])
            wavelength = 10**log_lambda

            # Loop over all objects inside this spPlate file
            # and create the SdssForest objects
            for row in group:
                thingid = row["THING_ID"]
                fiberid = row["FIBERID"]
                array_index = fiberid - 1
                self.spectra.append(
                    Spectrum(
                        thingid,
                        flux[array_index],
                        ivar[array_index],
                        wavelength,
                    ))

                self.logger.debug("%d read from file %s and fiberid %d",
                                  thingid, spplate, fiberid)

            num_read = len(group)
            num_read_total += num_read
            if num_read > 0.0:
                time_read = (time.time() - start_time) / num_read
            else:
                time_read = np.nan
            self.logger.progress(
                "read %d from %s in %.3f seconds per spec. Progress: %d of %d",
                num_read, os.path.basename(spplate), time_read, num_read_total,
                num_objects)
            hdul.close()

    def read_spall(self):
        """Read the spAll file and update the catalogue

        Raise
        -----
        ReaderError if spAll file is not found
        """
        self.logger.progress("reading spAll from %s", self.spall)
        try:
            catalogue = Table.read(self.spall, hdu=1)
            catalogue.keep_columns([
                "THING_ID", "PLATE", "MJD", "FIBERID", "PLATEQUALITY",
                "ZWARNING"
            ])
        except IOError as error:
            raise ReaderError("Error in reading spAll catalogue. Error "
                              f"reading file {self.spall}. IOError "
                              f"message: {str(error)}") from error

        keep_rows = np.in1d(catalogue["THING_ID"], self.catalogue["THING_ID"])
        self.logger.progress("Found %d spectra with required THING_ID",
                             np.sum(keep_rows))
        keep_rows &= catalogue["PLATEQUALITY"] == "good"
        self.logger.progress("Found %d spectra with 'good' plate",
                             np.sum(keep_rows))
        ## Removing spectra with the following ZWARNING bits set:
        ## SKY, LITTLE_COVERAGE, UNPLUGGED, BAD_TARGET, NODATA
        ## https://www.sdss.org/dr14/algorithms/bitmasks/#ZWARNING
        bad_z_warn_bit = {
            0: 'SKY',
            1: 'LITTLE_COVERAGE',
            7: 'UNPLUGGED',
            8: 'BAD_TARGET',
            9: 'NODATA'
        }
        for z_warn_bit, z_warn_bit_name in bad_z_warn_bit.items():
            warning_bit = catalogue["ZWARNING"] & 2**z_warn_bit == 0
            keep_rows &= warning_bit
            self.logger.progress("Found %d spectra without %d bit set: %s",
                                 np.sum(keep_rows), z_warn_bit, z_warn_bit_name)
        self.logger.progress("# unique objs: %s", len(self.catalogue))
        self.logger.progress("# spectra: %d", keep_rows.sum())
        catalogue = catalogue[keep_rows]

        # merge redshift information from DRQ catalogue
        # columns are discarded on DRQ catalogues to
        # avoid conflicts with PLATE, FIBERID, MJD when assigning
        # DRQ properies and on spAll catalogue to avoid
        # conflicts with the update of self.catalogue
        select_cols = [
            name for name in catalogue.colnames
            if name not in ["PLATEQUALITY", "ZWARNING"]
        ]
        select_cols_drq = [
            name for name in self.catalogue.colnames
            if name not in ["PLATE", "FIBERID", "MJD"]
        ]
        self.catalogue = join(catalogue[select_cols],
                              self.catalogue[select_cols_drq],
                              join_type="left")
