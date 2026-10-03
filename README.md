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

Uploads to PyPI are automatic. Bump `__version__` in `labware/__init__.py`,
merge that to `main`, then tag the commit and push the tag:

```bash
git tag v0.1.1
git push origin v0.1.1
```

The `pypi` workflow builds the sdist and wheel, checks that the tag matches
`__version__`, and publishes them.
