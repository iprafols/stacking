"""Class to store spectrum data"""

from stacking.errors import SpectrumError


class Spectrum:
    """Class to store spectrum data

    Methods
    -------
    __init__

    Class Attributes
    ----------------
    common_wavelength_grid: array
    Common wavelength grid to be used for stacking

    Attributes
    ----------
    ivar: array of float
    The inverse variance associated with the flux

    flux: array of float
    The flux array

    metadata: dict
    Metadata associated to the spectrum

    normalized_flux: array of float
    The normalized flux. Should be based on the common wavelength grid

    wavelength: array of float
    The wavelength array
    """
    common_wavelength_grid = None

    def __init__(self, specid, flux, ivar, wavelength):
        """Initialize class instance

        Arguments
        ---------
        specid: int
        Identifier for the spectrum

        flux: array of float
        The flux array

        ivar: array of float
        The inverse variance associated with the flux

        wavelength: array of float
        The wavelength array
        """
        self.flux = flux
        self.ivar = ivar
        self.wavelength = wavelength

        self.flux_common_grid = None
        self.ivar_common_grid = None
        self.normalized_flux = None

    def set_flux_ivar_common_grid(self, flux_common_grid, ivar_common_grid):
        """Add the rebinned flux and inverse variance"""
        if flux_common_grid.size != Spectrum.common_wavelength_grid.size:
            raise SpectrumError(
                "Normalized flux should be based on the common wavelength grid "
                f"but sizes differ. flux_common_grid.size = {flux_common_grid.size} "
                "Spectrum.common_wavelength_grid.size = "
                f"{Spectrum.common_wavelength_grid.size}")
        if ivar_common_grid.size != Spectrum.common_wavelength_grid.size:
            raise SpectrumError(
                "Normalized flux should be based on the common wavelength grid "
                f"but sizes differ. ivar_common_grid.size = {ivar_common_grid.size} "
                "Spectrum.common_wavelength_grid.size = "
                f"{Spectrum.common_wavelength_grid.size}")
        self.flux_common_grid = flux_common_grid
        self.ivar_common_grid = ivar_common_grid

    def set_normalized_flux(self, normalized_flux):
        """Set the normalized flux

        Arguments
        ---------
        normalized_flux: array of float
        The normalized flux. Should be
        """
        if normalized_flux.size != Spectrum.common_wavelength_grid.size:
            raise SpectrumError(
                "Normalized flux should be based on the common wavelength grid "
                f"but sizes differ. normalized_flux.size = {normalized_flux.size} "
                "Spectrum.common_wavelength_grid.size = "
                f"{Spectrum.common_wavelength_grid.size}")
        self.normalized_flux = normalized_flux
