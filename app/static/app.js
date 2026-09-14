"use strict";
const $ = (s) => document.querySelector(s);

const fileInput = $("#file-input");
const dropzone = $("#dropzone");
const resultEl = $("#result");
const errorEl = $("#error");
const canvas = $("#pv-canvas");
const pvEmpty = $("#pv-empty");

function showError(msg) {
  resultEl.hidden = true;
  errorEl.textContent = msg;
  errorEl.hidden = false;
}

function drawPreview(data, url) {
  const img = new Image();
  img.onload = () => {
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);
    ctx.lineWidth = Math.max(2, canvas.width / 500);
    ctx.strokeStyle = "#14505c";
    for (const [x, y, w, h] of data.boxes) {
      ctx.strokeRect(x, y, w, h);
    }
    pvEmpty.style.display = "none";
    canvas.hidden = false;
    URL.revokeObjectURL(url);
  };
  img.src = url;
}

function showResult(data, name) {
  dropzone.hidden = true;
  errorEl.hidden = true;
  resultEl.hidden = false;
  $("#res-name").textContent = name;
  const words = data.boxes.length;
  $("#res-sub").textContent = words + " words · tesseract 5 · real engine";
  const pct = Math.round(data.confidence * 100);
  $("#conf-pct").textContent = pct + "%";
  $("#conf-ring").style.setProperty("--pct", pct);
  $("#res-text").textContent = data.text;
  $("#box-chip").textContent = words + " boxes";
  drawPreview(data, URL.createObjectURL(currentFile));
}

let currentFile = null;

async function upload(file) {
  currentFile = file;
  errorEl.hidden = true;
  const fd = new FormData();
  fd.append("image", file);
  try {
    const r = await fetch("/api/ocr", { method: "POST", body: fd });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) {
      showError((body && body.error) || "HTTP " + r.status);
      return;
    }
    showResult(body, file.name);
  } catch (e) {
    showError("request failed: " + e.message);
  }
}

function clear() {
  fileInput.value = "";
  currentFile = null;
  resultEl.hidden = true;
  errorEl.hidden = true;
  dropzone.hidden = false;
  $("#res-text").textContent = "";
  $("#res-name").textContent = "—";
  $("#res-sub").textContent = "—";
  $("#conf-pct").textContent = "0%";
  $("#conf-ring").style.setProperty("--pct", 0);
  $("#box-chip").textContent = "no boxes";
  canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
  canvas.hidden = true;
  pvEmpty.style.display = "";
}

fileInput.addEventListener("change", () => {
  if (fileInput.files && fileInput.files[0]) upload(fileInput.files[0]);
});
$("#clear-btn").addEventListener("click", clear);
["dragenter", "dragover"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.add("drag");
  })
);
["dragleave", "drop"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag");
  })
);
dropzone.addEventListener("drop", (e) => {
  const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (f) upload(f);
});

function setVal(id, v) {
  const el = $(id);
  if (el) el.textContent = v;
}

function loadStats() {
  fetch("/api/stats")
    .then((r) => r.json())
    .then((d) => {
      if (!d || d.status === "no-run") return;
      const date = d.generated ? String(d.generated).slice(0, 10) : "";
      if (d.receipts != null) {
        setVal("#st-receipts", String(d.receipts));
        setVal("#st-upd-r", date ? "run " + date + " · 20 pinned" : "pinned set");
      }
      if (d.clean_cer_mean != null) {
        setVal("#st-cer", (d.clean_cer_mean * 100).toFixed(1) + "%");
        setVal("#st-upd-c", date ? "run " + date : "");
      }
      if (d.avg_ocr_s != null) {
        setVal("#st-avg", d.avg_ocr_s.toFixed(2) + " s");
        setVal("#st-upd-a", date ? "run " + date : "");
      }
      const pr = d.pass_rate || {};
      const layers = ["api", "model", "ui"].filter((k) => pr[k] != null);
      if (layers.length) {
        const mean = layers.reduce((a, k) => a + pr[k], 0) / layers.length;
        setVal("#st-pass", Math.round(mean * 100) + "%");
        setVal("#st-upd-p", date ? "run " + date : "");
      }
      if (date) $("#lastrun-date").textContent = "Last run · " + date;
      ["api", "model", "ui"].forEach((k) => {
        const el = document.getElementById("lr-" + k);
        if (!el) return;
        if (pr[k] == null) {
          el.innerHTML = '<span class="dot dot-none"></span><span class="dot dot-none"></span><span class="dot dot-none"></span>';
          return;
        }
        const n = Math.round(pr[k] * 3);
        el.innerHTML = [0, 1, 2]
          .map((i) => '<span class="dot ' + (i < n ? "dot-ok" : "dot-bad") + '"></span>')
          .join("");
      });
      drawChart(d);
    })
    .catch(() => {});
}

function drawChart(d) {
  const svg = $("#chart-svg");
  const empty = $("#chart-empty");
  const rows = d.by_receipt || [];
  if (!rows.length) {
    empty.hidden = false;
    svg.hidden = true;
    return;
  }
  empty.hidden = true;
  svg.hidden = false;
  const W = 760, H = 220, padL = 46, padB = 28, padT = 14, padR = 14;
  svg.setAttribute("viewBox", "0 0 " + W + " " + H);
  const maxC =
    Math.max(0.1, ...rows.map((r) => Math.max(r.cer_clean || 0, r.cer_blur || 0))) * 1.2;
  const x = (i) => padL + (i * (W - padL - padR)) / Math.max(1, rows.length - 1);
  const y = (c) => padT + (1 - c / maxC) * (H - padT - padB);
  let s = "";
  for (let g = 0; g <= 4; g++) {
    const c = (maxC * g) / 4;
    const yy = y(c);
    s += '<line x1="' + padL + '" y1="' + yy + '" x2="' + (W - padR) + '" y2="' + yy + '" stroke="#e6e7f0" stroke-width="1"/>';
    s += '<text x="' + (padL - 8) + '" y="' + (yy + 4) + '" text-anchor="end" font-size="10" fill="#8a8fa8">' + (c * 100).toFixed(0) + "%</text>";
  }
  const series = (key, color) => {
    const pts = rows.map((r, i) => x(i).toFixed(1) + "," + y(r[key] || 0).toFixed(1)).join(" ");
    s += '<polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="2.5" stroke-linejoin="round"/>';
    rows.forEach((r, i) => {
      s +=
        '<circle class="pt" data-tip="' + r.file + " · " + ((r[key] || 0) * 100).toFixed(1) + '%" cx="' +
        x(i).toFixed(1) + '" cy="' + y(r[key] || 0).toFixed(1) + '" r="3.4" fill="' + color + '"/>';
    });
  };
  series("cer_clean", "#232946");
  series("cer_blur", "#f0b34c");
  [0, Math.floor(rows.length / 2), rows.length - 1].forEach((i) => {
    s +=
      '<text x="' + x(i) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="9" fill="#8a8fa8">' +
      rows[i].file.replace("img_", "#").replace(".jpg", "") + "</text>";
  });
  svg.innerHTML = s;
  const tip = $("#chart-tip");
  const box = $("#chart");
  svg.querySelectorAll(".pt").forEach((p) => {
    p.addEventListener("mousemove", (e) => {
      const r = box.getBoundingClientRect();
      tip.textContent = p.dataset.tip;
      tip.style.display = "block";
      tip.style.left = e.clientX - r.left + 12 + "px";
      tip.style.top = e.clientY - r.top - 10 + "px";
    });
    p.addEventListener("mouseleave", () => {
      tip.style.display = "none";
    });
  });
}

loadStats();
