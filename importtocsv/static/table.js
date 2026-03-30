/**
 * Client-side search/filter for extracted rows (verify parsed data).
 */
(function () {
  const searchInput = document.getElementById("table-search");
  const colSelect = document.getElementById("table-search-column");
  const caseCb = document.getElementById("table-search-case");
  const countEl = document.getElementById("table-filter-count");
  if (!searchInput || !colSelect || !caseCb || !countEl) return;

  let allRows = [];
  let columns = [];

  function rowText(row, col) {
    if (col === "__all__") {
      return columns.map((c) => String(row[c] ?? "")).join("\u0001");
    }
    return String(row[col] ?? "");
  }

  function applyFilter() {
    const tbody = document.getElementById("preview-tbody");
    if (!tbody) return;
    const q = searchInput.value.trim();
    const col = colSelect.value;
    const cs = caseCb.checked;
    const needle = cs ? q : q.toLowerCase();

    tbody.innerHTML = "";
    let n = 0;
    for (const row of allRows) {
      const text = rowText(row, col);
      const hay = cs ? text : text.toLowerCase();
      if (!needle || hay.includes(needle)) {
        const tr = document.createElement("tr");
        columns.forEach((c) => {
          const td = document.createElement("td");
          const v = row[c];
          td.textContent = v == null ? "" : String(v);
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
        n++;
      }
    }
    countEl.textContent =
      needle || col !== "__all__"
        ? `Showing ${n} of ${allRows.length} row(s)`
        : `${allRows.length} row(s)`;
  }

  searchInput.addEventListener("input", applyFilter);
  colSelect.addEventListener("change", applyFilter);
  caseCb.addEventListener("change", applyFilter);

  window.__importtocsvSetTableData = function (cols, rows) {
    columns = cols;
    allRows = rows;
    const thead = document.getElementById("preview-thead");
    if (thead) {
      thead.innerHTML = "";
      const hr = document.createElement("tr");
      cols.forEach((c) => {
        const th = document.createElement("th");
        th.textContent = c;
        hr.appendChild(th);
      });
      thead.appendChild(hr);
    }
    colSelect.innerHTML = "";
    const optAll = document.createElement("option");
    optAll.value = "__all__";
    optAll.textContent = "All columns";
    colSelect.appendChild(optAll);
    cols.forEach((c) => {
      const o = document.createElement("option");
      o.value = c;
      o.textContent = c;
      colSelect.appendChild(o);
    });
    searchInput.value = "";
    applyFilter();
  };
})();
