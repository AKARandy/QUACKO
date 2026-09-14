<script src="https://cdn.tailwindcss.com"></script>

<div class="bg-slate-900 text-white min-h-screen p-8 font-sans rounded-2xl" id="qk-dash">
  <h1 class="text-3xl font-bold tracking-widest">QUACKO</h1>
  <p class="text-slate-400 mt-2">QA dashboard for a Tesseract OCR receipt reader. Every widget below is fed by the latest logged CI run.</p>

  <div class="flex flex-wrap gap-2 mt-5">
    <span id="pill-api" data-label="API CONTRACT" class="px-3 py-1 rounded-full text-xs font-bold tracking-wide whitespace-nowrap bg-slate-700 text-slate-300">API CONTRACT: LOADING</span>
    <span id="pill-model" data-label="MODEL GATES" class="px-3 py-1 rounded-full text-xs font-bold tracking-wide whitespace-nowrap bg-slate-700 text-slate-300">MODEL GATES: LOADING</span>
    <span id="pill-ui" data-label="UI SUITE" class="px-3 py-1 rounded-full text-xs font-bold tracking-wide whitespace-nowrap bg-slate-700 text-slate-300">UI SUITE: LOADING</span>
    <span id="pill-cer" data-label="CER TELEMETRY" class="px-3 py-1 rounded-full text-xs font-bold tracking-wide whitespace-nowrap bg-slate-700 text-slate-300">CER TELEMETRY: LOADING</span>
  </div>

  <div class="grid !grid-cols-2 lg:!grid-cols-4 gap-6 mt-6">
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <div class="text-2xl font-bold whitespace-nowrap" id="m-receipts">--</div>
      <div class="text-slate-400 text-xs mt-1">Total receipts</div>
    </div>
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <div class="text-2xl font-bold whitespace-nowrap" id="m-clean">--</div>
      <div class="text-slate-400 text-xs mt-1">Clean CER mean</div>
    </div>
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <div class="text-2xl font-bold whitespace-nowrap" id="m-blur">--</div>
      <div class="text-slate-400 text-xs mt-1">Blur CER mean</div>
    </div>
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <div class="text-xl font-bold whitespace-nowrap" id="m-reg">--</div>
      <div class="text-slate-400 text-xs mt-1">Regression status</div>
    </div>
  </div>
  <p class="text-slate-500 text-xs mt-4" id="dash-src">Loading run data...</p>

  <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 mt-8">
    <h2 class="text-xl font-bold mb-4">Clean vs blur CER per receipt</h2>
    <div class="relative h-80" id="cer-box"><canvas id="cer-chart"></canvas></div>
    <p class="text-slate-500 text-xs mt-4">Field-CER per receipt (percent). CER is telemetry: measured and shown, never a pass/fail gate.</p>
  </div>

  <h2 class="text-xl font-bold mt-10 mb-4">Screenshot proof (real runs)</h2>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden md:col-span-2">
      <img src="screenshots/02-result-valid.png" alt="real receipt read by the engine" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">Hero: a real receipt through the real engine (text, confidence, word boxes).</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/01-upload-empty.png" alt="empty dashboard" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">Empty dashboard before upload.</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/03-error-invalid.png" alt="invalid upload error" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">Invalid upload shows the real API error.</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/04-clear-reset.png" alt="cleared dashboard" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">Clear resets to the empty state.</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/06-pytest-report.png" alt="CI pytest report" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">CI pytest report: 16/16 green.</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/07-playwright-report.png" alt="CI Playwright report" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">CI Playwright report: 3/3 green.</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/10-ui-match.png" alt="dashboard next to reference design" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">Dashboard next to the reference design it matches.</figcaption>
    </figure>
    <figure class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <img src="screenshots/11-gallery-proof.png" alt="gallery self-test capture" loading="lazy" class="w-full">
      <figcaption class="p-4 text-sm text-slate-400">Gallery self-test: a forced miss, captured and rendered, then restored to green.</figcaption>
    </figure>
  </div>

  <div class="flex flex-wrap gap-3 mt-10">
    <a href="failure-gallery/" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">Failure gallery</a>
    <a href="reports/api-model.html" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">pytest report</a>
    <a href="reports/ui-report/" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">Playwright report</a>
    <a href="https://github.com/AKARandy/QUACKO/actions" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">Actions</a>
    <a href="https://github.com/AKARandy/QUACKO" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">Repository</a>
    <a href="test-strategy/" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">Test strategy</a>
    <a href="quality-gates/" class="border border-slate-700 rounded-full px-4 py-2 text-sm text-teal-300">Quality gates</a>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
