from datetime import datetime
from typing import Literal, Optional

from pydantic import ConfigDict, Field, model_validator

from ._model import RamonaBaseModel


class OuterDimensions(RamonaBaseModel):
    """
    Model describing the outer dimensions of a labware plate.
    """
    model_config = ConfigDict(
        title="Outer Dimensions",
    )

    owl_settings_type: Literal["labware_outer_dimensions"] = Field(
        "labware_outer_dimensions",
        alias='__owl_settings_type__',
    )

    length: float = Field(
        description="Length of the plate in meters"
    )

    width: float = Field(
        description="Width of the plate in meters"
    )

    height: float = Field(
        description="Height of the plate in meters"
    )


class WellDimensions(RamonaBaseModel):
    """
    Model describing the dimensions and properties of wells in a labware plate.
    """
    model_config = ConfigDict(
        title="Well Dimensions",
    )

    owl_settings_type: Literal["labware_well_dimensions"] = Field(
        "labware_well_dimensions",
        alias='__owl_settings_type__',
    )

    pitch: float = Field(
        description="Pitch between wells in meters"
    )

    rows: int = Field(
        description="Number of well rows"
    )

    columns: int = Field(
        description="Number of well columns"
    )

    shape: Literal["circle", "square", "other"] = Field(
        description="Shape of the wells"
    )

    diameter: float = Field(
        description="Diameter of circular wells in meters"
    )

    depth: float = Field(
        description="Depth of wells in meters"
    )

    bottom_shape: Literal["flat", "u", "v"] = Field(
        description="Shape of the well bottom: flat, u-shaped, or v-shaped"
    )


class AlignmentReference(RamonaBaseModel):
    """
    Model describing the alignment reference points for a labware plate.
    """
    model_config = ConfigDict(
        title="Alignment Reference",
    )

    owl_settings_type: Literal["labware_alignment_reference"] = Field(
        "labware_alignment_reference",
        alias='__owl_settings_type__',
    )

    origin_reference: Literal['A1 well center'] = Field(
        'A1 well center',
        description="Reference point for the origin (standardized to A1 well center)"
    )

    offset_from_left_edge: float = Field(
        description="X offset from the left edge of the plate in meters"
    )

    offset_from_top_edge: float = Field(
        description="Y offset from the top edge of the plate in meters"
    )

    z_reference: str = Field(
        description="Z reference point (e.g., 'top surface of plate')"
    )


class Labware(RamonaBaseModel):
    """
    Model describing a complete labware definition including dimensions, wells, and alignment.
    """
    model_config = ConfigDict(
        title="Labware Definition",
    )

    owl_settings_type: Literal["labware"] = Field(
        "labware",
        alias='__owl_settings_type__',
    )

    name: str = Field(
        description="Name of the labware (e.g., 'SBS 384 well')"
    )

    number_of_wells: int = Field(
        description="Total number of wells in the plate"
    )

    manufacturer: str = Field(
        description="Organization that designed the labware"
    )

    author: str = Field(
        description="Author or organization that wrote the labware specification"
    )

    last_updated: datetime = Field(
        description="Date when the labware definition was last updated (ISO/UTC format)"
    )

    part_number: str = Field(
        description="Part number or identifier for the labware"
    )

    web_reference: str = Field(
        description="URL reference to the labware specification"
    )

    outer_plate_dimensions: OuterDimensions = Field(
        description="Outer dimensions of the plate"
    )

    well_dimensions: WellDimensions = Field(
        description="Dimensions and properties of the wells"
    )

    alignment_reference: AlignmentReference = Field(
        description="Alignment reference points for the plate"
    )

    notes: Optional[str] = Field(
        None,
        description="Additional notes about the labware definition"
    )

    @model_validator(mode='after')
    def validate_well_count(self) -> 'Labware':
        expected_wells = self.well_dimensions.rows * self.well_dimensions.columns
        if self.number_of_wells != expected_wells:
            raise ValueError(
                f"number_of_wells ({self.number_of_wells}) must equal "
                "rows * columns "
                f"({self.well_dimensions.rows} * {self.well_dimensions.columns} = {expected_wells})"
            )
        return self
