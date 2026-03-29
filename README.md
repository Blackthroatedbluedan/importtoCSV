# importtoCSV

CLI to turn **equipment manuals and drawings** into **UTF-8 CSV** rows you can feed to an LLM or spreadsheet tools.

## Supported inputs

| Type | Extensions | Notes |
|------|------------|--------|
| PDF | `.pdf` | Text + detected tables via [pdfplumber](https://github.com/jsvine/pdfplumber). Use `--password` for encrypted PDFs when you have the password. |
| Screenshots / scans | `.png`, `.jpg`, … | OCR via [Tesseract](https://github.com/tesseract-ocr/tesseract) (`pytesseract`). Install `tesseract-ocr` on the system. |
| CAD | `.dxf`, `.dwg` | Geometry and text via [ezdxf](https://ezdxf.mozman.at/). Some DWGs only open if a compatible reader is available; converting DWG→DXF in CAD software is a reliable fallback. |

**Encrypted PDFs:** password-protected PDFs need the correct password. This tool does not crack passwords.

## Install

```bash
pip install -e .
# Optional: for tests
pip install -e ".[dev]"
```

System dependency for images:

```bash
# Debian/Ubuntu
sudo apt install tesseract-ocr
```

## Usage

```bash
python -m importtocsv convert manual.pdf out.csv
python -m importtocsv convert scan.png out.csv --ocr-lang eng
python -m importtocsv convert secret.pdf out.csv --password 'your-password'
python -m importtocsv convert drawing.dxf drawing.csv
```

## Output columns

Columns vary by source; typical fields include `source` (`pdf_text`, `pdf_table`, `image_ocr`, `cad`), `page`, `kind`, and `content`. CAD rows may include `layer` and `entity_index`.

## Tests

```bash
python -m pytest tests/ -q
```
