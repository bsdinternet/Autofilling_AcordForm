# ACORD PDF Form Extractor & Filler

Automate the extraction of form fields from ACORD insurance documents and fill them programmatically with AI-generated or user-provided data.

## Overview

This project provides a two-step workflow for working with ACORD insurance forms (AcroForm PDFs):

1. **Extract** – Parse form fields from a blank ACORD PDF template
2. **Fill** – Populate the form with data from JSON sources and save a completed PDF

### What It Does

- **Extracts** all form field metadata (text fields, checkboxes, radio buttons, signatures) from AcroForm PDFs
- **Generates** two JSON outputs:
  - **Full JSON**: Complete structural metadata with field positions and types
  - **Slim JSON**: Text-only fields ready for LLM enrichment
- **Fills** forms with data, handling:
  - Text fields (direct string insertion)
  - Checkboxes (automatic X marking)
  - Radio buttons (value matching)
  - Signatures (flagged as skip-only)
- **Validates** field integrity and handles malformed/invisible fields gracefully

## Requirements

- Python 3.7+
- `PyMuPDF` (fitz): `pip install pymupdf`

## Installation

```bash
pip install pymupdf
```

## Usage

### Step 1: Extract Form Fields

Run `acord_extract.py` on a blank ACORD template:

```bash
python acord_extract.py
```

**Configuration** (in the script):
```python
ACORD_VERSION = "Acord125_2016_03_NA"
PDF_PATH = "Demodata.pdf"  # Your template PDF
```

**Output**:
- `Acord125_2016_03_NA_fields_full.json` – All field metadata
- `Acord125_2016_03_NA_fields_slim.json` – Text fields ready for filling

### Step 2: Populate with Data

Take the slim JSON and fill it with an LLM (e.g., Gemini, ChatGPT):

```bash
# Copy contents of Acord125_2016_03_NA_fields_slim.json into Gemini with prompt:
# "Fill every fill_value with realistic insurance data"
```

Or populate manually by editing the JSON:
```json
[
  {"field_id": "Name", "fill_value": "John Smith"},
  {"field_id": "PolicyNumber", "fill_value": "POL-2024-001"},
  ...
]
```

Rename/save as `gemini.json` (or update `SLIM_JSON_PATH` in pdfwriter.py).

### Step 3: Fill the PDF

Run `pdfwriter.py` to generate the completed form:

```bash
python pdfwriter.py
```

**Output**:
- `Acord125_2016_03_NA_filled.pdf` – Your completed form

## JSON Structure

### Full Metadata (`_fields_full.json`)
```json
{
  "field_count": 42,
  "fields": [
    {
      "field_id": "PolicyNumber",
      "type": "text",
      "page": 1,
      "rect": [100.5, 200.3, 250.8, 220.1],
      "fill_value": ""
    },
    {
      "field_id": "CoverageType",
      "type": "checkbox",
      "page": 1,
      "rect": [50.0, 150.0, 70.0, 170.0],
      "checked_value": "/Yes",
      "unchecked_value": "/Off",
      "fill_value": ""
    },
    {
      "field_id": "CoverageLevel",
      "type": "radio_group",
      "page": 2,
      "radio_options": [
        {"value": "/Basic", "rect": [50.0, 100.0, 70.0, 120.0]},
        {"value": "/Premium", "rect": [50.0, 80.0, 70.0, 100.0]}
      ],
      "fill_value": ""
    }
  ]
}
```

### Slim JSON (`_fields_slim.json`)
```json
[
  {"field_id": "PolicyNumber", "fill_value": ""},
  {"field_id": "InsuredName", "fill_value": ""},
  {"field_id": "EffectiveDate", "fill_value": ""}
]
```

## Field Types

| Type | Handling |
|------|----------|
| **text** | Inserted as string value |
| **checkbox** | Draws literal "X" mark; always set to checked_value |
| **radio_group** | Matches fill_value to radio_options[].value |
| **signature** | Skipped (requires dedicated signing library) |

## Error Handling

- **Empty/missing fields**: Skipped silently with counter
- **Invalid rect geometry**: Caught and skipped (bad rect, zero-size, infinite)
- **Non-AcroForm PDFs**: Raises clear error with type classification
- **Missing files**: Graceful FileNotFoundError handling

## Configuration

Edit the top of each script:

```python
# acord_extract.py
ACORD_VERSION = "Acord125_2016_03_NA"  # Naming convention
PDF_PATH = "Demodata.pdf"               # Input template
FULL_OUT_PATH = f"{ACORD_VERSION}_fields_full.json"
SLIM_OUT_PATH = f"{ACORD_VERSION}_fields_slim.json"

# pdfwriter.py
ACORD_VERSION = "Acord125_2016_03_NA"
PDF_PATH = f"{ACORD_VERSION}.pdf"       # Template
FULL_JSON_PATH = f"{ACORD_VERSION}_fields_full.json"
SLIM_JSON_PATH = "gemini.json"          # Filled data
OUT_PATH = f"{ACORD_VERSION}_filled.pdf"
```

## Workflow Diagram

```
Blank PDF Template
      ↓
acord_extract.py
      ↓
┌─────────────────────────────┐
│ Full JSON (metadata)        │
│ Slim JSON (text fields)     │
└─────────────────────────────┘
      ↓
[Send Slim JSON to LLM for filling]
      ↓
gemini.json (populated)
      ↓
pdfwriter.py
      ↓
Completed PDF Form
```

## Limitations

- **AcroForm PDFs only** – Does not support flat PDFs or scanned documents
- **Checkboxes always marked** – Strict rule: if checkbox is in the form, it gets filled with X
- **Signature fields** – Extracted but not fillable (requires digital signing library)
- **Complex form logic** – No conditional field visibility or calculations

## Example: Complete Workflow

```bash
# 1. Extract fields
python acord_extract.py

# 2. Edit gemini.json with your data or send to LLM

# 3. Fill the PDF
python pdfwriter.py
```

## Known Issues

⚠️ **Bug in `pdfwriter.py` line 72**: The file open mode contains an invalid character. Change:
```python
with open(full_json_path, "腔") as f:
```
to:
```python
with open(full_json_path, "r") as f:
```

## License

[Add your license here]

## Contributing

Contributions welcome! Please submit issues or PRs for:
- Additional ACORD form versions
- Support for flat PDFs
- Signature field handling
- Enhanced error reporting

---

**For questions or issues**, please open a GitHub issue with:
- PDF version (ACORD_VERSION)
- Error message & traceback
- Sample field data
