import importlib.metadata
import importlib.resources

from .schema import AlignmentReference, Labware, OuterDimensions, WellDimensions

# The version comes from the git tag, through setuptools-scm, at build time.
try:
    __version__ = importlib.metadata.version('labware')
except importlib.metadata.PackageNotFoundError:
    __version__ = '0+unknown'

__all__ = [
    'AlignmentReference',
    'Labware',
    'OuterDimensions',
    'WellDimensions',
    'load_labware',
]


def load_labware() -> dict[str, Labware]:
    """Return every labware definition, keyed by its file name without ``.json``."""
    definitions = {}
    for entry in (importlib.resources.files(__name__) / 'definitions').iterdir():
        if entry.name.endswith('.json'):
            definitions[entry.name.removesuffix('.json')] = (
                Labware.model_validate_json_file(entry)
            )
    return definitions
