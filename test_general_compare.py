#!/usr/bin/env python3
"""
Test script for DXF General Comparator

This script creates sample DXF files with various types of changes
(excluding text orientation) to test the general comparison functionality.
"""

import ezdxf
import math
from dxf_general_compare import DXFGeneralComparator


def create_test_dxf_files():
    """Create test DXF files with various changes"""

    # Create first DXF file (original)
    doc1 = ezdxf.new("R2010")
    msp1 = doc1.modelspace()

    # Add various entity types
    # Lines
    msp1.add_line((0, 0), (10, 0), dxfattribs={"layer": "LINES", "color": 1})
    msp1.add_line((0, 5), (10, 5), dxfattribs={"layer": "LINES", "color": 2})

    # Circles
    msp1.add_circle((20, 0), 5, dxfattribs={"layer": "CIRCLES", "color": 3})
    msp1.add_circle((30, 0), 3, dxfattribs={"layer": "CIRCLES", "color": 4})

    # Arcs
    msp1.add_arc((40, 0), 5, 0, 90, dxfattribs={"layer": "ARCS", "color": 5})

    # Text (content and size changes, not orientation)
    msp1.add_text(
        "Original Text",
        dxfattribs={"insert": (0, 10), "height": 2.0, "layer": "TEXT", "color": 6},
    )

    msp1.add_text(
        "Text to Change",
        dxfattribs={"insert": (20, 10), "height": 1.5, "layer": "TEXT", "color": 7},
    )

    # Polylines
    points = [(0, 20), (5, 25), (10, 20), (15, 25)]
    msp1.add_lwpolyline(points, dxfattribs={"layer": "POLYLINES", "color": 8})

    # Rectangles (will be modified)
    rect_points = [(30, 20), (40, 20), (40, 30), (30, 30)]
    msp1.add_lwpolyline(
        rect_points, close=True, dxfattribs={"layer": "SHAPES", "color": 9}
    )

    doc1.saveas("test_drawing_original.dxf")
    print("Created test_drawing_original.dxf")

    # Create second DXF file (modified)
    doc2 = ezdxf.new("R2010")
    msp2 = doc2.modelspace()

    # Same lines but one moved
    msp2.add_line((0, 0), (10, 0), dxfattribs={"layer": "LINES", "color": 1})
    # Moved line
    msp2.add_line((2, 5), (12, 5), dxfattribs={"layer": "LINES", "color": 2})

    # Same circles but one with different radius and color
    msp2.add_circle((20, 0), 5, dxfattribs={"layer": "CIRCLES", "color": 3})
    # Changed radius and color
    msp2.add_circle((30, 0), 4, dxfattribs={"layer": "CIRCLES", "color": 10})

    # Arc with different angles
    msp2.add_arc((40, 0), 5, 0, 180, dxfattribs={"layer": "ARCS", "color": 5})

    # Text changes - content and size
    msp2.add_text(
        "Modified Text",
        dxfattribs={  # Content changed
            "insert": (0, 10),
            "height": 2.0,
            "layer": "TEXT",
            "color": 6,
        },
    )

    msp2.add_text(
        "Text to Change",
        dxfattribs={  # Size changed
            "insert": (20, 10),
            "height": 2.5,  # Height changed
            "layer": "TEXT",
            "color": 7,
        },
    )

    # New text
    msp2.add_text(
        "New Text Added",
        dxfattribs={"insert": (40, 10), "height": 1.8, "layer": "TEXT", "color": 11},
    )

    # Same polyline
    points = [(0, 20), (5, 25), (10, 20), (15, 25)]
    msp2.add_lwpolyline(points, dxfattribs={"layer": "POLYLINES", "color": 8})

    # Modified rectangle (different shape)
    modified_rect_points = [(30, 20), (45, 20), (45, 35), (30, 35)]
    msp2.add_lwpolyline(
        modified_rect_points, close=True, dxfattribs={"layer": "SHAPES", "color": 12}
    )

    # New entities
    msp2.add_circle((50, 0), 2, dxfattribs={"layer": "NEW_LAYER", "color": 13})
    msp2.add_line((50, 10), (60, 15), dxfattribs={"layer": "NEW_LAYER", "color": 14})

    doc2.saveas("test_drawing_modified.dxf")
    print("Created test_drawing_modified.dxf")


def run_general_comparison_test():
    """Run the general comparison test"""
    print("Creating test DXF files with various changes...")
    create_test_dxf_files()

    print("\nRunning general comparison test...")

    # Create comparator with default tolerances
    comparator = DXFGeneralComparator(position_tolerance=0.001, numeric_tolerance=1e-6)

    # Compare the files
    results = comparator.compare_files(
        "test_drawing_original.dxf", "test_drawing_modified.dxf"
    )

    # Print results
    comparator.print_results(
        results, "test_drawing_original.dxf", "test_drawing_modified.dxf"
    )


def main():
    """Run all tests"""
    print("DXF General Comparator - Test Suite")
    print("=" * 60)

    # Run main test
    run_general_comparison_test()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nTo test with command line:")
    print(
        "  python dxf_general_compare.py test_drawing_original.dxf "
        "test_drawing_modified.dxf"
    )


if __name__ == "__main__":
    main()
