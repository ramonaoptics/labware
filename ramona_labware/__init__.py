import importlib.resources

from .schema import AlignmentReference, Labware, OuterDimensions, WellDimensions

__version__ = '0.1.0'

__all__ = [
    'AlignmentReference',
    'Labware',
    'OuterDimensions',
    'WellDimensions',
    'load_labware',
]


def load_labware():
    """Return every labware definition, keyed by its file name without ``.json``."""
    definitions = {}
    for entry in (importlib.resources.files(__name__) / 'definitions').iterdir():
        if entry.name.endswith('.json'):
            definitions[entry.name.removesuffix('.json')] = Labware.model_validate_json_file(entry)
    return definitions
