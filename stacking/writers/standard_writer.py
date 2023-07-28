""" This module defines the class StandardWriter to write the stack results"""

from stacking.writer import Writer


class StandardWriter(Writer):
    """Class to write the satck results

    Methods
    -------
    (see Writer in stacking/writer.py)

    Attributes
    ----------
    (see Writer in stacking/writer.py)

    logger: logging.Logger
    Logger object

    stacked_flux: array of float
    The stacked flux

    stacked_weight: array of float
    The sum of weights associated with each flux

    """
