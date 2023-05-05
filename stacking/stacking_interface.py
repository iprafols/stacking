""" This file contains the interface to use the package"""
import logging
import multiprocessing
import time

from stacking.config import Config
from stacking.errors import StackingError
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

    num_processors: int
    Number of processors to use in parallelization
    """

    def __init__(self):
        """Initialize class instance"""
        self.logger = logging.getLogger('picca.delta_extraction.survey.Survey')
        self.config = None
        self.num_processors = None
        self.spectra = None
        self.stacker = None

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
        self.logger.info("Normalizing spectra")

        normalizer_type, normalizer_arguments = self.config.normalizer
        normalizer = normalizer_type(normalizer_arguments)

        # compute normalization factors
        normalizer.compute_normalisation_factors()

        # normalize spectra
        if self.num_processors > 1:
            context = multiprocessing.get_context('fork')
            with context.Pool(processes=self.num_processors) as pool:
                self.spectra = pool.map(normalizer.normalize, self.spectra)
        else:
            self.spectra = [
                normalizer.normalize(spectrum) for spectrum in self.spectra
            ]

        end_time = time.time()
        self.logger.info("Time spent normalizing spectra: %f seconds",
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

    def stack_spectra(self):
        """ Stack spectra """
        start_time = time.time()
        self.logger.info("Stacking data")

        stacker_type, stacker_arguments = self.config.stacker
        self.stacker = stacker_type(stacker_arguments)
        self.stacker.stak()

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
