#!/usr/bin/env python3
"""
DXF Comprehensive Comparator (Excluding Text Orientation Changes)

This script compares two DXF files and flags ALL changes EXCEPT text/label 
orientation changes. It detects geometry changes, property modifications, 
new/deleted entities, and other structural differences while ignoring 
text rotation changes.
"""

import ezdxf
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class EntityInfo:
    """Represents a DXF entity with its properties"""
    handle: str
    entity_type: str
    layer: str
    color: int
    linetype: str
    position: Tuple[float, float, float]
    properties: Dict[str, Any]
    geometry_hash: str


class DXFComprehensiveComparator:
    """Compare all aspects of DXF files except text orientation"""
    
    def __init__(self, 
                 position_tolerance: float = 0.001,
                 numeric_tolerance: float = 1e-6,
                 ignore_handles: bool = True):
        """
        Initialize the comprehensive comparator
        
        Args:
            position_tolerance: Tolerance for position comparisons
            numeric_tolerance: Tolerance for numeric value comparisons
            ignore_handles: Whether to ignore entity handle differences
        """
        self.position_tolerance = position_tolerance
        self.numeric_tolerance = numeric_tolerance
        self.ignore_handles = ignore_handles
        
    def extract_entity_info(self, dxf_path: str) -> Dict[str, EntityInfo]:
        """
        Extract all entity information from a DXF file
        
        Args:
            dxf_path: Path to the DXF file
            
        Returns:
            Dictionary mapping entity signatures to EntityInfo objects
        """
        try:
            doc = ezdxf.readfile(dxf_path)
        except IOError:
            print(f"Error: Cannot read DXF file '{dxf_path}'")
            return {}
        except ezdxf.DXFStructureError:
            print(f"Error: Invalid DXF file structure in '{dxf_path}'")
            return {}
        
        entities = {}
        
        # Process all spaces (model space and paper spaces)
        spaces = [doc.modelspace()]
        for layout_name in doc.layout_names():
            if layout_name.lower() != 'model':
                try:
                    spaces.append(doc.layout(layout_name))
                except:
                    continue
        
        for space in spaces:
            for entity in space:
                entity_info = self._extract_single_entity_info(entity)
                if entity_info:
                    # Create a signature that excludes text rotation for matching
                    signature = self._create_entity_signature(entity_info)
                    entities[signature] = entity_info
        
        return entities
    
    def _extract_single_entity_info(self, entity) -> Optional[EntityInfo]:
        """Extract information from a single entity"""
        try:
            # Get basic properties
            handle = entity.dxf.handle
            entity_type = entity.dxftype()
            layer = getattr(entity.dxf, 'layer', '0')
            color = getattr(entity.dxf, 'color', 256)
            linetype = getattr(entity.dxf, 'linetype', 'BYLAYER')
            
            # Get position and properties based on entity type
            position, properties = self._get_entity_specifics(entity)
            
            # Create geometry hash (excluding text rotation)
            geometry_hash = self._create_geometry_hash(entity, properties)
            
            return EntityInfo(
                handle=handle,
                entity_type=entity_type,
                layer=layer,
                color=color,
                linetype=linetype,
                position=position,
                properties=properties,
                geometry_hash=geometry_hash
            )
        except Exception as e:
            print(f"Warning: Could not process entity {entity.dxftype()}: {e}")
            return None
    
    def _get_entity_specifics(self, entity) -> Tuple[Tuple[float, float, float], Dict[str, Any]]:
        """Get entity-specific position and properties"""
        entity_type = entity.dxftype()
        properties = {}
        position = (0.0, 0.0, 0.0)
        
        try:
            if entity_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                position = (start.x, start.y, start.z)
                properties = {
                    'start': (start.x, start.y, start.z),
                    'end': (end.x, end.y, end.z)
                }
                
            elif entity_type == 'CIRCLE':
                center = entity.dxf.center
                position = (center.x, center.y, center.z)
                properties = {
                    'center': (center.x, center.y, center.z),
                    'radius': entity.dxf.radius
                }
                
            elif entity_type == 'ARC':
                center = entity.dxf.center
                position = (center.x, center.y, center.z)
                properties = {
                    'center': (center.x, center.y, center.z),
                    'radius': entity.dxf.radius,
                    'start_angle': entity.dxf.start_angle,
                    'end_angle': entity.dxf.end_angle
                }
                
            elif entity_type in ['TEXT', 'MTEXT']:
                insert = entity.dxf.insert
                position = (insert.x, insert.y, insert.z)
                properties = {
                    'text': entity.dxf.text if entity_type == 'TEXT' else entity.text,
                    'height': entity.dxf.height if entity_type == 'TEXT' else entity.dxf.char_height,
                    'insert': (insert.x, insert.y, insert.z),
                    # NOTE: Deliberately exclude rotation for text entities
                    'style': getattr(entity.dxf, 'style', None)
                }
                
            elif entity_type == 'LWPOLYLINE':
                points = list(entity.get_points())
                if points:
                    position = (points[0][0], points[0][1], 0.0)
                properties = {
                    'points': points,
                    'closed': entity.closed,
                    'elevation': getattr(entity.dxf, 'elevation', 0.0)
                }
                
            elif entity_type == 'POLYLINE':
                vertices = list(entity.vertices)
                if vertices:
                    first_vertex = vertices[0]
                    pos = first_vertex.dxf.location
                    position = (pos.x, pos.y, pos.z)
                properties = {
                    'vertices': [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) 
                               for v in vertices],
                    'closed': entity.is_closed
                }
                
            elif entity_type == 'ELLIPSE':
                center = entity.dxf.center
                position = (center.x, center.y, center.z)
                properties = {
                    'center': (center.x, center.y, center.z),
                    'major_axis': (entity.dxf.major_axis.x, entity.dxf.major_axis.y, entity.dxf.major_axis.z),
                    'ratio': entity.dxf.ratio,
                    'start_param': getattr(entity.dxf, 'start_param', 0.0),
                    'end_param': getattr(entity.dxf, 'end_param', 2 * math.pi)
                }
                
            elif entity_type == 'SPLINE':
                if hasattr(entity, 'control_points') and entity.control_points:
                    first_point = entity.control_points[0]
                    position = (first_point.x, first_point.y, first_point.z)
                properties = {
                    'degree': entity.dxf.degree,
                    'control_points': [(p.x, p.y, p.z) for p in entity.control_points] if entity.control_points else [],
                    'knots': list(entity.knots) if entity.knots else [],
                    'weights': list(entity.weights) if entity.weights else []
                }
                
            elif entity_type == 'INSERT':
                insert = entity.dxf.insert
                position = (insert.x, insert.y, insert.z)
                properties = {
                    'name': entity.dxf.name,
                    'insert': (insert.x, insert.y, insert.z),
                    'xscale': getattr(entity.dxf, 'xscale', 1.0),
                    'yscale': getattr(entity.dxf, 'yscale', 1.0),
                    'zscale': getattr(entity.dxf, 'zscale', 1.0),
                    'rotation': getattr(entity.dxf, 'rotation', 0.0)
                }
                
            elif entity_type == 'DIMENSION':
                defpoint = getattr(entity.dxf, 'defpoint', (0, 0, 0))
                position = (defpoint[0], defpoint[1], defpoint[2])
                properties = {
                    'defpoint': defpoint,
                    'text': getattr(entity.dxf, 'text', ''),
                    'dimstyle': getattr(entity.dxf, 'dimstyle', 'STANDARD')
                }
                
            else:
                # Generic handling for other entity types
                if hasattr(entity.dxf, 'insert'):
                    insert = entity.dxf.insert
                    position = (insert.x, insert.y, insert.z)
                elif hasattr(entity.dxf, 'start'):
                    start = entity.dxf.start
                    position = (start.x, start.y, start.z)
                
                # Extract all available properties
                for attr_name in dir(entity.dxf):
                    if not attr_name.startswith('_'):
                        try:
                            value = getattr(entity.dxf, attr_name)
                            if not callable(value):
                                properties[attr_name] = value
                        except:
                            continue
                            
        except Exception as e:
            print(f"Warning: Error extracting properties from {entity_type}: {e}")
            
        return position, properties
    
    def _create_geometry_hash(self, entity, properties: Dict[str, Any]) -> str:
        """Create a hash representing the entity's geometry (excluding text rotation)"""
        entity_type = entity.dxftype()
        
        # For text entities, exclude rotation from hash
        if entity_type in ['TEXT', 'MTEXT']:
            hash_data = [
                entity_type,
                properties.get('text', ''),
                properties.get('height', 0),
                str(properties.get('insert', (0, 0, 0))),
                properties.get('style', '')
            ]
        else:
            # For non-text entities, include all geometry properties
            hash_data = [entity_type]
            for key, value in sorted(properties.items()):
                if isinstance(value, (list, tuple)):
                    hash_data.append(f"{key}:{str(value)}")
                else:
                    hash_data.append(f"{key}:{value}")
        
        return "|".join(str(x) for x in hash_data)
    
    def _create_entity_signature(self, entity_info: EntityInfo) -> str:
        """Create a unique signature for entity matching"""
        # For better matching, use entity type, layer, and approximate position
        # This allows for some position changes to be detected as modifications
        pos_key = f"{entity_info.position[0]:.1f},{entity_info.position[1]:.1f},{entity_info.position[2]:.1f}"
        
        # For text entities, include text content for better matching
        if entity_info.entity_type in ['TEXT', 'MTEXT']:
            text_content = entity_info.properties.get('text', '')
            return f"{entity_info.entity_type}|{entity_info.layer}|{text_content}|{pos_key}"
        
        # For other entities, use type and layer
        return f"{entity_info.entity_type}|{entity_info.layer}|{pos_key}"
    
    def _find_similar_entity(self, target_entity: EntityInfo, 
                           entities_dict: Dict[str, EntityInfo]) -> Optional[str]:
        """Find a similar entity that might be a modified version"""
        target_type = target_entity.entity_type
        target_layer = target_entity.layer
        
        # Look for entities of same type and layer
        candidates = []
        for sig, entity in entities_dict.items():
            if (entity.entity_type == target_type and 
                entity.layer == target_layer):
                
                # Calculate position distance
                pos_dist = math.sqrt(
                    (entity.position[0] - target_entity.position[0]) ** 2 +
                    (entity.position[1] - target_entity.position[1]) ** 2 +
                    (entity.position[2] - target_entity.position[2]) ** 2
                )
                
                # For text entities, also check if content is similar
                if target_type in ['TEXT', 'MTEXT']:
                    target_text = target_entity.properties.get('text', '')
                    entity_text = entity.properties.get('text', '')
                    text_similarity = len(target_text) > 0 and len(entity_text) > 0
                    if text_similarity and pos_dist < 10.0:  # Within reasonable distance
                        candidates.append((sig, pos_dist))
                else:
                    if pos_dist < 10.0:  # Within reasonable distance for geometry
                        candidates.append((sig, pos_dist))
        
        # Return the closest candidate
        if candidates:
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]
        
        return None
    
    def _are_positions_equal(self, pos1: Tuple[float, float, float], 
                           pos2: Tuple[float, float, float]) -> bool:
        """Check if two positions are equal within tolerance"""
        return (abs(pos1[0] - pos2[0]) <= self.position_tolerance and
                abs(pos1[1] - pos2[1]) <= self.position_tolerance and
                abs(pos1[2] - pos2[2]) <= self.position_tolerance)
    
    def _are_numbers_equal(self, num1: float, num2: float) -> bool:
        """Check if two numbers are equal within tolerance"""
        return abs(num1 - num2) <= self.numeric_tolerance
    
    def compare_files(self, file1_path: str, file2_path: str) -> Dict:
        """
        Compare two DXF files for all changes except text orientation
        
        Args:
            file1_path: Path to first DXF file
            file2_path: Path to second DXF file
            
        Returns:
            Dictionary containing comparison results
        """
        print(f"Extracting entities from '{file1_path}'...")
        entities1 = self.extract_entity_info(file1_path)
        
        print(f"Extracting entities from '{file2_path}'...")
        entities2 = self.extract_entity_info(file2_path)
        
        print(f"Found {len(entities1)} entities in file 1")
        print(f"Found {len(entities2)} entities in file 2")
        
        # Find changes
        property_changes = []
        geometry_changes = []
        new_entities = []
        deleted_entities = []
        
        # Track matched entities
        matched_entities2 = set()
        
        # Compare entities from file1 with file2
        for sig1, entity1 in entities1.items():
            if sig1 in entities2:
                # Exact match found
                entity2 = entities2[sig1]
                matched_entities2.add(sig1)
                
                # Check for property changes (excluding handle if ignored)
                changes = self._find_property_changes(entity1, entity2)
                if changes:
                    property_changes.append({
                        'entity_type': entity1.entity_type,
                        'signature': sig1,
                        'layer': entity1.layer,
                        'position': entity1.position,
                        'changes': changes,
                        'handle1': entity1.handle,
                        'handle2': entity2.handle
                    })
            else:
                # Try to find a similar entity (might be modified)
                similar_sig = self._find_similar_entity(entity1, entities2)
                if similar_sig and similar_sig not in matched_entities2:
                    entity2 = entities2[similar_sig]
                    matched_entities2.add(similar_sig)
                    
                    # Check for changes between similar entities
                    changes = self._find_property_changes(entity1, entity2)
                    if changes:
                        property_changes.append({
                            'entity_type': entity1.entity_type,
                            'signature': f"{sig1} → {similar_sig}",
                            'layer': entity1.layer,
                            'position': entity1.position,
                            'changes': changes,
                            'handle1': entity1.handle,
                            'handle2': entity2.handle
                        })
                    else:
                        # Entities are similar enough to be considered the same
                        # (This handles minor floating-point differences)
                        pass
                else:
                    # Entity exists in file1 but not in file2 (deleted)
                    deleted_entities.append(entity1)
        
        # Find new entities in file2
        for sig2, entity2 in entities2.items():
            if sig2 not in matched_entities2:
                new_entities.append(entity2)
        
        return {
            'property_changes': property_changes,
            'geometry_changes': geometry_changes,
            'new_entities': new_entities,
            'deleted_entities': deleted_entities,
            'total_entities_file1': len(entities1),
            'total_entities_file2': len(entities2)
        }
    
    def _find_property_changes(self, entity1: EntityInfo, entity2: EntityInfo) -> List[Dict]:
        """Find property changes between two matched entities"""
        changes = []
        
        # Check basic properties
        if entity1.color != entity2.color:
            changes.append({
                'property': 'color',
                'old_value': entity1.color,
                'new_value': entity2.color
            })
        
        if entity1.linetype != entity2.linetype:
            changes.append({
                'property': 'linetype',
                'old_value': entity1.linetype,
                'new_value': entity2.linetype
            })
        
        if not self._are_positions_equal(entity1.position, entity2.position):
            changes.append({
                'property': 'position',
                'old_value': entity1.position,
                'new_value': entity2.position
            })
        
        # Check entity-specific properties
        for prop_name in entity1.properties:
            if prop_name in entity2.properties:
                val1 = entity1.properties[prop_name]
                val2 = entity2.properties[prop_name]
                
                # Skip rotation for text entities (this is what we want to ignore)
                if entity1.entity_type in ['TEXT', 'MTEXT'] and prop_name == 'rotation':
                    continue
                
                if not self._are_values_equal(val1, val2):
                    changes.append({
                        'property': prop_name,
                        'old_value': val1,
                        'new_value': val2
                    })
        
        return changes
    
    def _are_values_equal(self, val1: Any, val2: Any) -> bool:
        """Check if two values are equal with appropriate tolerance"""
        if type(val1) != type(val2):
            return False
        
        if isinstance(val1, (int, float)):
            return self._are_numbers_equal(float(val1), float(val2))
        elif isinstance(val1, (list, tuple)):
            if len(val1) != len(val2):
                return False
            return all(self._are_values_equal(v1, v2) for v1, v2 in zip(val1, val2))
        else:
            return val1 == val2
    
    def print_results(self, results: Dict, file1_name: str, file2_name: str):
        """Print comparison results in a formatted way"""
        print("\n" + "=" * 80)
        print("DXF COMPREHENSIVE COMPARISON RESULTS")
        print("(Excluding Text Orientation Changes)")
        print("=" * 80)
        print(f"File 1: {file1_name}")
        print(f"File 2: {file2_name}")
        print(f"Position tolerance: ±{self.position_tolerance}")
        print(f"Numeric tolerance: ±{self.numeric_tolerance}")
        print("-" * 80)
        
        total_changes = (len(results['property_changes']) + 
                        len(results['geometry_changes']) +
                        len(results['new_entities']) + 
                        len(results['deleted_entities']))
        
        if total_changes == 0:
            print("✅ NO CHANGES DETECTED (excluding text orientation)")
        else:
            print(f"⚠️  FOUND {total_changes} CHANGES:")
            print()
            
            # Property changes
            if results['property_changes']:
                print(f"📝 PROPERTY CHANGES ({len(results['property_changes'])}):")
                for i, change in enumerate(results['property_changes'], 1):
                    print(f"  {i}. {change['entity_type']} on layer '{change['layer']}'")
                    print(f"     Position: ({change['position'][0]:.3f}, {change['position'][1]:.3f}, {change['position'][2]:.3f})")
                    for prop_change in change['changes']:
                        print(f"     - {prop_change['property']}: {prop_change['old_value']} → {prop_change['new_value']}")
                    print()
            
            # New entities
            if results['new_entities']:
                print(f"➕ NEW ENTITIES ({len(results['new_entities'])}):")
                for i, entity in enumerate(results['new_entities'][:10], 1):  # Show first 10
                    print(f"  {i}. {entity.entity_type} on layer '{entity.layer}'")
                    print(f"     Position: ({entity.position[0]:.3f}, {entity.position[1]:.3f}, {entity.position[2]:.3f})")
                if len(results['new_entities']) > 10:
                    print(f"     ... and {len(results['new_entities']) - 10} more")
                print()
            
            # Deleted entities
            if results['deleted_entities']:
                print(f"➖ DELETED ENTITIES ({len(results['deleted_entities'])}):")
                for i, entity in enumerate(results['deleted_entities'][:10], 1):  # Show first 10
                    print(f"  {i}. {entity.entity_type} on layer '{entity.layer}'")
                    print(f"     Position: ({entity.position[0]:.3f}, {entity.position[1]:.3f}, {entity.position[2]:.3f})")
                if len(results['deleted_entities']) > 10:
                    print(f"     ... and {len(results['deleted_entities']) - 10} more")
                print()
        
        print(f"Summary: {results['total_entities_file1']} entities in file 1, "
              f"{results['total_entities_file2']} entities in file 2")
        print("=" * 80)


def main():
    """Main function to run the comprehensive comparison"""
    if len(sys.argv) != 3:
        print("Usage: python dxf_comprehensive_compare.py <file1.dxf> <file2.dxf>")
        print()
        print("This tool compares DXF files and flags ALL changes EXCEPT text orientation changes.")
        print()
        print("Example:")
        print("  python dxf_comprehensive_compare.py drawing_v1.dxf drawing_v2.dxf")
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
    
    # Create comprehensive comparator
    comparator = DXFComprehensiveComparator(
        position_tolerance=0.001,
        numeric_tolerance=1e-6,
        ignore_handles=True
    )
    
    try:
        # Compare the files
        results = comparator.compare_files(file1_path, file2_path)
        
        # Print results
        comparator.print_results(results, file1_path, file2_path)
        
        # Exit with appropriate code
        total_changes = (len(results['property_changes']) + 
                        len(results['geometry_changes']) +
                        len(results['new_entities']) + 
                        len(results['deleted_entities']))
        
        if total_changes > 0:
            sys.exit(1)  # Changes found
        else:
            sys.exit(0)  # No changes
            
    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
