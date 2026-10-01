# ramona-labware

Microplate and dish definitions used by Ramona Optics MCAM software: outer
footprint, well geometry, skirt, material, and the vendor drawing each
dimension came from. One JSON file per part in `ramona_labware/definitions/`,
validated by the pydantic schema in `ramona_labware/schema.py`.

Browse them in 3D: https://docs.ramonaoptics.com/tools/labware_viewer.html

```python
from ramona_labware import load_labware

plates = load_labware()  # {'SBS_96_well_plate': Labware(...), ...}
```

Split out of python-owl (`owl/instruments/labware/`) with its git history.

## Requesting a plate

Post the vendor and part number in Slack `#labware-requests`; the labware bot
opens a pull request here. Every new definition is added to the parametrized
list in `tests/test_labware.py`.
