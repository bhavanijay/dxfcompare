#!/usr/bin/env python3
"""
DXF General Comparator

This script compares two DXF files and detects all types of changes EXCEPT
text/label orientation changes. It identifies:
- New/deleted entities
- Geometric changes (position, size, shape)
- Property changes (color, layer, linetype)
- Text content changes (but ignores rotation)
- Block reference changes
- Dimension changes
"""

import ezdxf
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class EntityInfo:
    """Represents an entity with its properties for comparison"""

    handle: str
    entity_type: str
    layer: str
    color: int
    linetype: str
    position: Tuple[float, float, float]  # Primary position
    geometry_hash: str  # Hash of geometric properties
    properties: Dict[str, Any]  # All other properties
    text_content: Optional[str] = None  # For text entities


class DXFGeneralComparator:
    """Compare DXF files for all changes except text orientation"""

    def __init__(
        self, position_tolerance: float = 0.001, numeric_tolerance: float = 1e-6
    ):
        """
        Initialize the comparator

        Args:
            position_tolerance: Tolerance for position comparisons
            numeric_tolerance: Tolerance for numeric property comparisons
        """
        self.position_tolerance = position_tolerance
        self.numeric_tolerance = numeric_tolerance

    def get_entity_position(self, entity) -> Tuple[float, float, float]:
        """Extract primary position from an entity"""
        try:
            if hasattr(entity.dxf, "insert"):
                # TEXT, MTEXT, INSERT, etc.
                insert = entity.dxf.insert
                return (insert.x, insert.y, insert.z)
            elif hasattr(entity.dxf, "start"):
                # LINE
                start = entity.dxf.start
                return (start.x, start.y, start.z)
            elif hasattr(entity.dxf, "center"):
                # CIRCLE, ARC
                center = entity.dxf.center
                return (center.x, center.y, center.z)
            elif hasattr(entity.dxf, "location"):
                # POINT
                location = entity.dxf.location
                return (location.x, location.y, location.z)
            elif entity.dxftype() == "LWPOLYLINE":
                # LWPOLYLINE - use first vertex
                if entity.vertices:
                    vertex = entity.vertices[0]
                    return (vertex[0], vertex[1], 0.0)
            elif entity.dxftype() == "POLYLINE":
                # POLYLINE - use first vertex
                vertices = list(entity.vertices)
                if vertices:
                    v = vertices[0]
                    return (v.dxf.location.x, v.dxf.location.y, v.dxf.location.z)
            elif entity.dxftype() == "SPLINE":
                # SPLINE - use first control point
                if entity.control_points:
                    cp = entity.control_points[0]
                    return (cp.x, cp.y, cp.z)
            elif hasattr(entity.dxf, "defpoint"):
                # DIMENSION
                defpoint = entity.dxf.defpoint
                return (defpoint.x, defpoint.y, defpoint.z)
        except Exception:
            pass

        return (0.0, 0.0, 0.0)

    def get_geometry_hash(self, entity) -> str:
        """Generate a hash of geometric properties (excluding position)"""
        geometry_props = []

        try:
            entity_type = entity.dxftype()
            geometry_props.append(entity_type)

            if entity_type == "LINE":
                # For lines, include end point relative to start
                start = entity.dxf.start
                end = entity.dxf.end
                rel_end = (end.x - start.x, end.y - start.y, end.z - start.z)
                geometry_props.append(f"end:{rel_end}")

            elif entity_type == "CIRCLE":
                geometry_props.append(f"radius:{entity.dxf.radius}")

            elif entity_type == "ARC":
                geometry_props.append(f"radius:{entity.dxf.radius}")
                geometry_props.append(f"start_angle:{entity.dxf.start_angle}")
                geometry_props.append(f"end_angle:{entity.dxf.end_angle}")

            elif entity_type == "ELLIPSE":
                major_axis = entity.dxf.major_axis
                geometry_props.append(
                    f"major_axis:({major_axis.x},{major_axis.y},{major_axis.z})"
                )
                geometry_props.append(f"ratio:{entity.dxf.ratio}")
                geometry_props.append(f"start_param:{entity.dxf.start_param}")
                geometry_props.append(f"end_param:{entity.dxf.end_param}")

            elif entity_type in ["TEXT", "MTEXT"]:
                # For text, include size and style but NOT rotation
                if hasattr(entity.dxf, "height"):
                    geometry_props.append(f"height:{entity.dxf.height}")
                if hasattr(entity.dxf, "char_height"):
                    geometry_props.append(f"char_height:{entity.dxf.char_height}")
                if hasattr(entity.dxf, "style"):
                    geometry_props.append(f"style:{entity.dxf.style}")
                if hasattr(entity.dxf, "width"):
                    geometry_props.append(f"width:{entity.dxf.width}")

            elif entity_type == "LWPOLYLINE":
                # Include all vertices
                for i, vertex in enumerate(entity.vertices):
                    geometry_props.append(f"v{i}:({vertex[0]},{vertex[1]})")
                    if len(vertex) > 4:  # Has bulge
                        geometry_props.append(f"b{i}:{vertex[4]}")
                geometry_props.append(f"closed:{entity.closed}")

            elif entity_type == "POLYLINE":
                vertices = list(entity.vertices)
                for i, vertex in enumerate(vertices):
                    loc = vertex.dxf.location
                    geometry_props.append(f"v{i}:({loc.x},{loc.y},{loc.z})")
                    if hasattr(vertex.dxf, "bulge"):
                        geometry_props.append(f"b{i}:{vertex.dxf.bulge}")
                geometry_props.append(f"closed:{entity.is_closed}")

            elif entity_type == "INSERT":
                geometry_props.append(f"name:{entity.dxf.name}")
                if hasattr(entity.dxf, "xscale"):
                    geometry_props.append(f"xscale:{entity.dxf.xscale}")
                if hasattr(entity.dxf, "yscale"):
                    geometry_props.append(f"yscale:{entity.dxf.yscale}")
                if hasattr(entity.dxf, "zscale"):
                    geometry_props.append(f"zscale:{entity.dxf.zscale}")
                # Note: rotation is excluded for blocks as it's considered orientation

            elif entity_type == "HATCH":
                # Include boundary paths and pattern
                geometry_props.append(
                    f"pattern:{getattr(entity.dxf, 'pattern_name', '')}"
                )
                geometry_props.append(f"solid:{entity.dxf.solid_fill}")

            elif entity_type.startswith("DIMENSION"):
                # Include dimension-specific properties
                if hasattr(entity.dxf, "text"):
                    geometry_props.append(f"dim_text:{entity.dxf.text}")
                if hasattr(entity.dxf, "dimstyle"):
                    geometry_props.append(f"dimstyle:{entity.dxf.dimstyle}")

        except Exception as e:
            geometry_props.append(f"error:{str(e)}")

        return "|".join(sorted(geometry_props))

    def get_entity_properties(self, entity) -> Dict[str, Any]:
        """Extract all properties from an entity"""
        props = {}

        try:
            # Basic properties
            props["layer"] = getattr(entity.dxf, "layer", "0")
            props["color"] = getattr(entity.dxf, "color", 256)
            props["linetype"] = getattr(entity.dxf, "linetype", "ByLayer")
            props["lineweight"] = getattr(entity.dxf, "lineweight", -1)

            # Entity-specific properties
            entity_type = entity.dxftype()

            if entity_type in ["TEXT", "MTEXT"]:
                # Text content but NOT rotation
                if entity_type == "TEXT":
                    props["text"] = entity.dxf.text
                    props["height"] = getattr(entity.dxf, "height", 0)
                else:  # MTEXT
                    props["text"] = entity.text
                    props["char_height"] = getattr(entity.dxf, "char_height", 0)
                    props["width"] = getattr(entity.dxf, "width", 0)
                    props["attachment_point"] = getattr(
                        entity.dxf, "attachment_point", 1
                    )

                props["style"] = getattr(entity.dxf, "style", "Standard")
                # Explicitly exclude rotation

            elif entity_type == "LINE":
                props["thickness"] = getattr(entity.dxf, "thickness", 0)

            elif entity_type in ["CIRCLE", "ARC"]:
                props["thickness"] = getattr(entity.dxf, "thickness", 0)

            elif entity_type == "INSERT":
                props["name"] = entity.dxf.name
                props["xscale"] = getattr(entity.dxf, "xscale", 1.0)
                props["yscale"] = getattr(entity.dxf, "yscale", 1.0)
                props["zscale"] = getattr(entity.dxf, "zscale", 1.0)
                # Exclude rotation for blocks

        except Exception:
            pass

        return props

    def extract_entity_info(self, dxf_path: str) -> List[EntityInfo]:
        """Extract entity information from a DXF file"""
        try:
            doc = ezdxf.readfile(dxf_path)
        except IOError:
            print(f"Error: Cannot read DXF file '{dxf_path}'")
            return []
        except ezdxf.DXFStructureError:
            print(f"Error: Invalid DXF file structure in '{dxf_path}'")
            return []

        entities = []

        # Process all layouts
        spaces = [doc.modelspace()]
        for layout_name in doc.layout_names():
            if layout_name.lower() != "model":
                try:
                    spaces.append(doc.layout(layout_name))
                except:
                    continue

        for space in spaces:
            for entity in space:
                try:
                    entity_info = EntityInfo(
                        handle=entity.dxf.handle,
                        entity_type=entity.dxftype(),
                        layer=getattr(entity.dxf, "layer", "0"),
                        color=getattr(entity.dxf, "color", 256),
                        linetype=getattr(entity.dxf, "linetype", "ByLayer"),
                        position=self.get_entity_position(entity),
                        geometry_hash=self.get_geometry_hash(entity),
                        properties=self.get_entity_properties(entity),
                    )

                    # Add text content for text entities
                    if entity.dxftype() == "TEXT":
                        entity_info.text_content = entity.dxf.text
                    elif entity.dxftype() == "MTEXT":
                        entity_info.text_content = entity.text

                    entities.append(entity_info)

                except Exception as e:
                    print(
                        f"Warning: Error processing entity {getattr(entity.dxf, 'handle', 'unknown')}: {e}"
                    )
                    continue

        return entities

    def find_matching_entity(
        self, entity: EntityInfo, entity_list: List[EntityInfo]
    ) -> Optional[EntityInfo]:
        """Find a matching entity based on type, position, and geometry"""
        candidates = []

        # First pass: exact type and similar position
        for candidate in entity_list:
            if candidate.entity_type != entity.entity_type:
                continue

            # Check position similarity
            pos_diff = math.sqrt(
                (candidate.position[0] - entity.position[0]) ** 2
                + (candidate.position[1] - entity.position[1]) ** 2
                + (candidate.position[2] - entity.position[2]) ** 2
            )

            if pos_diff <= self.position_tolerance:
                candidates.append((candidate, pos_diff))

        if not candidates:
            return None

        # Sort by position difference and geometry similarity
        candidates.sort(key=lambda x: x[1])

        # Return the closest match
        return candidates[0][0]

    def compare_entities(self, entity1: EntityInfo, entity2: EntityInfo) -> List[str]:
        """Compare two entities and return list of differences"""
        differences = []

        # Check geometry changes
        if entity1.geometry_hash != entity2.geometry_hash:
            differences.append("geometry_changed")

        # Check property changes
        for prop, value1 in entity1.properties.items():
            if prop in entity2.properties:
                value2 = entity2.properties[prop]

                # Special handling for text content
                if prop == "text" and entity1.text_content != entity2.text_content:
                    differences.append(f"text_content_changed")
                elif prop != "text":  # Skip text content comparison here
                    if isinstance(value1, (int, float)) and isinstance(
                        value2, (int, float)
                    ):
                        if abs(value1 - value2) > self.numeric_tolerance:
                            differences.append(f"{prop}_changed")
                    elif value1 != value2:
                        differences.append(f"{prop}_changed")
            else:
                differences.append(f"{prop}_removed")

        # Check for new properties
        for prop in entity2.properties:
            if prop not in entity1.properties:
                differences.append(f"{prop}_added")

        # Check basic property changes
        if entity1.layer != entity2.layer:
            differences.append("layer_changed")
        if entity1.color != entity2.color:
            differences.append("color_changed")
        if entity1.linetype != entity2.linetype:
            differences.append("linetype_changed")

        return differences

    def compare_files(self, file1_path: str, file2_path: str) -> Dict:
        """Compare two DXF files and return comprehensive results"""
        print(f"Extracting entities from '{file1_path}'...")
        entities1 = self.extract_entity_info(file1_path)

        print(f"Extracting entities from '{file2_path}'...")
        entities2 = self.extract_entity_info(file2_path)

        print(f"Found {len(entities1)} entities in file 1")
        print(f"Found {len(entities2)} entities in file 2")

        # Results containers
        modified_entities = []
        deleted_entities = []
        new_entities = []

        # Track matched entities in file2
        matched_handles = set()

        # Compare entities from file1 with file2
        for entity1 in entities1:
            matching_entity2 = self.find_matching_entity(entity1, entities2)

            if matching_entity2 is None:
                # Entity was deleted
                deleted_entities.append(
                    {
                        "handle": entity1.handle,
                        "type": entity1.entity_type,
                        "position": entity1.position,
                        "layer": entity1.layer,
                        "text_content": entity1.text_content,
                    }
                )
            else:
                matched_handles.add(matching_entity2.handle)

                # Check for modifications
                differences = self.compare_entities(entity1, matching_entity2)

                if differences:
                    modified_entities.append(
                        {
                            "handle1": entity1.handle,
                            "handle2": matching_entity2.handle,
                            "type": entity1.entity_type,
                            "position": entity1.position,
                            "layer": entity1.layer,
                            "changes": differences,
                            "text_content": entity1.text_content,
                        }
                    )

        # Find new entities in file2
        for entity2 in entities2:
            if entity2.handle not in matched_handles:
                new_entities.append(
                    {
                        "handle": entity2.handle,
                        "type": entity2.entity_type,
                        "position": entity2.position,
                        "layer": entity2.layer,
                        "text_content": entity2.text_content,
                    }
                )

        return {
            "modified_entities": modified_entities,
            "deleted_entities": deleted_entities,
            "new_entities": new_entities,
            "total_entities_file1": len(entities1),
            "total_entities_file2": len(entities2),
        }

    def print_results(self, results: Dict, file1_name: str, file2_name: str):
        """Print comparison results in a formatted way"""
        print("\n" + "=" * 80)
        print(f"DXF GENERAL COMPARISON RESULTS")
        print("=" * 80)
        print(f"File 1: {file1_name}")
        print(f"File 2: {file2_name}")
        print(f"Position tolerance: {self.position_tolerance}")
        print(f"Numeric tolerance: {self.numeric_tolerance}")
        print("-" * 80)

        modified = results["modified_entities"]
        deleted = results["deleted_entities"]
        new = results["new_entities"]

        total_changes = len(modified) + len(deleted) + len(new)

        if total_changes == 0:
            print("✅ NO CHANGES DETECTED (excluding text orientation)")
        else:
            print(f"⚠️  FOUND {total_changes} TOTAL CHANGES:")
            print()

            # Modified entities
            if modified:
                print(f"🔄 MODIFIED ENTITIES ({len(modified)}):")
                for i, mod in enumerate(modified[:10], 1):  # Show first 10
                    print(f"{i}. {mod['type']} on layer '{mod['layer']}'")
                    print(
                        f"   Position: ({mod['position'][0]:.3f}, {mod['position'][1]:.3f}, {mod['position'][2]:.3f})"
                    )
                    if mod["text_content"]:
                        print(f"   Text: '{mod['text_content']}'")
                    print(f"   Changes: {', '.join(mod['changes'])}")
                    print(f"   Handles: {mod['handle1']} → {mod['handle2']}")
                    print()
                if len(modified) > 10:
                    print(f"   ... and {len(modified) - 10} more modified entities")
                print()

            # Deleted entities
            if deleted:
                print(f"❌ DELETED ENTITIES ({len(deleted)}):")
                for i, del_ent in enumerate(deleted[:10], 1):  # Show first 10
                    print(f"{i}. {del_ent['type']} on layer '{del_ent['layer']}'")
                    print(
                        f"   Position: ({del_ent['position'][0]:.3f}, {del_ent['position'][1]:.3f}, {del_ent['position'][2]:.3f})"
                    )
                    if del_ent["text_content"]:
                        print(f"   Text: '{del_ent['text_content']}'")
                    print(f"   Handle: {del_ent['handle']}")
                    print()
                if len(deleted) > 10:
                    print(f"   ... and {len(deleted) - 10} more deleted entities")
                print()

            # New entities
            if new:
                print(f"➕ NEW ENTITIES ({len(new)}):")
                for i, new_ent in enumerate(new[:10], 1):  # Show first 10
                    print(f"{i}. {new_ent['type']} on layer '{new_ent['layer']}'")
                    print(
                        f"   Position: ({new_ent['position'][0]:.3f}, {new_ent['position'][1]:.3f}, {new_ent['position'][2]:.3f})"
                    )
                    if new_ent["text_content"]:
                        print(f"   Text: '{new_ent['text_content']}'")
                    print(f"   Handle: {new_ent['handle']}")
                    print()
                if len(new) > 10:
                    print(f"   ... and {len(new) - 10} more new entities")
                print()

        print(
            f"Summary: {results['total_entities_file1']} entities in file 1, "
            f"{results['total_entities_file2']} entities in file 2"
        )
        print("=" * 80)


