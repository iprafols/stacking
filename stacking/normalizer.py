""" Basic structure for normalizers """

from stacking.errors import NormalizerError

accepted_options = []
required_options = []
defaults = {}


class Normalizer:
    """Abstract class to define the normalizer skeleton

    Methods
    -------
    compute_normalisation_factors
    normalize_spectrum
    """

    def compute_norm_factors(self, spectra):
        """ Compute normalization factors

        Arguments
        ---------
        spectra: list of Spectrum
        The list of spectra

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        raise NormalizerError(
            "Method 'normalize_spectrum' was not overloaded by child class")

    def normalize_spectrum(self, spectrum):
        """ Normalize a spectrum

        Arguments
        ---------
        spectrum: Spectrum
        A spectrum to normalize

        Return
        ------
        spectrum: Spectrum
        The normalized spectrum

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        raise NormalizerError(
            "Method 'normalize_spectrum' was not overloaded by child class")

    def save_norm_factors(self):
        """ Save the normalization factors
        Default behaviour is not saving and should be overloaded by the
        child classes if saving is desired
        """
        return
