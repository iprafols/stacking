""" Basic structure for normalizers """

from stacking.errors import NormalizerError


class Normalizer:
    """Abstract class to define the normalizer skeleton

    Methods
    -------
    compute_normalisation_factors
    normalize_spectrum
    """

    def compute_normalisation_factors(self):
        """ Compute normalization factors

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
