# DXF Comparison Tools

A comprehensive set of Python tools to compare CAD (DXF) files and detect different types of changes using the ezdxf library.

## 🔧 Available Tools

### 1. **Text Orientation Comparator** (`dxf_text_orientation_compare.py`)
Detects changes **only** in text label orientations while ignoring all other modifications. Perfect for quality control workflows where you need to verify annotation orientation standards.

**Key Features:**
- Focuses exclusively on TEXT and MTEXT rotation changes
- Ignores geometry, color, layer, and content changes
- Configurable angular tolerance
- Reports exact rotation angle changes

### 2. **Comprehensive Comparator** (`dxf_comprehensive_compare.py`)
Detects **all changes** between DXF files **except** text orientation changes. Ideal for general revision tracking while filtering out annotation orientation "noise".

**Key Features:**
- Detects geometry modifications (position, size, shape)
- Identifies property changes (color, layer, linetype)
- Finds new and deleted entities
- Smart entity matching algorithm
- Ignores text rotation changes completely

### 3. **Batch Comparator** (`batch_dxf_compare.py`)
Process multiple DXF file pairs in batch mode with pattern-based file matching.

## Features

### Text Orientation Comparator (`dxf_text_orientation_compare.py`)
- **Laser-focused detection**: Only reports text rotation/orientation changes
- **Handles all text types**: TEXT and MTEXT entities across model/paper spaces
- **Precise matching**: Content-based entity pairing with position tolerance
- **Configurable tolerance**: Adjustable angular sensitivity (default: ±0.1°)
- **Clear reporting**: Detailed output with before/after angles and change amounts
- **Context awareness**: Reports missing/new text entities for reference

### Comprehensive Comparator (`dxf_comprehensive_compare.py`)
- **Complete coverage**: Detects all entity modifications except text rotations
- **Universal support**: All DXF entity types (lines, circles, arcs, polylines, splines, blocks, dimensions, etc.)
- **Smart matching**: Advanced algorithm differentiates between modifications and new/deleted entities
- **Property tracking**: Colors, layers, linetypes, dimensions, and geometric properties
- **Tolerance controls**: Configurable position (±0.001) and numeric (±1e-6) tolerances
- **Detailed reporting**: Comprehensive change categorization with before/after values

## Installation

1. Make sure you have Python 3.7+ installed
2. Install required dependencies:

```bash
pip install ezdxf numpy
```

## Usage

### Text Orientation Comparator (Detects ONLY text rotation changes)

```bash
python dxf_text_orientation_compare.py <file1.dxf> <file2.dxf>
```

**Example:**
```bash
python dxf_text_orientation_compare.py drawing_old.dxf drawing_new.dxf
```

**Use this when:** You want to verify that text labels have consistent orientation while ignoring all other drawing changes.

### Comprehensive Comparator (Detects ALL changes EXCEPT text rotation)

```bash
python dxf_comprehensive_compare.py <file1.dxf> <file2.dxf>
```

**Example:**
```bash
python dxf_comprehensive_compare.py drawing_v1.dxf drawing_v2.dxf
```

**Use this when:** You want comprehensive revision tracking but don't care about text orientation adjustments.

### Batch Processing

```bash
python batch_dxf_compare.py <directory> [patterns] [tolerance]
```

### Exit Codes

- `0`: No orientation changes detected
- `1`: Orientation changes found
- `2`: Error occurred during comparison

### Test the Tools

**Text Orientation Comparator:**
```bash
python test_dxf_compare.py
```

**Comprehensive Comparator:**
```bash
python test_comprehensive_compare.py
```

This will:
1. Create sample DXF files with various changes
2. Run comparisons between them
3. Display the results showing what each tool detects

## 🔍 Tool Comparison & Decision Guide

