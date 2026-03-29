(function () {
  const form = document.getElementById("form");
  const status = document.getElementById("status");
  const submit = document.getElementById("submit");
  const previewSection = document.getElementById("preview-section");
  const previewMeta = document.getElementById("preview-meta");
  const previewThead = document.getElementById("preview-thead");
  const previewTbody = document.getElementById("preview-tbody");
  const previewTrunc = document.getElementById("preview-trunc");
  const btnDownload = document.getElementById("btn-download");

  let lastDownload = { name: "", blob: null };

  function buildTable(columns, rows) {
    previewThead.innerHTML = "";
    previewTbody.innerHTML = "";
    const hr = document.createElement("tr");
    columns.forEach((col) => {
      const th = document.createElement("th");
      th.textContent = col;
      hr.appendChild(th);
    });
    previewThead.appendChild(hr);
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      columns.forEach((col) => {
        const td = document.createElement("td");
        const v = row[col];
        td.textContent = v == null ? "" : String(v);
        tr.appendChild(td);
      });
      previewTbody.appendChild(tr);
    });
  }

  btnDownload.addEventListener("click", () => {
    if (!lastDownload.blob) return;
    const url = URL.createObjectURL(lastDownload.blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = lastDownload.name;
    a.click();
    URL.revokeObjectURL(url);
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "";
    status.className = "status";
    previewSection.classList.add("hidden");
    lastDownload = { name: "", blob: null };
    submit.disabled = true;

    const fd = new FormData(form);
    const fileInput = document.getElementById("file");
    const file = fileInput.files[0];
    if (!file) {
      status.textContent = "Choose a file first.";
      status.classList.add("err");
      submit.disabled = false;
      return;
    }
    fd.set("file", file);
    fd.append("preview_limit", "80");

    if (!fd.get("force_pdf_ocr")) {
      fd.delete("force_pdf_ocr");
    } else {
      fd.set("force_pdf_ocr", "true");
    }

    try {
      status.textContent = "Extracting…";
      const res = await fetch("/api/convert-preview", { method: "POST", body: fd });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || res.statusText);
      }
      const data = await res.json();
      const count = data.row_count;
      const cols = data.columns.length ? data.columns : ["content", "kind", "page", "source"];
      buildTable(cols, data.rows || []);

      previewMeta.textContent = `${data.filename} — ${count} row(s) total, showing first ${data.rows.length} in the table.`;
      if (data.preview_truncated) {
        previewTrunc.textContent =
          "Table shows a preview only. Download CSV for the full extract.";
        previewTrunc.classList.remove("hidden");
      } else {
        previewTrunc.textContent = "";
        previewTrunc.classList.add("hidden");
      }

      const csvName =
        (file.name || "export").replace(/\.[^.]+$/, "") + "_extracted.csv";
      lastDownload = {
        name: csvName,
        blob: new Blob([data.csv], { type: "text/csv;charset=utf-8" }),
      };

      previewSection.classList.remove("hidden");
      status.textContent = `Done — ${count} row(s). Preview below; use Download CSV for the full file.`;
      status.classList.add("ok");
    } catch (err) {
      status.textContent = err.message || String(err);
      status.classList.add("err");
    } finally {
      submit.disabled = false;
    }
  });
})();
