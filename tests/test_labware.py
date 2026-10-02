import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

import ramona_labware
from ramona_labware import AlignmentReference, Labware, OuterDimensions, WellDimensions
from ramona_labware.schema import SCHEMA_URL, json_schema

parametrize = pytest.mark.parametrize


def test_valid_outer_dimensions():
    """Test creating valid outer dimensions."""
    dims = OuterDimensions(
        length=0.12776,  # 127.76mm SBS standard
        width=0.08548,   # 85.48mm SBS standard
        height=0.01435   # 14.35mm typical plate height
    )

    assert dims.length == 0.12776
    assert dims.width == 0.08548
    assert dims.height == 0.01435


def test_outer_dimensions_required_fields():
    """Test that all fields are required."""
    with pytest.raises(ValidationError) as exc_info:
        OuterDimensions()

    error_message = str(exc_info.value)
    assert "length" in error_message
    assert "width" in error_message
    assert "height" in error_message


def test_outer_dimensions_negative_values():
    """Test that negative dimensions are allowed (for validation at higher level)."""
    # Note: Pydantic doesn't validate physical constraints by default
    dims = OuterDimensions(length=-0.1, width=0.08548, height=0.01435)
    assert dims.length == -0.1


def test_valid_well_dimensions_384_well():
    """Test creating valid 384-well plate dimensions."""
    wells = WellDimensions(
        pitch=0.0045,  # 4.5mm pitch for 384-well
        rows=16,       # A-P
        columns=24,       # 1-24
        shape="circle",
        diameter=0.0032,         # 3.2mm diameter
        depth=0.0105,           # 10.5mm depth
        bottom_shape="flat"
    )

    assert wells.pitch == 0.0045
    assert wells.rows == 16
    assert wells.columns == 24
    assert wells.shape == "circle"
    assert wells.diameter == 0.0032
    assert wells.depth == 0.0105
    assert wells.bottom_shape == "flat"


def test_valid_well_dimensions_96_well():
    """Test creating valid 96-well plate dimensions."""
    wells = WellDimensions(
        pitch=0.009,   # 9mm pitch for 96-well
        rows=8,        # A-H
        columns=12,       # 1-12
        shape="circle",
        diameter=0.0064,  # 6.4mm diameter
        depth=0.0107,     # 10.7mm depth

        bottom_shape="u"
    )

    assert wells.rows == 8
    assert wells.columns == 12
    assert wells.pitch == 0.009
    assert wells.bottom_shape == "u"


def test_well_dimensions_square_wells():
    """Test creating square well dimensions."""
    wells = WellDimensions(
        pitch=0.009,
        rows=8,
        columns=12,
        shape="square",
        diameter=0.0064,  # For square wells, this might represent side length
        depth=0.0107,

        bottom_shape="flat"
    )

    assert wells.shape == "square"
    assert wells.bottom_shape == "flat"


def test_well_dimensions_invalid_shape():
    """Test that invalid well shapes are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        WellDimensions(
            pitch=0.009,
            rows=8,
            columns=12,
            shape="triangle",  # Invalid shape
            diameter=0.0064,
            depth=0.0107,
            bottom_shape="flat"
        )

    error_message = str(exc_info.value)
    assert "shape" in error_message


def test_well_dimensions_invalid_bottom_shape():
    """Test that invalid bottom shapes are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        WellDimensions(
            pitch=0.009,
            rows=8,
            columns=12,
            shape="circle",
            diameter=0.0064,
            depth=0.0107,
            bottom_shape="pyramid"  # Invalid bottom shape
        )

    error_message = str(exc_info.value)
    assert "bottom_shape" in error_message


def test_well_dimensions_zero_rows_columns():
    """Test that zero rows/columns are handled."""
    # This should be allowed by Pydantic but caught by business logic
    wells = WellDimensions(
        pitch=0.009,
        rows=0,
        columns=0,
        shape="circle",
        diameter=0.0064,
        depth=0.0107,
        bottom_shape="flat"
    )

    assert wells.rows == 0
    assert wells.columns == 0


