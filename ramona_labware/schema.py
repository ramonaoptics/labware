import json
from datetime import datetime
from importlib.resources.abc import Traversable
from os import PathLike
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import JsonSchemaValue

# A definition names the schema version it was written against in its
# ``$schema`` key. A change that old files would not satisfy gets a new
# version and a new file beside this one.
SCHEMA_URL = (
    'https://raw.githubusercontent.com/ramonaoptics/labware/main/'
    'ramona_labware/labware.v1.schema.json'
)


class _LabwareModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class OuterDimensions(_LabwareModel):
    """Model describing the outer dimensions of a labware plate.

    The skirt is the bottom outside flange the plate rests on and a plate nest
    holds it by. Anything not recorded about it is the ANSI/SLAS standard: the
    plate's length and width with 3.18 mm outside corner radii (ANSI/SLAS
    1-2004), a 6.10 mm tall flange (the medium height of ANSI/SLAS 3-2004) and a
    1.27 mm flange width (its minimum). A skirt as tall as the plate is a plate
    whose outside walls run straight from the plane it rests on to its top with
    no step, such as a solid glass or quartz block; there is no flange top, and
    no thickness is recorded.
    """

    model_config = ConfigDict(
        title="Outer Dimensions",
    )

    length: float = Field(description="Length of the plate in meters")

    width: float = Field(description="Width of the plate in meters")

    height: float = Field(description="Height of the plate in meters")

    height_with_lid: float | None = Field(
        None,
        description=(
            "Height of the plate with its lid on, in meters; None when it has no "
            "lid or the height is not known. This key was added in version 0.19.621."
        ),
    )

    skirt_outline: list[tuple[float, float]] | None = Field(
        None,
        description=(
            "Outer edge of the skirt where it meets the plane the plate rests "
            "on, as a closed polyline of (x, y) points in meters: x from the "
            "left edge and y from the top edge of the plate, the edges the A1 "
            "offsets are measured from, seen from above with A1 at the top "
            "left. Curves such as rounded corners are sampled into points. "
            "None when the skirt is the plate's length and width with rounded "
            "corners. This key was added in version 0.19.621."
        ),
    )

    skirt_height: float | list[float] | None = Field(
        None,
        description=(
            "Height of the skirt above the plane the plate rests on, in "
            "meters: the ANSI/SLAS 3-2004 flange height, or the plate's height "
            "for a plate whose outside walls are straight with no step. One "
            "height all round, or, for a skirt whose height changes around the "
            "plate, a list of one height per segment of skirt_outline, in "
            "meters: the i-th from the i-th point to the next, the last back to "
            "the first. None when not known. This key was added in version "
            "0.19.621."
        ),
    )

    skirt_thickness: float | None = Field(
        None,
        description=(
            "Thickness of the skirt measured at its top, in meters: the "
            "ANSI/SLAS 3-2004 flange width; None when not known. "
            "This key was added in version 0.19.621."
        ),
    )

    upper_outline: list[tuple[float, float]] | None = Field(
        None,
        description=(
            "Outer edge of the plate's body above its skirt, seen from above, "
            "as a closed polyline of (x, y) points in meters in the same frame "
            "as the skirt outline. None when not recorded, and the body is "
            "taken to follow the skirt's outline up to the top of the plate. "
            "This key was added in version 0.19.621."
        ),
    )

    @model_validator(mode='after')
    def validate_skirt_outline(self) -> 'OuterDimensions':
        outline = self.skirt_outline
        if outline is None:
            return self
        if len(outline) < 3:
            message = "a skirt outline needs at least three points"
            raise ValueError(message)
        # Half a millimeter is the ANSI/SLAS 1-2004 footprint tolerance.
        if not all(
            -5e-4 <= x <= self.length + 5e-4 and -5e-4 <= y <= self.width + 5e-4
            for x, y in outline
        ):
            message = "the skirt outline must lie within the plate's length and width"
            raise ValueError(message)
        return self

    @model_validator(mode='after')
    def validate_upper_outline(self) -> 'OuterDimensions':
        outline = self.upper_outline
        if outline is None:
            return self
        if len(outline) < 3:
            message = "an upper outline needs at least three points"
            raise ValueError(message)
        if not all(
            -5e-4 <= x <= self.length + 5e-4 and -5e-4 <= y <= self.width + 5e-4
            for x, y in outline
        ):
            message = "the upper outline must lie within the plate's length and width"
            raise ValueError(message)
        return self

    @model_validator(mode='after')
    def validate_skirt_height(self) -> 'OuterDimensions':
        heights = self.skirt_height
        if heights is None:
            return self
        if isinstance(heights, list):
            if self.skirt_outline is None or len(heights) != len(self.skirt_outline):
                message = (
                    "a list of skirt heights needs a skirt outline with one "
                    "point per height"
                )
                raise ValueError(message)
        else:
            heights = [heights]
        if any(h <= 0 or h > self.height + 5e-4 for h in heights):
            message = "the skirt cannot be taller than the plate"
            raise ValueError(message)
        return self


