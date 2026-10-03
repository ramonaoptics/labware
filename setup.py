from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from setuptools import setup

# Loads _version.py module without importing the whole package.
spec = spec_from_file_location('version', Path('labware') / '_version.py')
module = module_from_spec(spec)
spec.loader.exec_module(module)

setup(version=module.__version__, cmdclass=module.get_cmdclass('labware'))