def test_valid_alignment_reference():
    """Test creating valid alignment reference."""
    alignment = AlignmentReference(
        origin_reference="A1 well center",
        offset_from_left_edge=0.01438,  # 14.38mm from left edge
        offset_from_top_edge=0.01124,   # 11.24mm from top edge
        z_reference="top surface of plate"
    )

    assert alignment.origin_reference == "A1 well center"
    assert alignment.offset_from_left_edge == 0.01438
    assert alignment.offset_from_top_edge == 0.01124
    assert alignment.z_reference == "top surface of plate"


def test_labware_creation():
    """Test creating a labware object with all required fields."""
    labware = Labware(
        name="Test Plate",
        number_of_wells=96,
        manufacturer="Test Manufacturer",
        author="Test Author",
        last_updated=datetime(2023, 1, 1, tzinfo=UTC),
        part_number="TEST001",
        web_reference="https://example.com",

        outer_plate_dimensions=OuterDimensions(
            length=0.12776,
            width=0.08548,
            height=0.01435
        ),
        well_dimensions=WellDimensions(
            pitch=0.009,
            rows=8,
            columns=12,
            shape="circle",
            diameter=0.0064,
            depth=0.0107,

            bottom_shape="u"
        ),
        alignment_reference=AlignmentReference(
            origin_reference="A1 well center",
            offset_from_left_edge=0.01438,
            offset_from_top_edge=0.01124,
            z_reference="top surface of plate"
        )
    )

    assert labware.name == "Test Plate"
    assert labware.number_of_wells == 96
    assert labware.manufacturer == "Test Manufacturer"
    assert labware.well_dimensions.rows == 8
    assert labware.well_dimensions.columns == 12
    assert labware.well_dimensions.bottom_shape == "u"


def test_valid_384_well_plate():
    """Test creating a complete 384-well plate definition."""
    outer_dims = OuterDimensions(
        length=0.12776,
        width=0.08548,
        height=0.01435
    )

    well_dims = WellDimensions(
        pitch=0.0045,
        rows=16,
        columns=24,
        shape="circle",
        diameter=0.0032,
        depth=0.0105,

        bottom_shape="flat"
    )

    alignment = AlignmentReference(
        origin_reference="A1 well center",
        offset_from_left_edge=0.01438,
        offset_from_top_edge=0.01124,
        z_reference="top surface of plate"
    )

    labware = Labware(
        name="SBS 384 well",
        number_of_wells=384,
        manufacturer="Ramona Optics",
        author="Ramona Optics",
        last_updated=datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC),
        part_number="RO-384-001",
        web_reference="https://www.ramonaoptics.com/labware/384-well",

        outer_plate_dimensions=outer_dims,
        well_dimensions=well_dims,
        alignment_reference=alignment,
        notes="Standard SBS 384-well plate for high-throughput screening"
    )

    assert labware.name == "SBS 384 well"
    assert labware.number_of_wells == 384
    assert labware.manufacturer == "Ramona Optics"
    assert labware.author == "Ramona Optics"

    assert labware.notes == "Standard SBS 384-well plate for high-throughput screening"

    # Test nested model access
    assert labware.outer_plate_dimensions.length == 0.12776
    assert labware.well_dimensions.rows == 16
    assert labware.well_dimensions.columns == 24
    assert labware.well_dimensions.bottom_shape == "flat"
    assert labware.alignment_reference.origin_reference == "A1 well center"


def test_labware_without_notes():
    """Test creating labware without optional notes field."""
    outer_dims = OuterDimensions(length=0.12776, width=0.08548, height=0.01435)
    well_dims = WellDimensions(
        pitch=0.009, rows=8, columns=12, shape="circle",
        diameter=0.0064,
        depth=0.0107,
        bottom_shape="u"
    )
    alignment = AlignmentReference(
        origin_reference="A1 well center",
        offset_from_left_edge=0.01438,
        offset_from_top_edge=0.01124,
        z_reference="top surface"
    )

    labware = Labware(
        name="SBS 96 well",
        number_of_wells=96,
        manufacturer="Test Manufacturer",
        author="Test Author",
        last_updated=datetime.now(UTC),
        part_number="TEST-96-001",
        web_reference="https://example.com",

        outer_plate_dimensions=outer_dims,
        well_dimensions=well_dims,
        alignment_reference=alignment
        # notes is optional
    )

    assert labware.notes is None


