"""This file contains class Rebin and several functions to do the rebinning."""


accepted_options = [
    "max wavelength", "min wavelength", "rebin", "step type", "step wavelength"]
required_options = [
    "max wavelength", "min wavelength", "step type", "step wavelength"]
defaults = {
    "rebin": True,
}

VALID_STEP_TYPES = ["lin", "log"]

class Rebin:
    """Class to rebin spectra

    Methods
    -------
    __init__
    __call__

    Attributes
    ----------
    common_wavelength_grid: array of float
    Common wavelength grid

    max_wavelength: float
    Maximum wavelength of the common wavelength grid

    min_wavelength: float
    Minimum wavelength of the common wavelength grid

    rebin: bool
    A boolean indicating whether rebin is necessary

    size_common_grid: int
    Number of pixels in the common wavelength grid

    step_type: string
    Step type in the common grid. "lin" means the common grid is equally spaced
    in wavelength. "log" means it is equally spaced in the logarithm of the
    wavelength
    """
    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        self.max_wavelength = None
        self.min_wavelength = None
        self.rebin = None
        self.size_common_grid = None
        self.step_type = None
        self.__parse_config(config)

        self.common_wavelength_grid = None
        self.find_common_wavelength_grid()

    def __call__(self, spectrum):
        """Rebin a spectrum

        Arguments
        ---------
        spectrum: Spectrum
        The spectrum to be rebinned

        Return
        ------
        spectrum: Spectrum
        The rebinned spetrum
        """
        if self.rebin:
            if self.step_type == "lin":
                rebinned_flux, rebinned_ivar = rebin(
                    spectrum.flux,
                    spectrum.ivar,
                    spectrum.wavelength,
                    common_wavelength_grid,
                )
            elif self.step_type == "log":
                rebinned_flux, rebinned_ivar = rebin(
                    spectrum.flux,
                    spectrum.ivar,
                    np.log10(spectrum.wavelength),
                    common_wavelength_grid,
                )

            spectrum.set_flux_ivar_common_grid(rebinned_flux, rebinned_ivar)

        else:
            spectrum.set_flux_ivar_common_grid(flux, ivar)

        return spectrum

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        RebinError upon missing required variables
        """
        self.max_wavelength = config.getfloat("max wavelength")
        if self.max_wavelength is None:
            raise RebinError(
                "Missing argument 'max wavelength' required by Rebin")

        self.min_wavelength = config.getfloat("min wavelength")
        if self.min_wavelength is None:
            raise RebinError(
                "Missing argument 'min wavelength' required by Rebin")

        self.rebin = config.getboolean("rebin")
        if self.rebin is None:
            raise RebinError(
                "Missing argument 'rebin' required by Rebin")

        self.step_type = config.get("step type")
        if step_type is None:
            raise RebinError(
                "Missing argument 'step type' required by Rebin")
        if self.step_type not in VALID_STEP_TYPES:
            raise RebinError(
                f"Error loading Rebin instance. 'step type' {self.read_mode} "
                " is not supported. Supported modes are " +
                " ".join(VALID_STEP_TYPES))

        step_wavelength = config.getfloat("step wavelength")
        if step_wavelength is None:
            raise RebinError(
                "Missing argument 'step wavelength' required by Rebin")
        if self.step_type == "lin":
            self.size_common_grid = (
                (self.max_wavelength - self.min_wavelength)/step_wavelength
                ).astype(np.int64)
            expected_max_wavelength = self.min_wavelength + self.size_common_grid*step_wavelength
        elif self.step_type == "log":
            self.size_common_grid = (
                (np.log10(self.max_wavelength) - np.log10(self.min_wavelength))/step_wavelength
                ).astype(np.int64)
            expected_max_wavelength = 10**(
                np.log10(self.min_wavelength) + self.size_common_grid*step_wavelength)
        if not np.isclose(expected_max_wavelength, self.max_wavelength):
            raise RebinError(
                f"Inconsistent values given for 'min wavelength' ({self.min_wavelength}), "
                f"'max wavelength' ({self.max_wavelength}) and "
                f"'step wavelength' ({step_wavelength}). Limiting wavelengths "
                "should be separated by N times the step with N being an integer. "
                f"Expected a maximum wavelength of {expected_max_wavelength}")

    def prepare_common_wavelength_grid(self):
        """Construct the common wavelength grid"""
        if step_type == "lin":
            self.common_wavelength_grid = np.linspace(
                self.min_wavelength,
                self.max_wavelength,
                self.size_common_grid
            )
            Spectrum.prepare_common_wavelength_grid(self.common_wavelength_grid)
        elif step_type == "log":
            self.common_wavelength_grid = np.linspace(
                np.log10(self.min_wavelength),
                np.log10(self.max_wavelength),
                self.size_common_grid
            )
            Spectrum.prepare_common_wavelength_grid(10**self.common_wavelength_grid)


@njit()
def find_bins(original_array, grid_array):
    """For each element in original_array, find the corresponding bin in grid_array

    This function assumes that wavelength grid that is evenly spaced on wavelength

    Arguments
    ---------
    original_array: array of float
    Read array

    grid_array: array of float
    Common array

    Return
    ------
    found_bin: array of int
    An array of size original_array.size filled with values smaller than
    grid_array.size with the bins correspondance
    """
    step = grid_array[1] - grid_array[0]
    found_bin = ((original_array - grid_array[0]) / step + 0.5).astype(np.int64)
    return found_bin

@njit
def rebin(flux, ivar, wavelength, common_wavelength_grid):
    """Rebin the arrays and update control variables
    Rebinned arrays are flux, ivar, lambda_ or log_lambda, and
    transmission_correction. Control variables are mean_snr

    Arguments
    ---------
    flux: array of float
    Flux

    ivar: array of float
    Inverse variance

    wavelength: array of float
    Wavelength (in Angstroms)

    common_wavelength_grid: array of float
    The common wavelength grid (in Angstroms)

    Return
    ------
    flux: array of float
    Rebinned version of input flux

    ivar: array of float
    Rebinned version of input ivar

    Raise
    -----
    AstronomicalObjectError if ivar only has zeros
    """
    rebin_flux = np.zeros(common_wavelength_grid.size)
    rebin_ivar = np.zeros(common_wavelength_grid.size)

    bins = find_bins(wavelength, common_wavelength_grid)
    max_bin = np.max(bins)
    binned_arr_size = bins.max() + 1

    # rebin flux, ivar and transmission_correction
    rebin_flux[:max_bin] = np.bincount(
        bins,
        weights=ivar * flux,
        minlength=binned_arr_size)
    rebin_ivar[:max_bin] = np.bincount(
        bins,
        weights=ivar,
        minlength=binned_arr_size)

    # normalize rebinned flux
    rebin_flux[rebin_ivar == 0.0] /= rebin_ivar[rebin_ivar == 0.0]


    return rebin_flux, rebin_ivar