class WellDimensions(_LabwareModel):
    """Model describing the dimensions and properties of wells in a labware plate."""

    model_config = ConfigDict(
        title="Well Dimensions",
    )

    pitch: float = Field(description="Pitch between wells in meters")

    rows: int = Field(description="Number of well rows")

    columns: int = Field(description="Number of well columns")

    shape: Literal["circle", "square", "other"] = Field(
        description=(
            "Cross-section of the wells at the bottom, where the sample sits; "
            "see bottom_shape for the profile of the floor"
        ),
    )

    top_shape: str | None = Field(
        None,
        description=(
            "Cross-section of the well opening at the top, in short plain words; None "
            "when it is not recorded. Suggested values, to reuse where they fit: "
            "circle, "
            "square, other. This key was added in version 0.19.621."
        ),
    )

    diameter: float = Field(
        description=(
            "Diameter of circular wells, or side of square wells, at the well "
            "bottom, where the sample sits, in meters"
        ),
    )

    diameter_top: float | None = Field(
        None,
        description=(
            "Diameter of circular wells, or side of square wells, at the well "
            "opening at the top in meters; None when it is not recorded. "
            "This key was added in version 0.19.621."
        ),
    )

    depth: float = Field(description="Depth of wells in meters")

    bottom_shape: Literal["flat", "u", "v"] = Field(
        description="Shape of the well bottom: flat, u-shaped, or v-shaped",
    )

    bottom_radius: float | None = Field(
        None,
        description=(
            "Radius of curvature of a u-shaped well bottom in meters; None when "
            "not known, and the bottom is taken as a hemisphere. "
            "This key was added in version 0.19.621."
        ),
    )

    bottom_angle: float | None = Field(
        None,
        description=(
            "Included angle of a v-shaped well bottom in degrees; None when not "
            "known, and the bottom is taken as a 90 degree cone. "
            "This key was added in version 0.19.621."
        ),
    )

    working_volume_min: float | None = Field(
        None,
        description=(
            "Smallest volume the manufacturer recommends for a well, in liters; "
            "the same as working_volume_max when a single volume is given; None "
            "when not known. This key was added in version 0.19.621."
        ),
    )

    working_volume_max: float | None = Field(
        None,
        description=(
            "Largest volume the manufacturer recommends for a well, in liters; "
            "None when not known. This key was added in version 0.19.621."
        ),
    )

    bottom_color: str | None = Field(
        None,
        description=(
            "Color of the well bottom, in short plain words: clear to image through "
            "it, "
            "black or white when it is opaque, which no light passes through, so the "
            "plate cannot be imaged through its bottom or used on a transmitted-light "
            "instrument such as Vireo; None when not known. The color of the plate, as "
            "vendors name it, is its wall_color. Suggested values, to reuse where they "
            "fit: clear, black, white. This key was added in version 0.19.621."
        ),
    )

    bottom_material: str | None = Field(
        None,
        description=(
            "Material of the well bottom, in short plain words; None when not known. "
            "Suggested values, to reuse where they fit: polystyrene, polypropylene, "
            "cyclo_olefin, glass, polymer_coverslip, film, other. This key was added "
            "in "
            "version 0.19.621."
        ),
    )

    bottom_thickness: float | None = Field(
        None,
        description=(
            "Thickness of the well bottom in meters; None when not known. This key was "
            "added in version 0.19.621."
        ),
    )

    bottom_refractive_index: float | None = Field(
        None,
        description=(
            "Refractive index of the well bottom, dimensionless; None when not known. "
            "This key was added in version 0.19.621."
        ),
    )

    bottom_elevation: float | None = Field(
        None,
        description=(
            "Height of the underside of the well bottom above the plane the plate "
            "rests "
            "on, in meters; None when not known. This key was added in version "
            "0.19.621."
        ),
    )

    floor_height: float | None = Field(
        None,
        description=(
            "Height of the surface the sample sits on above the plane the plate rests "
            "on, "
            "in meters: bottom_elevation plus bottom_thickness; None when not known. "
            "This "
            "key was added in version 0.19.621."
        ),
    )

    wall_material: str | None = Field(
        None,
        description=(
            "Material of the well walls, in short plain words; None when not known. "
            "Suggested values, to reuse where they fit: polystyrene, polypropylene, "
            "cyclo_olefin, glass, polymer_coverslip, film, other. This key was added "
            "in "
            "version 0.19.621."
        ),
    )

    wall_color: str | None = Field(
        None,
        description=(
            "Color of the well walls, in short plain words; None when not known. "
            "Suggested values, to reuse where they fit: clear, black, white, other. "
            "This "
            "key was added in version 0.19.621."
        ),
    )

    wall_thickness: float | None = Field(
        None,
        description=(
            "Thinnest wall between neighboring wells, in meters; None when not known. "
            "This key was added in version 0.19.621."
        ),
    )

    surface_treatments: list[str] | None = Field(
        None,
        description=(
            "The treatments this well geometry is sold with, across the catalog "
            "numbers "
            "a definition covers, as short plain words; it does not say which catalog "
            "number has which. None when not recorded. Suggested values, to reuse "
            "where "
            "they fit: tissue culture, untreated, ultra-low attachment, "
            "cell-repellent, "
            "poly-D-lysine, collagen, fibronectin, high binding, non-binding. This key "
            "was added in version 0.19.621."
        ),
    )

    @model_validator(mode='after')
    def validate_working_volume(self) -> 'WellDimensions':
        low, high = self.working_volume_min, self.working_volume_max
        if low is not None and high is not None and low > high:
            message = (
                f"working_volume_min ({low}) must not exceed "
                f"working_volume_max ({high})"
            )
            raise ValueError(message)
        return self

    @model_validator(mode='after')
    def validate_floor_height(self) -> 'WellDimensions':
        # Vendors' own stacks miss by tenths of a millimeter; more is a typo.
        parts = (self.bottom_elevation, self.bottom_thickness, self.floor_height)
        if (
            parts[0] is not None
            and parts[1] is not None
            and parts[2] is not None
            and abs(parts[0] + parts[1] - parts[2]) > 1e-4
        ):
            message = (
                f"floor_height ({parts[2]}) must equal "
                "bottom_elevation + bottom_thickness "
                f"({parts[0]} + {parts[1]}) to within 0.1 mm"
            )
            raise ValueError(message)
        return self


