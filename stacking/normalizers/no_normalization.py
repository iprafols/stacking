""" This module define the class NoNormalization to circunvent the normalization
procedure """

from stacking.normalizer import (  # pylint: disable=unused-import
    Normalizer, defaults, accepted_options, required_options)


class NoNormalization(Normalizer):
    """This class is set to circunvent the normalization procedure

    Methods
    -------
    __init__
    compute_normalisation_factors
    normalize_spectrum
    """
    def __init__(self, config):
        """ Initialize instance """
        return

    def compute_norm_factors(self, spectra):
        """ We are not normalizing so we don't need to do anything here

        Arguments
        ---------
        spectra: list of Spectrum
        The list of spectra
        """
        return

    def normalize_spectrum(self, spectrum):
        """ Set the flux as normalized flux

        Arguments
        ---------
        spectrum: Spectrum
        A spectrum to normalize

        Return
        ------
        spectrum: Spectrum
        The normalized spectrum
        """
        spectrum.set_normalized_flux(flux_common_grid)
        return spectrum
