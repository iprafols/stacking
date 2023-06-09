""" This file contains the interface to use the package"""
import logging
import multiprocessing
import time

from stacking.config import Config
from stacking.errors import StackingError
from stacking.rebin import Rebin
from stacking.spectrum import Spectrum


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
    """

    def __init__(self):
        """Initialize class instance"""
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.num_processors = None
        self.spectra = None

    def load_config(self, config_file):
        """Load the configuration of the run, sets up the print function
        that will be used to print, and initializes the saving folders

        Arguments
        ---------
        config_file: str
        Name of the file specifying the configuration
        """
        # load configuration
        self.config = Config(config_file)
        self.num_processors = self.config.num_processors

    def normalize_spectra(self):
        """ Normalize spectra """
        start_time = time.time()
        self.logger.info("Starting normallization procedure")

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
                normalizer.normalize(spectrum) for spectrum in self.spectra
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
        start_time = time.time()
        self.logger.info("Reading data")

        reader_type, reader_arguments = self.config.reader
        reader = reader_type(reader_arguments)
        self.spectra = reader.read()

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
        start_time = time.time()

        # initialize rebinnes (also sets common grid)
        rebin = Rebin(self.config.rebin_args)

        # do the actual rebinning
        if self.num_processors > 1:
            context = multiprocessing.get_context('fork')
            # Pick a large chunk size such that rebin is copied as few times
            # as possible
            chunksize = int(len(self.spectra) / self.num_processors / 3)
            chunksize = max(1, chunksize)
            with context.Pool(processes=self.num_processors) as pool:
                self.spectra = list(
                    pool.map(rebin, self.spectra, chunksize=chunksize))
        else:
            self.spectra = [rebin(spectrum) for spectrum in self.spectra]

        end_time = time.time()
        self.logger.info("Time spent rebinning data: %f seconds",
                         end_time - start_time)

    def stack_spectra(self):
        """ Stack spectra """
        start_time = time.time()
        self.logger.info("Stacking data")

        stacker_type, stacker_arguments = self.config.stacker
        stacker = stacker_type(stacker_arguments)
        stacker.stak()

        end_time = time.time()
        self.logger.info("Time spent stacking data: %f seconds",
                         end_time - start_time)

    def write_results(self):
        """ Write results to disc"""
        start_time = time.time()
        self.logger.info("Writing results")

        writer_type, writer_arguments = self.config.writer
        writer = writer_type(writer_arguments)
        writer.write_results()

        end_time = time.time()
        self.logger.info("Time spent writing results: %f seconds",
                         end_time - start_time)