class AlignmentReference(_LabwareModel):
    """Model describing the alignment reference points for a labware plate."""

    model_config = ConfigDict(
        title="Alignment Reference",
    )

    origin_reference: Literal['A1 well center'] = Field(
        'A1 well center',
        description="Reference point for the origin (standardized to A1 well center)",
    )

    offset_from_left_edge: float = Field(
        description=(
            "X offset of the A1 well center at the well bottom, where the "
            "sample sits, from the left edge of the plate in meters"
        ),
    )

    offset_from_top_edge: float = Field(
        description=(
            "Y offset of the A1 well center at the well bottom, where the "
            "sample sits, from the top edge of the plate in meters"
        ),
    )

    top_offset_from_left_edge: float | None = Field(
        None,
        description=(
            "X offset of the center of the A1 well opening at the top from the "
            "left edge of the plate in meters; None when the opening is "
            "centered over the well bottom. This key was added in version 0.19.621."
        ),
    )

    top_offset_from_top_edge: float | None = Field(
        None,
        description=(
            "Y offset of the center of the A1 well opening at the top from the "
            "top edge of the plate in meters; None when the opening is centered "
            "over the well bottom. This key was added in version 0.19.621."
        ),
    )

    z_reference: str = Field(
        description="Z reference point (e.g., 'top surface of plate')",
    )


