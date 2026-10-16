#!/usr/bin/env python

"""Compatibility shim for setuptools builds.

All package metadata lives in ``pyproject.toml``.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