def test_labware_well_count_consistency():
    """Test that well count matches rows * columns (business logic validation)."""
    outer_dims = OuterDimensions(length=0.12776, width=0.08548, height=0.01435)
    well_dims = WellDimensions(
        pitch=0.009, rows=8, columns=12, shape="circle",
        diameter=0.0064,
        depth=0.0107,
        bottom_shape="u"
    )
    alignment = AlignmentReference(
        origin_reference="A1 well center",
        offset_from_left_edge=0.01438,
        offset_from_top_edge=0.01124,
        z_reference="top surface"
    )

    # This creates a labware with inconsistent well count (should be 96, not 384)
    with pytest.raises(ValidationError):
        Labware(
            name="Inconsistent Plate",
            number_of_wells=384,  # Wrong count for 8x12 = 96 wells
            manufacturer="Test Manufacturer",
            author="Test Author",
            last_updated=datetime.now(UTC),
            part_number="TEST-INCONSISTENT",
            web_reference="https://example.com",

            outer_plate_dimensions=outer_dims,
            well_dimensions=well_dims,
            alignment_reference=alignment
        )


def test_labware_serialization():
    """Test that labware can be serialized to dict and back."""
    outer_dims = OuterDimensions(length=0.12776, width=0.08548, height=0.01435)
    well_dims = WellDimensions(
        pitch=0.0045, rows=16, columns=24, shape="circle",
        diameter=0.0032,
        depth=0.0105,
        bottom_shape="flat"
    )
    alignment = AlignmentReference(
        origin_reference="A1 well center",
        offset_from_left_edge=0.01438,
        offset_from_top_edge=0.01124,
        z_reference="top surface of plate"
    )

    original_labware = Labware(
        name="Test Serialization Plate",
        number_of_wells=384,
        manufacturer="Test Manufacturer",
        author="Test Author",
        last_updated=datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC),
        part_number="TEST-SER-001",
        web_reference="https://test.com",

        outer_plate_dimensions=outer_dims,
        well_dimensions=well_dims,
        alignment_reference=alignment
    )

    # Serialize to dict
    labware_dict = original_labware.model_dump()

    # Deserialize back to object
    restored_labware = Labware.model_validate(labware_dict)

    # Verify they're equivalent
    assert restored_labware.name == original_labware.name
    assert restored_labware.number_of_wells == original_labware.number_of_wells

    assert restored_labware.well_dimensions.rows == original_labware.well_dimensions.rows


def test_labware_json_serialization():
    """Test JSON serialization with datetime handling."""
    outer_dims = OuterDimensions(length=0.12776, width=0.08548, height=0.01435)
    well_dims = WellDimensions(
        pitch=0.009, rows=8, columns=12, shape="circle",
        diameter=0.0064,
        depth=0.0107,
        bottom_shape="u"
    )
    alignment = AlignmentReference(
        origin_reference="A1 well center",
        offset_from_left_edge=0.01438,
        offset_from_top_edge=0.01124,
        z_reference="top surface"
    )

    time = datetime(2024, 1, 15, 12, 30, 45, tzinfo=UTC)

    labware = Labware(
        name="JSON Test Plate",
        number_of_wells=96,
        manufacturer="JSON Manufacturer",
        author="JSON Author",
        last_updated=time,
        part_number="JSON-96-001",
        web_reference="https://json-test.com",

        outer_plate_dimensions=outer_dims,
        well_dimensions=well_dims,
        alignment_reference=alignment
    )

    # Test JSON serialization
    json = labware.model_dump()
    assert isinstance(json, dict)
    assert json["name"] == "JSON Test Plate"
    assert json["last_updated"] == time

    # Test JSON deserialization
    restored_labware = Labware.model_validate(json)
    assert restored_labware.name == labware.name
    assert restored_labware.last_updated == labware.last_updated


