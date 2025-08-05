#!/usr/bin/env python3
"""
Batch DXF Text Orientation Comparator

This script allows comparing multiple pairs of DXF files in batch mode.
Useful for comparing multiple versions or variations of drawings.
"""

import os
import sys
from pathlib import Path
from dxf_text_orientation_compare import DXFTextOrientationComparator


def find_dxf_pairs(directory: str, pattern1: str = "_old", pattern2: str = "_new"):
    """
    Find pairs of DXF files based on naming patterns

    Args:
        directory: Directory to search in
        pattern1: Pattern for first file (e.g., "_old", "_v1")
        pattern2: Pattern for second file (e.g., "_new", "_v2")

    Returns:
        List of tuples (file1_path, file2_path)
    """
    pairs = []
    dir_path = Path(directory)

    # Find all DXF files with pattern1
    files1 = list(dir_path.glob(f"*{pattern1}*.dxf"))

    for file1 in files1:
        # Look for corresponding file with pattern2
        base_name = file1.stem.replace(pattern1, pattern2)
        file2 = dir_path / f"{base_name}.dxf"

        if file2.exists():
            pairs.append((str(file1), str(file2)))

    return pairs


def batch_compare(
    directory: str,
    pattern1: str = "_old",
    pattern2: str = "_new",
    tolerance: float = 0.1,
    output_file: str = None,
):
    """
    Compare multiple pairs of DXF files in batch

    Args:
        directory: Directory containing DXF files
        pattern1: Pattern for first files
        pattern2: Pattern for second files
        tolerance: Angular tolerance in degrees
        output_file: Optional file to save results to
    """
    pairs = find_dxf_pairs(directory, pattern1, pattern2)

    if not pairs:
        print(f"No matching DXF file pairs found in '{directory}'")
        print(f"Looking for files with patterns: '{pattern1}' and '{pattern2}'")
        return

    print(f"Found {len(pairs)} DXF file pairs to compare")
    print("=" * 80)

    comparator = DXFTextOrientationComparator(tolerance=tolerance)

    # Collect all results
    all_results = []

    for i, (file1, file2) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] Comparing:")
        print(f"  File 1: {Path(file1).name}")
        print(f"  File 2: {Path(file2).name}")

        try:
            results = comparator.compare_files(file1, file2)

            # Store results with file info
            result_entry = {"file1": file1, "file2": file2, "results": results}
            all_results.append(result_entry)

            # Print summary
            changes = len(results["orientation_changes"])
            if changes > 0:
                print(f"  ⚠️  {changes} orientation changes found")
            else:
                print(f"  ✅ No orientation changes")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Print detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    output_lines = []
    total_changes = 0

    for result_entry in all_results:
        file1_name = Path(result_entry["file1"]).name
        file2_name = Path(result_entry["file2"]).name
        results = result_entry["results"]

        changes = results["orientation_changes"]
        total_changes += len(changes)

        # Add to output
        output_lines.append(f"\nComparison: {file1_name} → {file2_name}")
        output_lines.append("-" * 60)

        if not changes:
            output_lines.append("✅ No orientation changes detected")
        else:
            output_lines.append(f"⚠️  Found {len(changes)} orientation changes:")
            for j, change in enumerate(changes, 1):
                output_lines.append(
                    f"  {j}. '{change['text']}' at "
                    f"({change['position'][0]:.2f}, "
                    f"{change['position'][1]:.2f})"
                )
                output_lines.append(
                    f"     {change['old_rotation']:.1f}° → "
                    f"{change['new_rotation']:.1f}° "
                    f"(Δ{change['rotation_change']:.1f}°)"
                )

    # Print to console
    for line in output_lines:
        print(line)

    # Save to file if requested
    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write("DXF TEXT ORIENTATION BATCH COMPARISON RESULTS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Total file pairs: {len(all_results)}\n")
                f.write(f"Total orientation changes: {total_changes}\n")
                f.write(f"Angular tolerance: ±{tolerance}°\n\n")

                for line in output_lines:
                    f.write(line + "\n")

            print(f"\nResults saved to: {output_file}")
        except Exception as e:
            print(f"\nError saving results to file: {e}")

    print(f"\nBatch comparison complete:")
    print(f"  Total pairs: {len(all_results)}")
    print(f"  Total changes: {total_changes}")


def main():
    """Main function for batch comparison"""
    if len(sys.argv) < 2:
        print(
            "Usage: python batch_dxf_compare.py <directory> [pattern1] [pattern2] [tolerance]"
        )
        print()
        print("Arguments:")
        print("  directory : Directory containing DXF files")
        print("  pattern1  : Pattern for first files (default: '_old')")
        print("  pattern2  : Pattern for second files (default: '_new')")
        print("  tolerance : Angular tolerance in degrees (default: 0.1)")
        print()
        print("Examples:")
        print("  python batch_dxf_compare.py ./drawings")
        print("  python batch_dxf_compare.py ./drawings _v1 _v2")
        print("  python batch_dxf_compare.py ./drawings _old _new 0.5")
        sys.exit(1)

    directory = sys.argv[1]
    pattern1 = sys.argv[2] if len(sys.argv) > 2 else "_old"
    pattern2 = sys.argv[3] if len(sys.argv) > 3 else "_new"
    tolerance = float(sys.argv[4]) if len(sys.argv) > 4 else 0.1

    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)

    # Generate output filename
    output_file = f"batch_comparison_results_{Path(directory).name}.txt"

    try:
        batch_compare(directory, pattern1, pattern2, tolerance, output_file)
    except Exception as e:
        print(f"Error during batch comparison: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()

