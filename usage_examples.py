#!/usr/bin/env python3
"""
Usage examples for DXF Text Orientation Comparator

This script demonstrates different ways to use the DXF comparison tools.
"""

import sys
from pathlib import Path
from dxf_text_orientation_compare import DXFTextOrientationComparator


def example_basic_comparison():
    """Example of basic file comparison"""
    print("=== EXAMPLE 1: Basic Text Orientation Comparison ===")

    # Create a comparator with default tolerance (0.1 degrees)
    comparator = DXFTextOrientationComparator()

    # Compare the sample files created by the test script
    file1 = "sample_drawing_v1.dxf"
    file2 = "sample_drawing_v2.dxf"

    if not (Path(file1).exists() and Path(file2).exists()):
        print("Sample files not found. Run test_dxf_compare.py first.")
        return

    try:
        results = comparator.compare_files(file1, file2)
        comparator.print_results(results, file1, file2)

        # Access specific results
        print(f"\nDetailed Analysis:")
        print(f"- Changes found: {len(results['orientation_changes'])}")
        print(f"- Missing texts: {len(results['missing_in_file2'])}")
        print(f"- New texts: {len(results['new_in_file2'])}")

    except Exception as e:
        print(f"Error: {e}")


def example_custom_tolerance():
    """Example with custom angular tolerance"""
    print("\n=== EXAMPLE 2: Custom Angular Tolerance ===")

    # Create comparator with higher tolerance (1 degree)
    comparator = DXFTextOrientationComparator(tolerance=1.0)

    file1 = "sample_drawing_v1.dxf"
    file2 = "sample_drawing_v2.dxf"

    if not (Path(file1).exists() and Path(file2).exists()):
        print("Sample files not found. Run test_dxf_compare.py first.")
        return

    try:
        results = comparator.compare_files(file1, file2)

        print(f"With 1.0° tolerance:")
        print(f"- Changes found: {len(results['orientation_changes'])}")

        # Compare with default tolerance
        strict_comparator = DXFTextOrientationComparator(tolerance=0.1)
        strict_results = strict_comparator.compare_files(file1, file2)

        print(f"With 0.1° tolerance:")
        print(f"- Changes found: {len(strict_results['orientation_changes'])}")

    except Exception as e:
        print(f"Error: {e}")


def example_programmatic_usage():
    """Example of using the comparator programmatically"""
    print("\n=== EXAMPLE 3: Programmatic Usage ===")

    comparator = DXFTextOrientationComparator(tolerance=0.1)

    file1 = "sample_drawing_v1.dxf"
    file2 = "sample_drawing_v2.dxf"

    if not (Path(file1).exists() and Path(file2).exists()):
        print("Sample files not found. Run test_dxf_compare.py first.")
        return

    try:
        results = comparator.compare_files(file1, file2)

        # Process results programmatically
        for change in results["orientation_changes"]:
            print(f"Text '{change['text']}' changed orientation:")
            print(f"  From: {change['old_rotation']:.1f}°")
            print(f"  To: {change['new_rotation']:.1f}°")
            print(f"  Difference: {change['rotation_change']:.1f}°")
            print(
                f"  Location: ({change['position'][0]:.1f}, "
                f"{change['position'][1]:.1f})"
            )
            print()

        # Check if any significant changes (> 10 degrees)
        significant_changes = [
            change
            for change in results["orientation_changes"]
            if abs(change["rotation_change"]) > 10
        ]

        if significant_changes:
            print(f"Found {len(significant_changes)} significant changes (>10°)")
        else:
            print("No significant orientation changes found")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples"""
    print("DXF Text Orientation Comparator - Usage Examples")
    print("=" * 60)

    # Run examples
    example_basic_comparison()
    example_custom_tolerance()
    example_programmatic_usage()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nFor command-line usage:")
    print("  python dxf_text_orientation_compare.py file1.dxf file2.dxf")
    print("\nFor batch processing:")
    print("  python batch_dxf_compare.py ./directory_with_dxf_files")


if __name__ == "__main__":
    main()
