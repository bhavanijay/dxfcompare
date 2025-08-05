# dxfcompare# DXF Text Orientation Comparator

A Python tool to compare two CAD (DXF) files and detect changes in text label orientations using the ezdxf library.

## Features

- Compares TEXT and MTEXT entities between two DXF files
- Detects orientation/rotation changes in text labels
- Configurable angular tolerance for comparison
- Reports missing and new text entities
- Handles both model space and paper space layouts
- Provides detailed comparison results with positions and angles

## Installation

1. Make sure you have Python 3.7+ installed
2. Install required dependencies:

```bash
pip install ezdxf numpy
```

## Usage

### Command Line Usage

```bash
python dxf_text_orientation_compare.py <file1.dxf> <file2.dxf>
```

Example:
```bash
python dxf_text_orientation_compare.py drawing_old.dxf drawing_new.dxf
```

### Exit Codes

- `0`: No orientation changes detected
- `1`: Orientation changes found
- `2`: Error occurred during comparison

### Test the Tool

Run the test script to create sample DXF files and test the comparison:

```bash
python test_dxf_compare.py
```

This will:
1. Create two sample DXF files with text entities
2. Run a comparison between them
3. Display the results

## How It Works

1. **Text Extraction**: The tool extracts all TEXT and MTEXT entities from both DXF files
2. **Entity Matching**: It matches text entities between files based on:
   - Text content (exact match)
   - Position (within tolerance)
3. **Orientation Comparison**: For matched entities, it compares rotation angles
4. **Change Detection**: Reports any rotation differences beyond the specified tolerance

## Configuration

### Angular Tolerance

You can adjust the angular tolerance by modifying the `DXFTextOrientationComparator` constructor:

```python
comparator = DXFTextOrientationComparator(tolerance=0.5)  # 0.5 degree tolerance
```

### Position Tolerance

The position matching tolerance can be adjusted in the `find_matching_text` method:

```python
matching_text2 = self.find_matching_text(text1, texts2, position_tolerance=0.1)
```

## Output Format

The tool provides detailed output including:

- Total number of text entities in each file
- List of orientation changes with:
  - Text content
  - Position coordinates
  - Layer information
  - Old and new rotation angles
  - Amount of rotation change
  - Entity handles
- Missing text entities (present in file 1 but not file 2)
- New text entities (present in file 2 but not file 1)

## Example Output

```
================================================================================
DXF TEXT ORIENTATION COMPARISON RESULTS
================================================================================
File 1: drawing_old.dxf
File 2: drawing_new.dxf
Angular tolerance: ±0.1°
--------------------------------------------------------------------------------
⚠️  FOUND 2 TEXT ORIENTATION CHANGES:

1. Text: 'SAMPLE TEXT 1'
   Position: (10.000, 10.000, 0.000)
   Layer: TEXT
   Old rotation: 0.00°
   New rotation: 15.00°
   Change: 15.00°
   Handles: A1B → C2D

2. Text: 'SAMPLE TEXT 3'
   Position: (30.000, 10.000, 0.000)
   Layer: TEXT
   Old rotation: 90.00°
   New rotation: 135.00°
   Change: 45.00°
   Handles: E3F → G4H

Summary: 4 texts in file 1, 5 texts in file 2
================================================================================
```

## Supported Entity Types

- **TEXT**: Standard single-line text entities
- **MTEXT**: Multi-line text entities

## Limitations

- Only compares text orientation (rotation), not other properties like size or style
- Requires exact text content match for entity pairing
- Position-based matching may not work well for significantly moved text
- Does not handle text in blocks or external references

## Troubleshooting

### "Cannot read DXF file" Error
- Ensure the file path is correct
- Check that the file is a valid DXF format
- Verify file permissions

### "Invalid DXF file structure" Error
- The DXF file may be corrupted
- Try opening the file in a CAD application to verify it's valid

### No Changes Detected When Expected
- Check if the angular tolerance is too large
- Verify that text content matches exactly between files
- Ensure text entities are in the same coordinate system

## License

This tool is provided as-is for educational and professional use.
