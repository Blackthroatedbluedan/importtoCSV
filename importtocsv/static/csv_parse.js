/**
 * Parse CSV text into { columns: string[], rows: Record<string,string>[] }.
 * Handles quoted fields, doubled quotes, and UTF-8 BOM.
 */
function importtocsvParseCsv(text) {
  if (text.charCodeAt(0) === 0xfeff) {
    text = text.slice(1);
  }
  const out = [];
  let row = [];
  let cell = "";
  let i = 0;
  let inQuotes = false;
  while (i < text.length) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          cell += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i++;
        continue;
      }
      cell += c;
      i++;
      continue;
    }
    if (c === '"') {
      inQuotes = true;
      i++;
      continue;
    }
    if (c === ",") {
      row.push(cell);
      cell = "";
      i++;
      continue;
    }
    if (c === "\r") {
      i++;
      continue;
    }
    if (c === "\n") {
      row.push(cell);
      out.push(row);
      row = [];
      cell = "";
      i++;
      continue;
    }
    cell += c;
    i++;
  }
  row.push(cell);
  if (row.length > 1 || (row.length === 1 && row[0] !== "")) {
    out.push(row);
  }
  if (out.length === 0) {
    return { columns: [], rows: [] };
  }
  const columns = out[0].map((h) => String(h).trim());
  const rows = [];
  for (let r = 1; r < out.length; r++) {
    const cells = out[r];
    const obj = {};
    columns.forEach((col, j) => {
      obj[col] = cells[j] != null ? String(cells[j]) : "";
    });
    rows.push(obj);
  }
  return { columns, rows };
}
