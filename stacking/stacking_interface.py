""" This file contains the interface to use the package"""
import logging
import multiprocessing
import time

from stacking.config import Config
from stacking.errors import StackingError
from stacking.rebin import Rebin
from stacking.spectrum import Spectrum

ACCEPTED_RUN_TYPES = ["normal", "merge norm factors", "merge stack"]


class StackingInterface:
    """Interface for the stacking Package

    Methods
    -------
    __init__
    load_config
    read_data

    Attributes
    ----------
    config: Config
    A Config instance

    logger: logging.Logger
    Logger object

    num_processors: int
    Number of processors to use in parallelization

    spectra: list of Spectrum
    List of spectra to stack

    stacker: Stacker
    Stacker object

    rebin: Rebin
    Rebin object
    """

    def __init__(self):
        """Initialize class instance"""
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.num_processors = None
        self.spectra = None
        self.stacker = None
        self.rebin = None

        # setup flags
        self.normalize_spectra_flag = None
        self.read_data_flag = None
        self.rebin_data_flag = None
        self.stack_spectra_flag = None
        self.write_results_flag = None

    def load_config(self, config_file):
        """Load the configuration of the run, sets up the print function
        that will be used to print, initializes the saving folders and the
        rebin instance

        Arguments
        ---------
        config_file: str
        Name of the file specifying the configuration
        """
        # load configuration
        self.config = Config(config_file)
        self.num_processors = self.config.num_processors

        # load run setup
        self.setup_run()

        # initialize rebin (also sets common grid)
        # done here to detect early errors
        self.rebin = Rebin(self.config.rebin_args)

    def normalize_spectra(self):
        """ Normalize spectra """
        if self.normalize_spectra_flag:
            start_time = time.time()
            self.logger.info("Starting normalization procedure")

            normalizer_type, normalizer_arguments = self.config.normalizer
            normalizer = normalizer_type(normalizer_arguments)

            # compute normalization factors
            start_time_step = time.time()
            self.logger.progress("Computing normalization factors")
            normalizer.compute_norm_factors(self.spectra)
            end_time_step = time.time()
            self.logger.progress(
                "Time spent computing normalisation factors: %f seconds",
                end_time_step - start_time_step)

            # save normalisation factor
            start_time_step = time.time()
            self.logger.progress("Saving normalization factors")
            normalizer.save_norm_factors()
            end_time_step = time.time()
            self.logger.progress(
                "Time spent saving normalisation factors: %f seconds",
                end_time_step - start_time_step)

            # normalize spectra
            start_time_step = time.time()
            self.logger.progress("Normalizing")
            if self.num_processors > 1:
                context = multiprocessing.get_context('fork')
                with context.Pool(processes=self.num_processors) as pool:
                    self.spectra = pool.map(normalizer.normalize, self.spectra)
            else:
                self.spectra = [
                    normalizer.normalize_spectrum(spectrum)
                    for spectrum in self.spectra
                ]
            end_time_step = time.time()
            self.logger.progress("Time spent normalizing: %f seconds",
                                 end_time_step - start_time_step)

            end_time = time.time()
            self.logger.info(
                "Time spent in the normalization procedure: %f seconds",
                end_time - start_time)

    def read_data(self):
        """Load spectra to stack. Use the reader specified in the configuration"""
        if self.read_data_flag:
            start_time = time.time()
            self.logger.info("Reading data")

            reader_type, reader_arguments = self.config.reader
            reader = reader_type(reader_arguments)
            self.spectra = reader.read_data()

            # we should never enter this block unless ReaderType is not correctly
            # writen
            if not all((isinstance(spectrum, Spectrum)
                        for spectrum in self.spectra)):  # pragma: no cover
                raise StackingError(
                    "Error reading data.\n At least one of the elements in variable "
                    "'spectra' is not of class Spectrum. This can happen if the "
                    "Reader object responsible for reading the data did not define "
                    "the correct data type. Please check for correct inheritance "
                    "pattern.")

            end_time = time.time()
            self.logger.info("Time spent reading data: %f seconds",
                             end_time - start_time)

    def rebin_data(self):
        """Rebin data to a common grid"""
        if self.rebin_data_flag:
            start_time = time.time()

            self.logger.info("Rebinning data")

            # do the actual rebinning
            if self.num_processors > 1:
                context = multiprocessing.get_context('fork')
                # Pick a large chunk size such that rebin is copied as few times
                # as possible
                chunksize = int(len(self.spectra) / self.num_processors / 3)
                chunksize = max(1, chunksize)
                with context.Pool(processes=self.num_processors) as pool:
                    self.spectra = list(
                        pool.map(self.rebin, self.spectra, chunksize=chunksize))
            else:
                self.spectra = [
                    self.rebin(spectrum) for spectrum in self.spectra
                ]

            end_time = time.time()
            self.logger.info("Time spent rebinning data: %f seconds",
                             end_time - start_time)

    def setup_run(self):
        """Setup the current run"""
        if self.config.run_type not in ACCEPTED_RUN_TYPES:
            raise StackingError("Unrecognised run type. Expeced one of " +
                                " ".join(ACCEPTED_RUN_TYPES) +
                                f"Found {self.config.run_type}")
        # normal run
        if self.config.run_type == "normal":
            self.normalize_spectra_flag = True
            self.read_data_flag = True
            self.rebin_data_flag = True
            self.stack_spectra_flag = True
            self.write_results_flag = True
        # merge normalization factors from partial runs
        elif self.config.run_type == "merge norm factors":
            self.normalize_spectra_flag = True
            self.read_data_flag = False
            self.rebin_data_flag = False
            self.stack_spectra_flag = False
            self.write_results_flag = False
        # merge stack from partial runs
        # not using else in case we add more modes in the future
        elif self.config.run_type == "merge stack":  # pragma: no cover
            self.normalize_spectra_flag = False
            self.read_data_flag = False
            self.rebin_data_flag = False
            self.stack_spectra_flag = True
            self.write_results_flag = True

    def stack_spectra(self):
        """ Stack spectra """
        if self.stack_spectra_flag:
            start_time = time.time()
            self.logger.info("Stacking data")

            stacker_type, stacker_arguments = self.config.stacker
            self.stacker = stacker_type(stacker_arguments)
            self.stacker.stack(self.spectra)

            end_time = time.time()
            self.logger.info("Time spent stacking data: %f seconds",
                             end_time - start_time)

    def write_results(self):
        """ Write results to disc"""
        if self.write_results_flag:
            start_time = time.time()
            self.logger.info("Writing results")

            writer_type, writer_arguments = self.config.writer
            writer = writer_type(writer_arguments)
            writer.write_results(self.stacker)

            end_time = time.time()
            self.logger.info("Time spent writing results: %f seconds",
                             end_time - start_time)
