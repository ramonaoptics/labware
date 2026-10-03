# labware

Microplate and dish definitions for software: outer footprint, well geometry,
skirt, material, and the vendor drawing each dimension came from.

Browse them in 3D: https://docs.ramonaoptics.com/tools/labware_viewer.html

## Example

```python
from labware import load_labware

plates = load_labware()
plate = plates["SBS_96_well_plate"]

print(plate.name)  # SBS 96 well
print(plate.well_dimensions.rows, plate.well_dimensions.columns)  # 8 12
print(plate.well_dimensions.pitch)  # 0.009, in meters
```

## Layout

- `labware/definitions/` holds one JSON file per part. The file name, without
  `.json`, is the key `load_labware()` returns it under.
- `labware/schema.py` is the pydantic model every definition is validated
  against.
- `labware/labware.v1.schema.json` is that model published as a JSON schema.
  Each definition names it in its `$schema` key.

## Releasing

Uploads to PyPI are automatic, and the version comes from the git tag, so
there is no version number to edit in the source.

To release, create the tag from the GitHub web interface:

1. Open https://github.com/ramonaoptics/labware/releases/new
2. Under "Choose a tag", type the new version with a leading `v`, for example
   `v0.1.1`, and pick "Create new tag on publish".
3. Leave the target as `main`, click "Generate release notes", then
   "Publish release".

The `pypi` workflow then builds the sdist and wheel and publishes them, and
`labware.__version__` in the installed package reports that same version.
