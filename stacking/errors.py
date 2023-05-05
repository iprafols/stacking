"""This module define the different Error types related to the
package stacking
"""


class ConfigError(Exception):
    """
        Exceptions occurred in class Config
    """


class NormalizerError(Exception):
    """
        Exceptions occurred in class Normalizer or its childs
    """


class ReaderError(Exception):
    """
        Exceptions occurred in class Reader or its childs
    """


class SpectrumError(Exception):
    """
        Exceptions occurred in class Spectrum
    """


class StackerError(Exception):
    """
        Exceptions occurred in class Stacker or its childs
    """


class StackingError(Exception):
    """
        General exceptions ocurred in the package Stacking
    """


class WriterError(Exception):
    """
        Exceptions occurred in class Writer or its childs
    """


if __name__ == '__main__':
    pass
