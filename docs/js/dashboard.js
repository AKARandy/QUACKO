/* QUACKO home dashboard: pills, metric cards, and the CER bar chart.
 * All values come from the packaged run record (assets/data/metrics.json,
 * copied at site build time from the real CI run). No data here is invented:
 * if the record is absent, every widget says so explicitly.
 * Regression status mirrors the model layer pass rate, because REG-1/2 run
 * in that layer (see docs/quality-gates.md).
 */
(function () {
  "use strict";
  var root = document.getElementById("qk-dash");
  if (!root) return;

  function set(id, txt) {
    var el = document.getElementById(id);
    if (el) el.textContent = txt;
  }
  var PILL_BASE = "px-3 py-1 rounded-full text-xs font-bold tracking-wide whitespace-nowrap ";
  function pill(id, label, rate, infoText) {
    var el = document.getElementById(id);
    if (!el) return;
    if (infoText) {
      el.className = PILL_BASE + "bg-blue-500/20 text-blue-400";
      el.textContent = label + ": " + infoText;
    } else if (rate === 1) {
      el.className = PILL_BASE + "bg-green-500/20 text-green-400";
      el.textContent = label + ": PASSING";
    } else if (rate == null) {
      el.className = PILL_BASE + "bg-slate-700 text-slate-300";
      el.textContent = label + ": NO DATA";
    } else {
      el.className = PILL_BASE + "bg-red-500/20 text-red-400";
      el.textContent = label + ": FAILING";
    }
  }
  function noData(msg) {
    ["pill-api", "pill-model", "pill-ui"].forEach(function (id) {
      pill(id, document.getElementById(id).dataset.label, null);
    });
    pill("pill-cer", "CER TELEMETRY", null);
    ["m-receipts", "m-clean", "m-blur", "m-reg"].forEach(function (id) {
      set(id, "--");
    });
    set("dash-src", msg);
    var box = document.getElementById("cer-box");
    if (box) box.innerHTML = '<div class="border border-slate-700 rounded-xl p-6 text-slate-400 text-sm">' + msg + "</div>";
  }

  fetch("assets/data/metrics.json", { cache: "no-store" })
    .then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    })
    .then(function (m) {
      var run = m.last_run || (m.baselines && m.baselines[0]) || m.baseline;
      if (!run || !run.by_receipt || !run.by_receipt.length) {
        noData("No run data packaged with this build.");
        return;
      }
      var pr = run.pass_rate || {};
      pill("pill-api", "API CONTRACT", pr.api);
      pill("pill-model", "MODEL GATES", pr.model);
      pill("pill-ui", "UI SUITE", pr.ui);
      pill("pill-cer", "CER TELEMETRY", null, "REPORTED");

      set("m-receipts", String(run.receipts));
      set("m-clean", (run.clean_cer_mean * 100).toFixed(1) + "%");
      set("m-blur", (run.blur_cer_mean * 100).toFixed(1) + "%");
      var reg = document.getElementById("m-reg");
      if (pr.model === 1) {
        set("m-reg", "HOLDING");
        if (reg) reg.classList.add("text-green-400");
      } else if (pr.model == null) {
        set("m-reg", "NO DATA");
      } else {
        set("m-reg", "FAILING");
        if (reg) reg.classList.add("text-red-400");
      }

      var p = run.provenance || {};
      var date = run.generated ? String(run.generated).slice(0, 10) : "undated";
      var src = m.last_run ? "latest run" : "committed baseline";
      set(
        "dash-src",
        "Source: " + src + " (" + date + ", " + (p.os_family || "?") +
          " / Tesseract " + (p.tesseract_version || "?") + ")."
      );

      var canvas = document.getElementById("cer-chart");
      if (!canvas) return;
      if (!window.Chart) {
        document.getElementById("cer-box").innerHTML =
          '<div class="border border-slate-700 rounded-xl p-6 text-slate-400 text-sm">Chart library (Chart.js CDN) did not load. ' +
          "Raw per-receipt values ship with this build in assets/data/metrics.json.</div>";
        return;
      }
      var rows = run.by_receipt;
      var labels = rows.map(function (r) {
        return String(r.file).replace("img_", "").replace(".jpg", "");
      });
      var pct = function (rows2, key) {
        return rows2.map(function (r) {
          return Math.round((r[key] || 0) * 1000) / 10;
        });
      };
      new window.Chart(canvas, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            { label: "clean", data: pct(rows, "cer_clean"), backgroundColor: "#2dd4bf" },
            { label: "blur", data: pct(rows, "cer_blur"), backgroundColor: "#fbbf24" }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top", labels: { color: "#e2e8f0" } },
            tooltip: {
              callbacks: {
                label: function (c) {
                  return " " + c.dataset.label + ": " + c.parsed.y + "% field-CER";
                }
              }
            }
          },
          scales: {
            y: {
              title: { display: true, text: "field-CER %", color: "#94a3b8" },
              ticks: { color: "#94a3b8" },
              grid: { color: "rgba(148,163,184,0.15)" },
              beginAtZero: true
            },
            x: {
              title: { display: true, text: "receipt", color: "#94a3b8" },
              ticks: { color: "#94a3b8" },
              grid: { display: false }
            }
          }
        }
      });
    })
    .catch(function () {
      noData("No run data packaged with this build.");
    });
})();
