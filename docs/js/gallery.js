/* QUACKO failure gallery lightbox: thumbnail click opens input vs degraded
 * vs ground truth. Cards and hidden per-card data are emitted at site build
 * time by scripts/gen_gallery.py from real captured failures only.
 */
(function () {
  "use strict";
  var grid = document.getElementById("qk-gal");
  if (!grid) return;
  var modal = document.getElementById("qk-modal");
  if (!modal) return;

  function val(card, key) {
    var el = card.querySelector('[data-k="' + key + '"]');
    return el ? el.textContent : "";
  }
  function open(card) {
    var title = card.dataset.title || "failure";
    document.getElementById("qk-m-title").textContent = title;
    document.getElementById("qk-m-assert").textContent =
      val(card, "assertion") + " | CER " + val(card, "cer") +
      " | " + val(card, "class") + " | " + val(card, "test");
    var deg = card.dataset.degraded || "";
    var degImg = document.getElementById("qk-m-degraded");
    var degFig = document.getElementById("qk-m-degraded-fig");
    if (deg) {
      degImg.src = deg;
      degFig.style.display = "";
    } else {
      degImg.removeAttribute("src");
      degFig.style.display = "none";
    }
    document.getElementById("qk-m-input").src = card.dataset.input || "";
    document.getElementById("qk-m-gt").textContent = val(card, "gt");
    document.getElementById("qk-m-pred").textContent = val(card, "pred");
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }
  function close() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  grid.querySelectorAll(".qk-gal-card").forEach(function (card) {
    card.addEventListener("click", function () { open(card); });
    card.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        open(card);
      }
    });
  });
  document.getElementById("qk-modal-x").addEventListener("click", close);
  modal.addEventListener("click", function (e) {
    if (e.target === modal) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
  });
})();
