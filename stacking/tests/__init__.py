"""Initialize python package"""
import logging
import os
import unittest

logging.getLogger(__name__).addHandler(logging.NullHandler())


def test_suite():
    """
        Returns unittest.TestSuite of picca tests for use by setup.py
    """

    thisdir = os.path.dirname(__file__)
    return unittest.defaultTestLoader.discover(thisdir, top_level_dir=thisdir)
