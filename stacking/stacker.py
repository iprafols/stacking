""" Basic structure for stackers """

from stacking.errors import StackerError

required_options = []


class Stacker:
    """Abstract class to define the normalizer skeleton

    Methods
    -------
    __init__
    stack

    Attributes
    ----------
    stack_result: spectrum or list of Spectrum
    The resulting stack
    """

    def __init__(self):
        """ Initialize class instance """
        self.stack_result = None

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        raise StackerError("Method 'stack' was not overloaded by child class")
