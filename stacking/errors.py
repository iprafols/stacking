"""This module define the different Error types related to the
package stacking
"""
import logging

class StackingError(Exception):
    """
        General exceptions ocurred in the package Stacking
    """
    def __init__(self, message):
        self.logger = logging.getLogger(__name__)
        self.logger.error(message)
        super().__init__(message)

class ConfigError(StackingError):
    """
        Exceptions occurred in class Config
    """


class NormalizerError(StackingError):
    """
        Exceptions occurred in class Normalizer or its childs
    """


class ReaderError(StackingError):
    """
        Exceptions occurred in class Reader or its childs
    """


class RebinError(StackingError):
    """
        Exceptions occurred in class Rebin
    """


class SpectrumError(StackingError):
    """
        Exceptions occurred in class Spectrum
    """


class StackerError(StackingError):
    """
        Exceptions occurred in class Stacker or its childs
    """


class WriterError(StackingError):
    """
        Exceptions occurred in class Writer or its childs
    """


if __name__ == '__main__':
    pass
