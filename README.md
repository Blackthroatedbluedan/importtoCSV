# importtoCSV

CLI to turn **equipment manuals and drawings** into **UTF-8 CSV** rows you can feed to an LLM or spreadsheet tools.

## Supported inputs

| Type | Extensions | Notes |
|------|------------|--------|
| PDF | `.pdf` | Text + tables via [pdfplumber](https://github.com/jsvine/pdfplumber). **Scanned PDFs:** if a page has images but almost no text (≤ `--pdf-ocr-max-lines` lines and under `--pdf-ocr-min-chars` characters), the page is rendered and OCR’d with Tesseract (`source` column `pdf_ocr`). Use `--force-pdf-ocr` to OCR every page. Encrypted PDFs: `--password`. |
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
python -m importtocsv manual.pdf out.csv
python -m importtocsv scan.png out.csv --ocr-lang eng
python -m importtocsv brochure_scan.pdf out.csv --ocr-lang eng+fra --pdf-ocr-dpi 300
python -m importtocsv secret.pdf out.csv --password 'your-password'
python -m importtocsv drawing.dxf drawing.csv
```

## Output columns

Columns vary by source; typical fields include `source` (`pdf_text`, `pdf_table`, `image_ocr`, `cad`), `page`, `kind`, and `content`. CAD rows may include `layer` and `entity_index`.

## Tests

```bash
python -m pytest tests/ -q
```
