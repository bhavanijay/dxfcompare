#!/usr/bin/env python3
"""
DXF Text Orientation Comparator

This script compares two DXF files and flags changes in text label orientations.
It extracts text entities from both files and compares their rotation angles,
reporting any differences found.
"""

import ezdxf
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TextEntity:
    """Represents a text entity with its properties"""

    text: str
    x: float
    y: float
    z: float
    rotation: float  # in degrees
    height: float
    layer: str
    handle: str
    style: Optional[str] = None


class DXFTextOrientationComparator:
    """Compare text orientations between two DXF files"""

    def __init__(self, tolerance: float = 0.1):
        """
        Initialize the comparator

        Args:
            tolerance: Angular tolerance in degrees for considering rotations as equal
        """
        self.tolerance = tolerance

    def extract_text_entities(self, dxf_path: str) -> List[TextEntity]:
        """
        Extract all text entities from a DXF file

        Args:
            dxf_path: Path to the DXF file

        Returns:
            List of TextEntity objects
        """
        try:
            doc = ezdxf.readfile(dxf_path)
        except IOError:
            print(f"Error: Cannot read DXF file '{dxf_path}'")
            return []
        except ezdxf.DXFStructureError:
            print(f"Error: Invalid DXF file structure in '{dxf_path}'")
            return []

        text_entities = []

        # Iterate through all entities in modelspace and paperspace
        spaces = [doc.modelspace()]

        # Add all paper space layouts
        for layout_name in doc.layout_names():
            if layout_name.lower() != "model":
                try:
                    spaces.append(doc.layout(layout_name))
                except:
                    continue

        for space in spaces:
            # Extract TEXT entities
            for entity in space.query("TEXT"):
                text_entity = TextEntity(
                    text=entity.dxf.text,
                    x=entity.dxf.insert.x,
                    y=entity.dxf.insert.y,
                    z=entity.dxf.insert.z,
                    rotation=math.degrees(entity.dxf.rotation),
                    height=entity.dxf.height,
                    layer=entity.dxf.layer,
                    handle=entity.dxf.handle,
                    style=getattr(entity.dxf, "style", None),
                )
                text_entities.append(text_entity)

            # Extract MTEXT entities
            for entity in space.query("MTEXT"):
                # MTEXT rotation might be stored differently
                rotation = 0.0
                if hasattr(entity.dxf, "rotation"):
                    rotation = math.degrees(entity.dxf.rotation)

                text_entity = TextEntity(
                    text=entity.text,
                    x=entity.dxf.insert.x,
                    y=entity.dxf.insert.y,
                    z=entity.dxf.insert.z,
                    rotation=rotation,
                    height=entity.dxf.char_height,
                    layer=entity.dxf.layer,
                    handle=entity.dxf.handle,
                    style=getattr(entity.dxf, "style", None),
                )
                text_entities.append(text_entity)

        return text_entities

    def normalize_rotation(self, rotation: float) -> float:
        """
        Normalize rotation angle to [0, 360) range

        Args:
            rotation: Rotation angle in degrees

        Returns:
            Normalized rotation angle
        """
        while rotation < 0:
            rotation += 360
        while rotation >= 360:
            rotation -= 360
        return rotation

    def are_rotations_equal(self, rot1: float, rot2: float) -> bool:
        """
        Check if two rotation angles are equal within tolerance

        Args:
            rot1, rot2: Rotation angles in degrees

        Returns:
            True if rotations are considered equal
        """
        rot1 = self.normalize_rotation(rot1)
        rot2 = self.normalize_rotation(rot2)

        # Check direct difference
        diff = abs(rot1 - rot2)

        # Also check wrapped difference (e.g., 359° vs 1°)
        wrapped_diff = min(diff, 360 - diff)

        return wrapped_diff <= self.tolerance

    def find_matching_text(
        self,
        text_entity: TextEntity,
        text_list: List[TextEntity],
        position_tolerance: float = 0.01,
    ) -> Optional[TextEntity]:
        """
        Find a matching text entity in another list based on position and content

        Args:
            text_entity: Text entity to find match for
            text_list: List to search in
            position_tolerance: Tolerance for position matching

        Returns:
            Matching TextEntity or None if not found
        """
        for candidate in text_list:
            # Check if text content matches
            if candidate.text.strip() != text_entity.text.strip():
                continue

            # Check if position matches within tolerance
            pos_diff = math.sqrt(
                (candidate.x - text_entity.x) ** 2
                + (candidate.y - text_entity.y) ** 2
                + (candidate.z - text_entity.z) ** 2
            )

            if pos_diff <= position_tolerance:
                return candidate

        return None

    def compare_files(self, file1_path: str, file2_path: str) -> Dict:
        """
        Compare text orientations between two DXF files

        Args:
            file1_path: Path to first DXF file
            file2_path: Path to second DXF file

        Returns:
            Dictionary containing comparison results
        """
        print(f"Extracting text entities from '{file1_path}'...")
        texts1 = self.extract_text_entities(file1_path)

        print(f"Extracting text entities from '{file2_path}'...")
        texts2 = self.extract_text_entities(file2_path)

        print(f"Found {len(texts1)} text entities in file 1")
        print(f"Found {len(texts2)} text entities in file 2")

        orientation_changes = []
        missing_in_file2 = []
        new_in_file2 = []

        # Track which entities in file2 have been matched
        matched_in_file2 = set()

        # Compare each text entity from file1 with file2
        for text1 in texts1:
            matching_text2 = self.find_matching_text(text1, texts2)

            if matching_text2 is None:
                missing_in_file2.append(text1)
            else:
                matched_in_file2.add(matching_text2.handle)

                # Check if orientation changed
                if not self.are_rotations_equal(
                    text1.rotation, matching_text2.rotation
                ):
                    orientation_changes.append(
                        {
                            "text": text1.text,
                            "position": (text1.x, text1.y, text1.z),
                            "layer": text1.layer,
                            "old_rotation": text1.rotation,
                            "new_rotation": matching_text2.rotation,
                            "rotation_change": matching_text2.rotation - text1.rotation,
                            "handle1": text1.handle,
                            "handle2": matching_text2.handle,
                        }
                    )

        # Find new text entities in file2
        for text2 in texts2:
            if text2.handle not in matched_in_file2:
                new_in_file2.append(text2)

        return {
            "orientation_changes": orientation_changes,
            "missing_in_file2": missing_in_file2,
            "new_in_file2": new_in_file2,
            "total_texts_file1": len(texts1),
            "total_texts_file2": len(texts2),
        }

    def print_results(self, results: Dict, file1_name: str, file2_name: str):
        """
        Print comparison results in a formatted way

        Args:
            results: Results dictionary from compare_files
            file1_name: Name of first file
            file2_name: Name of second file
        """
        print("\n" + "=" * 80)
        print(f"DXF TEXT ORIENTATION COMPARISON RESULTS")
        print("=" * 80)
        print(f"File 1: {file1_name}")
        print(f"File 2: {file2_name}")
        print(f"Angular tolerance: ±{self.tolerance}°")
        print("-" * 80)

        orientation_changes = results["orientation_changes"]

        if not orientation_changes:
            print("✅ NO TEXT ORIENTATION CHANGES DETECTED")
        else:
            print(f"⚠️  FOUND {len(orientation_changes)} TEXT ORIENTATION CHANGES:")
            print()

            for i, change in enumerate(orientation_changes, 1):
                print(f"{i}. Text: '{change['text']}'")
                print(
                    f"   Position: ({change['position'][0]:.3f}, {change['position'][1]:.3f}, {change['position'][2]:.3f})"
                )
                print(f"   Layer: {change['layer']}")
                print(f"   Old rotation: {change['old_rotation']:.2f}°")
                print(f"   New rotation: {change['new_rotation']:.2f}°")
                print(f"   Change: {change['rotation_change']:.2f}°")
                print(f"   Handles: {change['handle1']} → {change['handle2']}")
                print()

        # Report missing and new texts
        missing = results["missing_in_file2"]
        new = results["new_in_file2"]

        if missing:
            print(f"📋 {len(missing)} text entities missing in file 2:")
            for text in missing[:5]:  # Show first 5
                print(f"   - '{text.text}' at ({text.x:.3f}, {text.y:.3f})")
            if len(missing) > 5:
                print(f"   ... and {len(missing) - 5} more")
            print()

        if new:
            print(f"📋 {len(new)} new text entities in file 2:")
            for text in new[:5]:  # Show first 5
                print(f"   + '{text.text}' at ({text.x:.3f}, {text.y:.3f})")
            if len(new) > 5:
                print(f"   ... and {len(new) - 5} more")
            print()

        print(
            f"Summary: {results['total_texts_file1']} texts in file 1, "
            f"{results['total_texts_file2']} texts in file 2"
        )
        print("=" * 80)


def main():
    """Main function to run the comparison"""
    if len(sys.argv) != 3:
        print("Usage: python dxf_text_orientation_compare.py <file1.dxf> <file2.dxf>")
        print()
        print("Example:")
        print(
            "  python dxf_text_orientation_compare.py drawing_old.dxf drawing_new.dxf"
        )
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    # Check if files exist
    if not Path(file1_path).exists():
        print(f"Error: File '{file1_path}' does not exist")
        sys.exit(1)

    if not Path(file2_path).exists():
        print(f"Error: File '{file2_path}' does not exist")
        sys.exit(1)

    # Create comparator with 0.1 degree tolerance
    comparator = DXFTextOrientationComparator(tolerance=0.1)

    try:
        # Compare the files
        results = comparator.compare_files(file1_path, file2_path)

        # Print results
        comparator.print_results(results, file1_path, file2_path)

        # Exit with appropriate code
        if results["orientation_changes"]:
            sys.exit(1)  # Changes found
        else:
            sys.exit(0)  # No changes

    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