def test_labware_validation_missing_fields():
    """Test labware validation with missing required fields."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        Labware(
            name="Invalid Plate",
            # Missing required fields
        )


def test_labware_validation_invalid_well_shape():
    """Test labware validation with invalid well shape."""
    # Test invalid well dimensions
    with pytest.raises(ValidationError):
        Labware(
            name="Test Plate",
            number_of_wells=96,
            manufacturer="Test Manufacturer",
            author="Test Author",
            last_updated=datetime(2023, 1, 1, tzinfo=UTC),
            part_number="TEST001",
            web_reference="https://example.com",

            outer_plate_dimensions=OuterDimensions(
                length=0.12776,
                width=0.08548,
                height=0.01435
            ),
            well_dimensions=WellDimensions(
                pitch=0.009,
                rows=8,
                columns=12,
                shape="invalid_shape",  # Invalid shape
                diameter=0.0064,
                depth=0.0107,

                bottom_shape="flat"
            ),
            alignment_reference=AlignmentReference(
                origin_reference="A1 well center",
                offset_from_left_edge=0.01438,
                offset_from_top_edge=0.01124,
                z_reference="top surface of plate"
            )
        )


def test_common_plate_formats():
    """Test that common plate formats can be represented."""
    # Test data for common formats
    plate_formats = [
        {"name": "6-well", "rows": 2, "columns": 3, "wells": 6, "pitch": 0.039},
        {"name": "12-well", "rows": 3, "columns": 4, "wells": 12, "pitch": 0.0225},
        {"name": "24-well", "rows": 4, "columns": 6, "wells": 24, "pitch": 0.016},
        {"name": "48-well", "rows": 6, "columns": 8, "wells": 48, "pitch": 0.0125},
        {"name": "96-well", "rows": 8, "columns": 12, "wells": 96, "pitch": 0.009},
        {"name": "384-well", "rows": 16, "columns": 24, "wells": 384, "pitch": 0.0045},
        {"name": "1536-well", "rows": 32, "columns": 48, "wells": 1536, "pitch": 0.00225},
    ]

    for plate_format in plate_formats:
        outer_dims = OuterDimensions(length=0.12776, width=0.08548, height=0.01435)
        well_dims = WellDimensions(
            pitch=plate_format["pitch"],
            rows=plate_format["rows"],
            columns=plate_format["columns"],
            shape="circle",
            diameter=plate_format["pitch"] * 0.7,  # Typical well diameter
            depth=0.01,

            bottom_shape="flat"
        )
        alignment = AlignmentReference(
            origin_reference="A1 well center",
            offset_from_left_edge=plate_format["pitch"],
            offset_from_top_edge=plate_format["pitch"],
            z_reference="top surface"
        )

        labware = Labware(
            name=f"SBS {plate_format['name']} plate",
            number_of_wells=plate_format["wells"],
            manufacturer="Test Suite",
            author="Test Suite",
            last_updated=datetime.now(UTC),
            part_number=f"TEST-{plate_format['wells']}-001",
            web_reference="https://test.com",

            outer_plate_dimensions=outer_dims,
            well_dimensions=well_dims,
            alignment_reference=alignment
        )

        # Verify the plate was created successfully
        assert labware.number_of_wells == plate_format["wells"]
        assert labware.well_dimensions.rows == plate_format["rows"]
        assert labware.well_dimensions.columns == plate_format["columns"]

        # Business logic check: well count should match rows * columns
        calculated_wells = labware.well_dimensions.rows * labware.well_dimensions.columns
        assert calculated_wells == plate_format["wells"]


def test_physical_constraints_assumptions():
    """Test assumptions about physical constraints (for future validation)."""
    # These tests document expected behavior even if not enforced by Pydantic

    # Assumption: Well pitch should be larger than well diameter
    well_dims = WellDimensions(
        pitch=0.009,     # 9mm pitch
        rows=8, columns=12,
        shape="circle",
        diameter=0.0064,  # 6.4mm diameter (reasonable)
        depth=0.01,

        bottom_shape="u"
    )

    # This should be physically reasonable
    assert well_dims.pitch > well_dims.diameter

    # Test unreasonable case (diameter larger than pitch)
    unreasonable_wells = WellDimensions(
        pitch=0.005,     # 5mm pitch
        rows=8, columns=12,
        shape="circle",
        diameter=0.008,  # 8mm diameter (larger than pitch!)
        depth=0.01,

        bottom_shape="v"
    )

    # Pydantic allows this, but business logic should catch it
    assert unreasonable_wells.diameter > unreasonable_wells.pitch


@parametrize('plate_file,expected_name,expected_wells,expected_rows,expected_columns', [
    ('SBS_96_well_plate.json', 'SBS 96 well', 96, 8, 12),
    ('SBS_384_well_plate.json', 'SBS 384 well', 384, 16, 24),
    ('SBS_1536_well_plate.json', 'SBS 1536 well', 1536, 32, 48),
    ('Akura_384_spheroid_microplate.json', 'Akura 384 Spheroid Microplate', 384, 16, 24),
    ('Akura_96_spheroid_microplate.json', 'Akura 96 Spheroid Microplate', 96, 8, 12),
    ('CellVis_24_well_plate.json', 'CellVis 24 well', 24, 4, 6),
    ('Corning_costar_6_well_plate.json', 'Corning Costar 6 well', 6, 2, 3),
    ('Corning_costar_12_well_plate.json', 'Corning Costar 12 well', 12, 3, 4),
    ('Corning_costar_24_well_plate.json', 'Corning Costar 24 well', 24, 4, 6),
    ('Watson_bio_24_well_plate.json', 'Watson Bio 24 well', 24, 4, 6),
    ('TPP_92412_12_well_plate.json', 'TPP 92412 12 well', 12, 3, 4),
    ('Corning_3599_96_well_plate.json', 'Corning 3599 96 well', 96, 8, 12),
    ('Corning_3610_96_well_plate.json', 'Corning 3610 96 well', 96, 8, 12),
    ('Corning_3601_96_well_plate.json', 'Corning 3601 96 well', 96, 8, 12),
    ('Thermo_nunc_167008_96_well_plate.json', 'Thermo Nunc 167008 96 well', 96, 8, 12),
    ('Thermo_nunc_165305_96_well_plate.json', 'Thermo Nunc 165305 96 well', 96, 8, 12),
    ('Thermo_nunc_142475_24_well_plate.json', 'Thermo Nunc 142475 24 well', 24, 4, 6),
    ('Thermo_nunc_142485_24_well_plate.json', 'Thermo Nunc 142485 24 well', 24, 4, 6),
    ('Greiner_655090_96_well_plate.json', 'Greiner CELLSTAR 655090 96 well', 96, 8, 12),
    ('Greiner_655161_96_well_plate.json', 'Greiner 655161 96 well', 96, 8, 12),
    ('Greiner_655180_96_well_plate.json', 'Greiner CELLSTAR 655180 96 well', 96, 8, 12),
    ('Revvity_phenoplate_96_well_plate.json', 'Revvity PhenoPlate 96 well', 96, 8, 12),
    ('Revvity_phenoplate_384_well_plate.json', 'Revvity PhenoPlate 384 well', 384, 16, 24),
    ('Greiner_783092_1536_well_plate.json', 'Greiner CELLSTAR 783092 1536 well', 1536, 32, 48),
    ('Genesee_25-105_6_well_plate.json', 'Genesee GenClone 25-105 6 well', 6, 2, 3),
    ('Corning_351146_6_well_plate.json', 'Corning Falcon 351146 6 well', 6, 2, 3),
    ('Corning_3527_24_well_plate.json', 'Corning Costar 3527 24 well', 24, 4, 6),
    ('Corning_353502_6_well_plate.json', 'Corning Falcon 353502 6 well', 6, 2, 3),
    ('Corning_3512_12_well_plate.json', 'Corning Costar 3512 12 well', 12, 3, 4),
    ('Corning_3335_6_well_plate.json', 'Corning Costar 3335 6 well', 6, 2, 3),
    ('Corning_3548_48_well_plate.json', 'Corning Costar 3548 48 well', 48, 6, 8),
    ('InSphero_GRI3D-96IBI_96_well_plate.json',
     'InSphero Gri3D Imaging GRI3D-96IBI-S 96 well', 96, 8, 12),
    ('InSphero_GRI3D-96P_96_well_plate.json',
     'InSphero Gri3D Plastic GRI3D-96P-S 96 well', 96, 8, 12),
    ('TPP_92424_24_well_plate.json', 'TPP 92424 24 well', 24, 4, 6),
    ('TPP_92406_6_well_plate.json', 'TPP 92406 6 well', 6, 2, 3),
    ('Mimetas_4004-400-B_384_well_plate.json',
     'Mimetas OrganoPlate 3-lane 40 4004-400-B 384 well', 384, 16, 24),
    ('Mimetas_6405-400-B_384_well_plate.json',
     'Mimetas OrganoPlate 3-lane 64 6405-400-B 384 well', 384, 16, 24),
    ('Mimetas_6401-400-B_384_well_plate.json',
     'Mimetas OrganoPlate Graft 6401-400-B 384 well', 384, 16, 24),
    ('Axion_M768-SPH-48B_48_well_plate.json',
     'Axion SpheroGuide MEA M768-SPH-48B 48 well', 48, 6, 8),
    ('Corning_3764_384_well_plate.json', 'Corning 3764 384 well', 384, 16, 24),
    ('Ibidi_82426_24_well_plate.json', 'Ibidi mu-Plate 82426 24 well', 24, 4, 6),
    ('Ibidi_80636_6_well_plate.json', 'Ibidi mu-Plate 80636 6 well', 6, 2, 3),
    ('Corning_3830_384_well_plate.json',
     'Corning 3830 384 well spheroid', 384, 16, 24),
    ('Thermo_nunc_150628_12_well_plate.json', 'Thermo Nunc 150628 12 well multidish', 12, 3, 4),
    ('Ramona_petri_dish_insert_30_mm.json', 'Ramona Petri Dish Insert 30 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_35_mm.json', 'Ramona Petri Dish Insert 35 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_40_mm.json', 'Ramona Petri Dish Insert 40 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_45_mm.json', 'Ramona Petri Dish Insert 45 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_50_mm.json', 'Ramona Petri Dish Insert 50 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_55_mm.json', 'Ramona Petri Dish Insert 55 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_60_mm.json', 'Ramona Petri Dish Insert 60 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_65_mm.json', 'Ramona Petri Dish Insert 65 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_70_mm.json', 'Ramona Petri Dish Insert 70 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_75_mm.json', 'Ramona Petri Dish Insert 75 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_80_mm.json', 'Ramona Petri Dish Insert 80 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_85_mm.json', 'Ramona Petri Dish Insert 85 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_90_mm.json', 'Ramona Petri Dish Insert 90 mm', 1, 1, 1),
    ('Ramona_petri_dish_insert_95_mm.json', 'Ramona Petri Dish Insert 95 mm', 1, 1, 1),
])
def test_plate_definition_files_can_be_loaded(
    plate_file, expected_name, expected_wells, expected_rows, expected_columns
):
    plate_definitions_path = Path(ramona_labware.__file__).parent / "definitions"
    plate_file_path = (plate_definitions_path / plate_file).resolve()

    assert plate_file_path.is_file(), f"Plate definition file {plate_file} not found"

    labware = Labware.model_validate_json_file(plate_file_path)

    assert labware.name == expected_name
    assert labware.number_of_wells == expected_wells
    assert labware.well_dimensions.rows == expected_rows
    assert labware.well_dimensions.columns == expected_columns

    calculated_wells = labware.well_dimensions.rows * labware.well_dimensions.columns
    assert calculated_wells == expected_wells

    assert labware.manufacturer
    assert labware.author
    assert labware.part_number
    assert labware.web_reference
    assert labware.last_updated

    assert labware.outer_plate_dimensions.length > 0
    assert labware.outer_plate_dimensions.width > 0
    assert labware.outer_plate_dimensions.height > 0

    assert labware.well_dimensions.pitch > 0
    assert labware.well_dimensions.diameter > 0
    assert labware.well_dimensions.depth > 0
    assert labware.well_dimensions.shape in ["circle", "square"]
    assert labware.well_dimensions.bottom_shape in ["flat", "u", "v"]

    assert labware.alignment_reference.origin_reference == "A1 well center"
    assert labware.alignment_reference.offset_from_left_edge >= 0
    assert labware.alignment_reference.offset_from_top_edge >= 0
    assert labware.alignment_reference.z_reference


def test_definition_files_name_the_schema_version():
    definitions = Path(ramona_labware.__file__).parent / "definitions"
    for plate_file in definitions.glob("*.json"):
        assert json.loads(plate_file.read_text())["$schema"] == SCHEMA_URL, plate_file.name


def test_published_schema_matches_the_model():
    # Regenerate with:
    # python -c "import json; from ramona_labware.schema import json_schema; print(json.dumps(json_schema(), indent=2))" > ramona_labware/labware.v1.schema.json
    published = Path(ramona_labware.__file__).parent / "labware.v1.schema.json"
    assert json.loads(published.read_text()) == json_schema()
