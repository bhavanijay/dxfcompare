#!/usr/bin/env python3
"""
Test script for DXF Text Orientation Comparator

This script creates sample DXF files with text entities at different
orientations for testing the comparison functionality.
"""

import ezdxf
import math


def create_sample_dxf_files():
    """Create sample DXF files for testing"""

    # Create first DXF file
    doc1 = ezdxf.new("R2010")
    msp1 = doc1.modelspace()

    # Add some text entities with different orientations
    msp1.add_text(
        "SAMPLE TEXT 1",
        dxfattribs={
            "insert": (10, 10),
            "height": 2.5,
            "rotation": math.radians(0),  # 0 degrees
            "layer": "TEXT",
        },
    )

    msp1.add_text(
        "SAMPLE TEXT 2",
        dxfattribs={
            "insert": (20, 10),
            "height": 2.5,
            "rotation": math.radians(45),  # 45 degrees
            "layer": "TEXT",
        },
    )

    msp1.add_text(
        "SAMPLE TEXT 3",
        dxfattribs={
            "insert": (30, 10),
            "height": 2.5,
            "rotation": math.radians(90),  # 90 degrees
            "layer": "TEXT",
        },
    )

    # Add MTEXT entity
    msp1.add_mtext(
        "MULTILINE\nTEXT SAMPLE",
        dxfattribs={
            "insert": (10, 20),
            "char_height": 2.0,
            "rotation": math.radians(30),  # 30 degrees
            "layer": "MTEXT",
        },
    )

    doc1.saveas("sample_drawing_v1.dxf")
    print("Created sample_drawing_v1.dxf")

    # Create second DXF file with some orientation changes
    doc2 = ezdxf.new("R2010")
    msp2 = doc2.modelspace()

    # Same text but with different orientations
    msp2.add_text(
        "SAMPLE TEXT 1",
        dxfattribs={
            "insert": (10, 10),
            "height": 2.5,
            "rotation": math.radians(15),  # Changed from 0 to 15 degrees
            "layer": "TEXT",
        },
    )

    msp2.add_text(
        "SAMPLE TEXT 2",
        dxfattribs={
            "insert": (20, 10),
            "height": 2.5,
            "rotation": math.radians(45),  # Same as before
            "layer": "TEXT",
        },
    )

    msp2.add_text(
        "SAMPLE TEXT 3",
        dxfattribs={
            "insert": (30, 10),
            "height": 2.5,
            "rotation": math.radians(135),  # Changed from 90 to 135 degrees
            "layer": "TEXT",
        },
    )

    # Same MTEXT but different rotation
    msp2.add_mtext(
        "MULTILINE\nTEXT SAMPLE",
        dxfattribs={
            "insert": (10, 20),
            "char_height": 2.0,
            "rotation": math.radians(60),  # Changed from 30 to 60 degrees
            "layer": "MTEXT",
        },
    )

    # Add a new text entity
    msp2.add_text(
        "NEW TEXT",
        dxfattribs={
            "insert": (40, 10),
            "height": 2.5,
            "rotation": math.radians(0),
            "layer": "TEXT",
        },
    )

    doc2.saveas("sample_drawing_v2.dxf")
    print("Created sample_drawing_v2.dxf")


def run_test():
    """Run a test comparison"""
    print("Creating sample DXF files...")
    create_sample_dxf_files()

    print("\nRunning comparison test...")

    # Import and run the comparator
    from dxf_text_orientation_compare import DXFTextOrientationComparator

    comparator = DXFTextOrientationComparator(tolerance=0.1)
    results = comparator.compare_files("sample_drawing_v1.dxf", "sample_drawing_v2.dxf")
    comparator.print_results(results, "sample_drawing_v1.dxf", "sample_drawing_v2.dxf")


if __name__ == "__main__":
    run_test()
