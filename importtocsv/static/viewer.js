(function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("csv-file");
  const fileNameEl = document.getElementById("viewer-file-name");
  const errEl = document.getElementById("viewer-error");
  const previewSection = document.getElementById("preview-section");
  const previewMeta = document.getElementById("preview-meta");

  function showError(msg) {
    errEl.textContent = msg || "";
    errEl.classList.toggle("hidden", !msg);
  }

  function loadText(name, text) {
    showError("");
    try {
      const { columns, rows } = importtocsvParseCsv(text);
      if (!columns.length) {
        showError("No columns found — is this a valid CSV?");
        previewSection.classList.add("hidden");
        return;
      }
      fileNameEl.textContent = name;
      previewMeta.textContent = `${name} — ${rows.length} data row(s), ${columns.length} column(s).`;
      if (typeof window.__importtocsvSetTableData === "function") {
        window.__importtocsvSetTableData(columns, rows);
      }
      previewSection.classList.remove("hidden");
    } catch (e) {
      showError(e.message || String(e));
      previewSection.classList.add("hidden");
    }
  }

  function handleFile(file) {
    if (!file) return;
    const name = file.name || "file.csv";
    if (!name.toLowerCase().endsWith(".csv")) {
      showError("Please choose a .csv file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => loadText(name, String(reader.result || ""));
    reader.onerror = () => showError("Could not read file.");
    reader.readAsText(file, "UTF-8");
  }

  fileInput.addEventListener("change", () => {
    const f = fileInput.files && fileInput.files[0];
    handleFile(f);
    fileInput.value = "";
  });

  ["dragenter", "dragover"].forEach((ev) => {
    dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("drop-zone-active");
    });
  });
  ["dragleave", "drop"].forEach((ev) => {
    dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (ev !== "drop") dropZone.classList.remove("drop-zone-active");
    });
  });
  dropZone.addEventListener("drop", (e) => {
    dropZone.classList.remove("drop-zone-active");
    const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    handleFile(f);
  });

  dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });
})();