| Change Type | Text Orientation Comparator | Comprehensive Comparator |
|-------------|----------------------------|-------------------------|
| Text rotation changes | ✅ **DETECTS** | ❌ **IGNORES** |
| Text content changes | ❌ Ignores | ✅ **DETECTS** |
| Text size changes | ❌ Ignores | ✅ **DETECTS** |
| Line position changes | ❌ Ignores | ✅ **DETECTS** |
| Circle radius changes | ❌ Ignores | ✅ **DETECTS** |
| Color changes | ❌ Ignores | ✅ **DETECTS** |
| Layer changes | ❌ Ignores | ✅ **DETECTS** |
| New/deleted entities | Reports for context | ✅ **DETECTS** |
| Property changes | ❌ Ignores | ✅ **DETECTS** |

### When to Use Each Tool

**🎯 Text Orientation Comparator:**
- Quality control for annotation standards
- Checking label consistency after drawing updates
- Verifying text rotation fixes
- When you only care about text orientation changes

**🎯 Comprehensive Comparator:**
- General revision tracking and change detection
- Identifying technical drawing modifications
- Catching geometry, dimension, and property changes
- When text orientation changes are "noise" you want to ignore

### 🔄 Complementary Workflow

For complete coverage, use both tools on the same file pair:

```bash
# Step 1: Check for substantial changes (ignore text rotation)
python dxf_comprehensive_compare.py old.dxf new.dxf

# Step 2: Separately verify text orientation consistency
python dxf_text_orientation_compare.py old.dxf new.dxf
```

## 🎯 Perfect for Different Workflows

**Quality Control Workflow:**
1. Use **Comprehensive Comparator** to catch all technical changes (geometry, dimensions, content)
2. Use **Text Orientation Comparator** separately to verify annotation orientation standards

**Revision Tracking Workflow:**
- Use **Comprehensive Comparator** when you want to ignore text orientation "noise" and focus on substantial drawing changes

**Annotation Review Workflow:**
- Use **Text Orientation Comparator** when checking if labels have been properly oriented after drawing updates

## Example Output

### Text Orientation Comparator Output
```
================================================================================
DXF TEXT ORIENTATION COMPARISON RESULTS
================================================================================
File 1: demo_drawing_v1.dxf
File 2: demo_drawing_v2.dxf
Angular tolerance: ±0.1°
--------------------------------------------------------------------------------
⚠️  FOUND 1 TEXT ORIENTATION CHANGES:

1. Text: 'NORTH ARROW'
   Position: (50.000, 75.000, 0.000)
   Layer: ANNOTATION
   Old rotation: 0.00°
   New rotation: 45.00°
   Change: 45.00°
   Handles: 101 → 201

Summary: 3 texts in file 1, 3 texts in file 2
================================================================================
```

### Comprehensive Comparator Output
```
================================================================================
DXF COMPREHENSIVE COMPARISON RESULTS
(Excluding Text Orientation Changes)
================================================================================
File 1: demo_drawing_v1.dxf
File 2: demo_drawing_v2.dxf
Position tolerance: ±0.001
Numeric tolerance: ±1e-06
--------------------------------------------------------------------------------
⚠️  FOUND 3 CHANGES:

📝 PROPERTY CHANGES (3):
  1. LINE on layer 'GEOMETRY'
     Position: (0.000, 0.000, 0.000)
     - end: (50.0, 0.0, 0.0) → (60.0, 0.0, 0.0)

  2. CIRCLE on layer 'GEOMETRY'
     Position: (25.000, 25.000, 0.000)
     - radius: 10.0 → 15.0

  3. TEXT on layer 'ANNOTATION'
     Position: (10.000, 50.000, 0.000)
     - text: Technical Drawing → Engineering Drawing

Summary: 4 entities in file 1, 4 entities in file 2
================================================================================
```

Notice how the comprehensive comparator **ignored** the 45° text rotation change but detected the line extension, circle radius change, and text content change.

## How It Works

