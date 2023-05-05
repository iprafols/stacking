"""Class to store spectrum data"""


class Spectrum:
    """Class to store spectrum data

    Methods
    -------
    __init__

    Attributes
    ----------
    ivar: array of float
    The inverse variance associated with the flux

    flux: array of float
    The flux array

    normalized_flux: array of float
    The normalized flux

    wavelength: array of float
    The wavelength array
    """

    def __init__(self, flux, ivar, wavelength):
        """Initialize class instance"""
        self.flux = flux
        self.ivar = ivar
        self.wavelength = wavelength

        self.normalized_flux = None

    def set_normalized_flux(self, normalized_flux):
        """Set the normalized flux

        Arguments
        ---------
        normalized_flux: array of float
        The normalized flux
        """
        self.normalized_flux = normalized_flux