def main():
    """Main function to run the comparison"""
    if len(sys.argv) not in [3, 4, 5]:
        print(
            "Usage: python dxf_general_compare.py <file1.dxf> <file2.dxf> [pos_tolerance] [num_tolerance]"
        )
        print()
        print("Arguments:")
        print("  file1.dxf      : First DXF file to compare")
        print("  file2.dxf      : Second DXF file to compare")
        print("  pos_tolerance  : Position tolerance (default: 0.001)")
        print("  num_tolerance  : Numeric tolerance (default: 1e-6)")
        print()
        print("Example:")
        print("  python dxf_general_compare.py drawing_old.dxf drawing_new.dxf")
        print(
            "  python dxf_general_compare.py drawing_old.dxf drawing_new.dxf 0.01 1e-5"
        )
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    pos_tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 0.001
    num_tolerance = float(sys.argv[4]) if len(sys.argv) > 4 else 1e-6

    # Check if files exist
    if not Path(file1_path).exists():
        print(f"Error: File '{file1_path}' does not exist")
        sys.exit(1)

    if not Path(file2_path).exists():
        print(f"Error: File '{file2_path}' does not exist")
        sys.exit(1)

    # Create comparator
    comparator = DXFGeneralComparator(
        position_tolerance=pos_tolerance, numeric_tolerance=num_tolerance
    )

    try:
        # Compare the files
        results = comparator.compare_files(file1_path, file2_path)

        # Print results
        comparator.print_results(results, file1_path, file2_path)

        # Exit with appropriate code
        total_changes = (
            len(results["modified_entities"])
            + len(results["deleted_entities"])
            + len(results["new_entities"])
        )

        if total_changes > 0:
            sys.exit(1)  # Changes found
        else:
            sys.exit(0)  # No changes

    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