### Text Orientation Comparator Process
1. **Text Extraction**: Extracts all TEXT and MTEXT entities from both DXF files
2. **Content Matching**: Matches text entities between files based on exact text content and position
3. **Rotation Analysis**: Compares rotation angles between matched entities
4. **Change Detection**: Reports rotation differences beyond the specified tolerance
5. **Context Reporting**: Lists missing/new text entities for reference

### Comprehensive Comparator Process
1. **Entity Extraction**: Extracts all entity types with their geometric and property data
2. **Smart Matching**: Uses advanced algorithm to match entities between files based on type, layer, and proximity
3. **Property Comparison**: Compares all properties except text rotation angles
4. **Change Classification**: Categorizes findings as property changes, new entities, or deleted entities
5. **Comprehensive Reporting**: Details all changes with before/after values

## Configuration

### Text Orientation Comparator Settings

```python
# Adjust angular tolerance
comparator = DXFTextOrientationComparator(tolerance=0.5)  # 0.5 degree tolerance

# Adjust position matching tolerance
matching_text2 = self.find_matching_text(text1, texts2, position_tolerance=0.1)
```

### Comprehensive Comparator Settings

```python
# Create comparator with custom tolerances
comparator = DXFComprehensiveComparator(
    position_tolerance=0.001,    # Position comparison tolerance
    numeric_tolerance=1e-6,      # Numeric value comparison tolerance
    ignore_handles=True          # Ignore handle differences
)
```

## Supported Entity Types

### Text Orientation Comparator
- **TEXT**: Standard single-line text entities
- **MTEXT**: Multi-line text entities

### Comprehensive Comparator
- **Geometry**: LINE, CIRCLE, ARC, ELLIPSE, SPLINE
- **Polylines**: LWPOLYLINE, POLYLINE
- **Text**: TEXT, MTEXT (content and properties, excluding rotation)
- **Blocks**: INSERT entities with transformation data
- **Dimensions**: All dimension types with their properties
- **Generic**: Universal support for any DXF entity type

## Limitations

### Text Orientation Comparator
- Only compares text orientation (rotation), not other properties
- Requires exact text content match for entity pairing
- Position-based matching may struggle with significantly moved text
- Does not handle text in blocks or external references

### Comprehensive Comparator
- Text rotation changes are completely ignored by design
- Very large files may require increased memory
- Complex block structures may have limited attribute comparison
- External reference (XREF) changes are not tracked

## Troubleshooting

### Common Issues

**"Cannot read DXF file" Error**
- Ensure the file path is correct
- Check that the file is a valid DXF format
- Verify file permissions

**"Invalid DXF file structure" Error**
- The DXF file may be corrupted
- Try opening the file in a CAD application to verify it's valid
- Check if the DXF version is supported by ezdxf

**No Changes Detected When Expected**
- For text orientation: Check if angular tolerance is too large
- For comprehensive: Check if position/numeric tolerances are too large
- Verify that entities exist in the expected spaces (model vs paper)
- Ensure coordinate systems are consistent between files

**Performance Issues with Large Files**
- Consider increasing system memory
- Try processing smaller sections of the drawing
- Use batch processing for multiple file comparisons

### Getting Help

If you encounter issues:
1. Verify your DXF files open correctly in CAD software
2. Check the console output for specific error messages
3. Try with simpler test files first
4. Ensure ezdxf library is up to date: `pip install --upgrade ezdxf`

## Project Structure

```
dxfcompare/
├── dxf_text_orientation_compare.py    # Text orientation comparator
├── dxf_comprehensive_compare.py       # Comprehensive comparator
├── batch_dxf_compare.py              # Batch processing tool
├── test_dxf_compare.py               # Tests for orientation comparator
├── test_comprehensive_compare.py     # Tests for comprehensive comparator
├── demo_drawing_v1.dxf               # Demo file (version 1)
├── demo_drawing_v2.dxf               # Demo file (version 2)
├── sample_*.dxf                      # Additional test files
└── README.md                         # This documentation
```

## License

This tool is provided professional use.