class Labware(_LabwareModel):
    """Model describing a complete labware definition including dimensions, wells, and alignment."""  # noqa: E501

    model_config = ConfigDict(
        title="Labware Definition",
    )

    schema_url: Literal[
        "https://raw.githubusercontent.com/ramonaoptics/labware/main/"
        "ramona_labware/labware.v1.schema.json"
    ] = Field(
        SCHEMA_URL,
        alias='$schema',
        description="URL of the JSON schema version this definition follows",
    )

    name: str = Field(description="Name of the labware (e.g., 'SBS 384 well')")

    number_of_wells: int = Field(description="Total number of wells in the plate")

    manufacturer: str = Field(description="Organization that designed the labware")

    author: str = Field(
        description="Author or organization that wrote the labware specification",
    )

    last_updated: datetime = Field(
        description=(
            "Date and time, in UTC to the second (ISO 8601), when a value in the "
            "labware definition last changed; set it to the current time on "
            "every change to the definition"
        ),
    )

    part_number: str = Field(description="Part number or identifier for the labware")

    web_reference: str = Field(
        description="URL of the vendor's product web page for the labware",
    )

    drawing_reference: str | None = Field(
        None,
        description=(
            "URL of the vendor document with the labware's schematic drawing "
            "and dimensions. This key was added in version 0.19.621."
        ),
    )

    applications: list[str] | None = Field(
        None,
        description=(
            "What the plate is used for, as short plain words, so the catalog "
            "can be searched by experiment: the uses the manufacturer names on "
            "its product page, data sheet or application notes, and any our "
            "team has found the plate suited to. List every term that applies, "
            "the general beside the specific: a plate for cardiac organoids "
            "lists '3D culture', 'organoids' and 'cardiac'. A term names a use, "
            "not a property of the plate, whose materials and colors are in "
            "well_dimensions. Suggested terms, to reuse where they fit: cell "
            "culture, suspension culture, primary cells, stem cells, co-culture, "
            "cell culture inserts, 3D culture, spheroids, organoids, "
            "organ-on-chip, tissue explants; neural, cardiac, liver, tumor, "
            "intestinal, vascular; microbiology, zebrafish; imaging, "
            "high-content screening, high-throughput screening, fluorescence, "
            "luminescence, absorbance, binding assays, barrier transport, cell "
            "migration, electrophysiology; PCR, nucleic acids, storage, "
            "crystallography. None when not recorded. This key was added in "
            "version 0.19.621."
        ),
    )

    outer_plate_dimensions: OuterDimensions = Field(
        description="Outer dimensions of the plate",
    )

    well_dimensions: WellDimensions = Field(
        description="Dimensions and properties of the wells",
    )

    alignment_reference: AlignmentReference = Field(
        description="Alignment reference points for the plate",
    )

    notes: str | None = Field(
        None,
        description="Additional notes about the labware definition",
    )

    @classmethod
    def model_validate_json_file(
        cls, file: str | PathLike[str] | Traversable, *, encoding: str = 'utf-8'
    ) -> Self:
        if isinstance(file, (str, PathLike)):
            file = Path(file)
        with file.open(encoding=encoding) as f:
            return cls.model_validate(json.load(f))

    @model_validator(mode='after')
    def validate_well_count(self) -> 'Labware':
        expected_wells = self.well_dimensions.rows * self.well_dimensions.columns
        if self.number_of_wells != expected_wells:
            message = (
                f"number_of_wells ({self.number_of_wells}) must equal "
                "rows * columns "
                f"({self.well_dimensions.rows} * {self.well_dimensions.columns} "
                f"= {expected_wells})"
            )
            raise ValueError(message)
        return self


def json_schema() -> JsonSchemaValue:
    """Return the JSON schema of a labware definition file."""
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': SCHEMA_URL,
        **Labware.model_json_schema(by_alias=True),
    }
