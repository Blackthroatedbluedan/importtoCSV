(function () {
  const form = document.getElementById("form");
  const status = document.getElementById("status");
  const submit = document.getElementById("submit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "";
    status.className = "status";
    submit.disabled = true;

    const fd = new FormData(form);
    const file = document.getElementById("file").files[0];
    if (!file) {
      status.textContent = "Choose a file first.";
      status.classList.add("err");
      submit.disabled = false;
      return;
    }
    fd.set("file", file);

    if (!fd.get("force_pdf_ocr")) {
      fd.delete("force_pdf_ocr");
    } else {
      fd.set("force_pdf_ocr", "true");
    }

    try {
      const res = await fetch("/api/convert", { method: "POST", body: fd });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || res.statusText);
      }
      const blob = await res.blob();
      const count = res.headers.get("X-Row-Count");
      const name =
        (file.name || "export").replace(/\.[^.]+$/, "") + "_extracted.csv";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
      status.textContent =
        count != null
          ? `Done — ${count} row(s) saved as ${name}.`
          : `Download started — ${name}.`;
      status.classList.add("ok");
    } catch (err) {
      status.textContent = err.message || String(err);
      status.classList.add("err");
    } finally {
      submit.disabled = false;
    }
  });
})();
