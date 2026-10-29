/**
 * Frontend — Two-phase: Discover → Select URLs → Scrape
 * + Custom keyword, custom location (Bhavani), JustDial-aware rendering
 */

let geoData = { states: [], districts_by_state: {} };
let categoriesList = [];
let pollingTimer = null;
let currentStatus = "idle";
let allLeads = [];
let discoveredCandidates = [];
let hasAutoDownloaded = false;

const SEARCH_ENGINES_LIST = [
    { id: "google", name: "Google", icon: "fa-brands fa-google", color: "#2563eb" },
    { id: "brave", name: "Brave Search", icon: "fa-solid fa-shield-halved", color: "#ea580c" },
    { id: "firefox", name: "Firefox", icon: "fa-brands fa-firefox-browser", color: "#d97706" },
    { id: "yahoo", name: "Yahoo", icon: "fa-brands fa-yahoo", color: "#7c3aed" },
    { id: "bing", name: "Microsoft Bing", icon: "fa-brands fa-microsoft", color: "#0284c7" },
    { id: "duckduckgo", name: "DuckDuckGo", icon: "fa-solid fa-compass", color: "#dc2626" }
];

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    renderSearchEnginesList();
    setupEventListeners();
    await loadGeoAndCategories();
    selectPresetTamilNadu(true);  // Default: TN + Erode preset
    startPolling();
}

// ── SEARCH ENGINES ─────────────────────────────────────────────────────────
function renderSearchEnginesList() {
    const container = document.getElementById("searchEnginesContainer");
    if (!container) return;
    container.innerHTML = "";
    SEARCH_ENGINES_LIST.forEach(eng => {
        const label = document.createElement("label");
        label.className = "engine-checkbox-item";
        label.title = `Search & collect data from ${eng.name}`;

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.value = eng.id;
        cb.checked = true;
        cb.addEventListener("change", updateSearchEnginesSummary);

        const icon = document.createElement("i");
        icon.className = `${eng.icon} engine-icon`;
        icon.style.color = eng.color;

        const textSpan = document.createElement("span");
        textSpan.className = "engine-label-text";
        textSpan.textContent = eng.name;

        label.appendChild(cb);
        label.appendChild(icon);
        label.appendChild(textSpan);
        container.appendChild(label);
    });
    updateSearchEnginesSummary();
}

function getSelectedSearchEngines() {
    return Array.from(document.querySelectorAll("#searchEnginesContainer input:checked")).map(cb => cb.value);
}

function updateSearchEnginesSummary() {
    const summaryEl = document.getElementById("enginesSelectedSummary");
    if (!summaryEl) return;
    const selected = getSelectedSearchEngines();
    summaryEl.textContent = `${selected.length} / ${SEARCH_ENGINES_LIST.length} Search Engines selected`;
}

// ── DATA LOAD ──────────────────────────────────────────────────────────────
async function loadGeoAndCategories() {
    try {
        const [geoRes, catRes] = await Promise.all([
            fetch('/api/geo-data'), fetch('/api/categories')
        ]);
        geoData = await geoRes.json();
        const catData = await catRes.json();
        categoriesList = catData.categories || [];
        renderStatesList(geoData.states);
        renderCategoriesList(categoriesList);
    } catch (err) {
        console.error("Data load failed:", err);
    }
}

// ── STATES ─────────────────────────────────────────────────────────────────
function renderStatesList(states, filterText = "") {
    const container = document.getElementById("statesContainer");
    const selected = getSelectedStates();
    container.innerHTML = "";
    states.filter(s => s.toLowerCase().includes(filterText.toLowerCase())).forEach(state => {
        const label = document.createElement("label");
        label.className = "checkbox-item";
        const cb = document.createElement("input");
        cb.type = "checkbox"; cb.value = state; cb.checked = selected.includes(state);
        cb.addEventListener("change", () => { updateDistrictsList(); updateStatesSummary(); });
        label.appendChild(cb); label.appendChild(document.createTextNode(state));
        container.appendChild(label);
    });
    updateStatesSummary();
}

function updateStatesSummary() {
    document.getElementById("statesSelectedSummary").textContent = `${getSelectedStates().length} States selected`;
}

function getSelectedStates() {
    return Array.from(document.querySelectorAll("#statesContainer input:checked")).map(cb => cb.value);
}

// ── DISTRICTS ──────────────────────────────────────────────────────────────
function updateDistrictsList(filterText = "") {
    const selectedStates = getSelectedStates();
    const container = document.getElementById("districtsContainer");
    const prevSelected = getSelectedDistricts();
    if (selectedStates.length === 0) {
        container.innerHTML = '<div class="empty-hint">Select a State to load districts.</div>';
        updateDistrictsSummary(); return;
    }
    let all = [];
    selectedStates.forEach(s => { all = all.concat(geoData.districts_by_state[s] || []); });
    all = Array.from(new Set(all)).sort();
    const filtered = all.filter(d => d.toLowerCase().includes(filterText.toLowerCase()));
    container.innerHTML = "";
    if (!filtered.length) { container.innerHTML = '<div class="empty-hint">No districts match.</div>'; return; }
    filtered.forEach(dist => {
        const label = document.createElement("label");
        label.className = "checkbox-item";
        const cb = document.createElement("input");
        cb.type = "checkbox"; cb.value = dist; cb.checked = prevSelected.includes(dist);
        cb.addEventListener("change", updateDistrictsSummary);
        label.appendChild(cb); label.appendChild(document.createTextNode(dist));
        container.appendChild(label);
    });
    updateDistrictsSummary();
}

function updateDistrictsSummary() {
    document.getElementById("districtsSelectedSummary").textContent = `${getSelectedDistricts().length} Districts selected`;
}

function getSelectedDistricts() {
    return Array.from(document.querySelectorAll("#districtsContainer input:checked")).map(cb => cb.value);
}

// ── CATEGORIES ─────────────────────────────────────────────────────────────
function renderCategoriesList(categories) {
    const container = document.getElementById("categoriesContainer");
    container.innerHTML = "";
    categories.forEach((cat, idx) => {
        const label = document.createElement("label");
        label.className = "checkbox-item";
        const cb = document.createElement("input");
        cb.type = "checkbox"; cb.value = cat.id; cb.checked = (idx < 2);
        cb.addEventListener("change", updateCategoriesSummary);
        label.appendChild(cb); label.appendChild(document.createTextNode(cat.name));
        container.appendChild(label);
    });
    updateCategoriesSummary();
}

function updateCategoriesSummary() {
    document.getElementById("categoriesSelectedSummary").textContent = `${getSelectedCategories().length} Categories selected`;
}

function getSelectedCategories() {
    return Array.from(document.querySelectorAll("#categoriesContainer input:checked")).map(cb => cb.value);
}

// ── PRESETS ─────────────────────────────────────────────────────────────────
function selectPresetTamilNadu(onlyErode = false) {
    document.querySelectorAll("#statesContainer input").forEach(cb => { cb.checked = cb.value === "Tamil Nadu"; });
    updateStatesSummary(); updateDistrictsList();
    if (onlyErode) {
        setTimeout(() => {
            document.querySelectorAll("#districtsContainer input").forEach(cb => { cb.checked = cb.value === "Erode"; });
            updateDistrictsSummary();
        }, 50);
    } else {
        setTimeout(() => {
            document.querySelectorAll("#districtsContainer input").forEach(cb => { cb.checked = true; });
            updateDistrictsSummary();
        }, 50);
    }
}

// ── EVENT LISTENERS ─────────────────────────────────────────────────────────
function setupEventListeners() {
    document.getElementById("stateSearchInput").addEventListener("input", e => renderStatesList(geoData.states, e.target.value));
    document.getElementById("districtSearchInput").addEventListener("input", e => updateDistrictsList(e.target.value));

    document.getElementById("btnSelectAllStates").addEventListener("click", () => {
        document.querySelectorAll("#statesContainer input").forEach(cb => cb.checked = true);
        updateStatesSummary(); updateDistrictsList();
    });
    document.getElementById("btnClearStates").addEventListener("click", () => {
        document.querySelectorAll("#statesContainer input").forEach(cb => cb.checked = false);
        updateStatesSummary(); updateDistrictsList();
    });
    document.getElementById("btnPresetTN").addEventListener("click", () => selectPresetTamilNadu(false));
    document.getElementById("btnSelectAllDistricts").addEventListener("click", () => {
        document.querySelectorAll("#districtsContainer input").forEach(cb => cb.checked = true);
        updateDistrictsSummary();
    });
    document.getElementById("btnPresetErode").addEventListener("click", () => selectPresetTamilNadu(true));
    document.getElementById("btnClearDistricts").addEventListener("click", () => {
        document.querySelectorAll("#districtsContainer input").forEach(cb => cb.checked = false);
        updateDistrictsSummary();
    });
    document.getElementById("btnSelectAllCats").addEventListener("click", () => {
        document.querySelectorAll("#categoriesContainer input").forEach(cb => cb.checked = true);
        updateCategoriesSummary();
    });
    document.getElementById("btnSelectCivilOnly").addEventListener("click", () => {
        document.querySelectorAll("#categoriesContainer input").forEach(cb => { cb.checked = cb.value === "civil_contractors"; });
        updateCategoriesSummary();
    });

    // Search Engine quick buttons
    const btnAllEngines = document.getElementById("btnSelectAllEngines");
    if (btnAllEngines) {
        btnAllEngines.addEventListener("click", () => {
            document.querySelectorAll("#searchEnginesContainer input").forEach(cb => cb.checked = true);
            updateSearchEnginesSummary();
        });
    }
    const btnGoogleBrave = document.getElementById("btnPresetGoogleBrave");
    if (btnGoogleBrave) {
        btnGoogleBrave.addEventListener("click", () => {
            document.querySelectorAll("#searchEnginesContainer input").forEach(cb => {
                cb.checked = (cb.value === "google" || cb.value === "brave");
            });
            updateSearchEnginesSummary();
        });
    }
    const btnClearEngines = document.getElementById("btnClearEngines");
    if (btnClearEngines) {
        btnClearEngines.addEventListener("click", () => {
            document.querySelectorAll("#searchEnginesContainer input").forEach(cb => cb.checked = false);
            updateSearchEnginesSummary();
        });
    }

    // Main action buttons
    const btnAuto = document.getElementById("btnAutoProcess");
    if (btnAuto) {
        btnAuto.addEventListener("click", handleAutoProcess);
    }
    const btnPanIndia = document.getElementById("btnPanIndiaAutoProcess");
    if (btnPanIndia) {
        btnPanIndia.addEventListener("click", handlePanIndiaAutoProcess);
    }
    document.getElementById("btnDiscover").addEventListener("click", handleDiscover);
    document.getElementById("btnScrapeAll").addEventListener("click", handleScrapeAll);
    document.getElementById("btnScrapeSelected").addEventListener("click", handleScrapeSelected);
    document.getElementById("btnPause").addEventListener("click", handlePause);
    document.getElementById("btnResume").addEventListener("click", handleResume);
    document.getElementById("btnStop").addEventListener("click", handleStop);
    document.getElementById("btnClear").addEventListener("click", handleClear);

    // Discovered URLs panel controls
    document.getElementById("btnCheckAllDisc").addEventListener("click", () => {
        document.querySelectorAll(".disc-item input[type='checkbox']").forEach(cb => {
            cb.checked = true; cb.closest('.disc-item').classList.add('selected');
        });
        updateDiscSelectedCount();
    });
    document.getElementById("btnUncheckAllDisc").addEventListener("click", () => {
        document.querySelectorAll(".disc-item input[type='checkbox']").forEach(cb => {
            cb.checked = false; cb.closest('.disc-item').classList.remove('selected');
        });
        updateDiscSelectedCount();
    });

    document.getElementById("tableSearchInput").addEventListener("input", e => filterLeadsTable(e.target.value));
    document.getElementById("btnConsoleClear").addEventListener("click", () => { document.getElementById("consoleBody").innerHTML = ""; });
}

// ── 1-CLICK FULL AUTOMATION (A → Z DISTRICTS) ──────────────────────────────
async function handleAutoProcess() {
    const states = getSelectedStates();
    let districts = getSelectedDistricts();
    const categories = getSelectedCategories();
    const customLocation = document.getElementById("customLocationInput").value.trim();
    const customKeyword = document.getElementById("customKeywordInput").value.trim();

    if (!states.length) {
        alert("Please select at least one State (e.g. Tamil Nadu).");
        return;
    }

    // If user selected state(s) without ticking specific districts, auto-select all districts for complete coverage
    if (districts.length === 0) {
        document.querySelectorAll("#districtsContainer input").forEach(cb => { cb.checked = true; });
        updateDistrictsSummary();
        districts = getSelectedDistricts();
    }

    if (!categories.length && !customKeyword) {
        alert("Please select at least one Category or enter a Custom Search Keyword.");
        return;
    }

    // Auto-select Google search engine checkbox if unchecked
    const googleCb = document.querySelector("#searchEnginesContainer input[value='google']");
    if (googleCb && !googleCb.checked) {
        googleCb.checked = true;
        updateSearchEnginesSummary();
    }

    const searchEngines = getSelectedSearchEngines();
    if (!searchEngines.includes('google')) {
        searchEngines.unshift('google');
    }

    // Reset UI state for auto processing
    hasAutoDownloaded = false;
    allLeads = [];
    discoveredCandidates = [];
    document.getElementById("discoveredPanel").style.display = "none";
    document.getElementById("discList").innerHTML = "";
    const banner = document.getElementById("masterDownloadBanner");
    if (banner) banner.style.display = "none";

    try {
        const res = await fetch('/api/auto-process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pan_india: false,
                states,
                districts,
                categories,
                custom_location: customLocation,
                custom_keyword: customKeyword,
                search_engines: searchEngines
            })
        });
        const data = await res.json();
        if (!data.success) {
            alert(data.message);
            return;
        }
        updateControlsState("running");
    } catch (err) {
        alert("Auto-process failed: " + err);
    }
}

// ── 1-CLICK PAN-INDIA FULL AUTOMATION (ALL 36 STATES & DISTRICTS A → Z) ───
async function handlePanIndiaAutoProcess() {
    const categories = getSelectedCategories();
    const customKeyword = document.getElementById("customKeywordInput").value.trim();

    if (!categories.length && !customKeyword) {
        alert("Please select at least one Category or enter a Custom Search Keyword.");
        return;
    }

    // Auto-select Google search engine checkbox if unchecked
    const googleCb = document.querySelector("#searchEnginesContainer input[value='google']");
    if (googleCb && !googleCb.checked) {
        googleCb.checked = true;
        updateSearchEnginesSummary();
    }

    const searchEngines = getSelectedSearchEngines();
    if (!searchEngines.includes('google')) {
        searchEngines.unshift('google');
    }

    // Visually select all states in UI as well for user transparency
    document.querySelectorAll("#statesContainer input").forEach(cb => cb.checked = true);
    updateStatesSummary();

    // Reset UI state for auto processing
    hasAutoDownloaded = false;
    allLeads = [];
    discoveredCandidates = [];
    document.getElementById("discoveredPanel").style.display = "none";
    document.getElementById("discList").innerHTML = "";
    const banner = document.getElementById("masterDownloadBanner");
    if (banner) banner.style.display = "none";

    try {
        const res = await fetch('/api/auto-process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pan_india: true,
                states: (geoData.states || []).slice().sort(),
                districts: [],
                categories,
                custom_location: "",
                custom_keyword: customKeyword,
                search_engines: searchEngines
            })
        });
        const data = await res.json();
        if (!data.success) {
            alert(data.message);
            return;
        }
        updateControlsState("running");
    } catch (err) {
        alert("Pan India Auto-process failed: " + err);
    }
}

// ── PHASE 1: DISCOVER ───────────────────────────────────────────────────────
async function handleDiscover() {
    const states = getSelectedStates();
    let districts = getSelectedDistricts();
    const categories = getSelectedCategories();
    const searchEngines = getSelectedSearchEngines();
    const customLocation = document.getElementById("customLocationInput").value.trim();
    const customKeyword = document.getElementById("customKeywordInput").value.trim();

    if (!states.length) { alert("Please select at least one State."); return; }

    // If user selected state(s) without ticking specific districts, auto-select all districts for complete coverage
    if (districts.length === 0) {
        document.querySelectorAll("#districtsContainer input").forEach(cb => { cb.checked = true; });
        updateDistrictsSummary();
        districts = getSelectedDistricts();
    }
    if (!categories.length && !customKeyword) { alert("Please select at least one Category or enter a Custom Search Keyword."); return; }
    if (!searchEngines.length) { alert("Please select at least one Search Engine (Google, Brave Search, Firefox, Yahoo, Microsoft Bing, or DuckDuckGo)."); return; }

    // Reset candidates and hide panel for new discovery run
    discoveredCandidates = [];
    document.getElementById("discoveredPanel").style.display = "none";
    document.getElementById("discList").innerHTML = "";

    try {
        const res = await fetch('/api/discover', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                states,
                districts,
                categories,
                custom_location: customLocation,
                custom_keyword: customKeyword,
                search_engines: searchEngines
            })
        });
        const data = await res.json();
        if (!data.success) { alert(data.message); return; }
        updateControlsState("discovering");
    } catch (err) {
        alert("Discovery failed: " + err);
    }
}

// ── PHASE 2: SCRAPE ─────────────────────────────────────────────────────────
async function handleScrapeAll() {
    try {
        const res = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scrape_all: true })
        });
        const data = await res.json();
        if (!data.success) { alert(data.message); return; }
        updateControlsState("running");
    } catch (err) {
        alert("Scrape failed: " + err);
    }
}

async function handleScrapeSelected() {
    const selectedUrls = Array.from(document.querySelectorAll(".disc-item input[type='checkbox']:checked"))
        .map(cb => cb.value);
    if (!selectedUrls.length) { alert("Please tick at least one URL to scrape."); return; }
    try {
        const res = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scrape_all: false, selected_urls: selectedUrls })
        });
        const data = await res.json();
        if (!data.success) { alert(data.message); return; }
        updateControlsState("running");
    } catch (err) {
        alert("Scrape failed: " + err);
    }
}

// ── CONTROL HANDLERS ────────────────────────────────────────────────────────
async function handlePause() {
    const res = await fetch('/api/pause', { method: 'POST' });
    const data = await res.json();
    if (data.success) updateControlsState("paused");
}
async function handleResume() {
    const res = await fetch('/api/resume', { method: 'POST' });
    const data = await res.json();
    if (data.success) updateControlsState("running");
}
async function handleStop() {
    const btnStop = document.getElementById("btnStop");
    if (btnStop) {
        btnStop.disabled = true;
        btnStop.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Stopping...`;
    }
    currentStatus = "stopped";
    updateControlsState("stopped");
    const dot = document.querySelector(".status-dot");
    if (dot) dot.className = "status-dot dot-stopped";
    const statusTxt = document.getElementById("statusText");
    if (statusTxt) statusTxt.textContent = "STOPPED";

    try {
        await fetch('/api/stop', { method: 'POST' });
    } catch (err) {}
}
async function handleClear() {
    if (!confirm("Clear all results and session?")) return;
    const res = await fetch('/api/clear', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
        updateControlsState("idle");
        hasAutoDownloaded = false;
        const masterBanner = document.getElementById("masterDownloadBanner");
        if (masterBanner) masterBanner.style.display = "none";
        allLeads = [];
        discoveredCandidates = [];
        document.getElementById("discoveredPanel").style.display = "none";
        document.getElementById("discList").innerHTML = "";
        document.getElementById("leadsTableBody").innerHTML = `<tr class="empty-row"><td colspan="13"><div class="table-empty-state"><div class="empty-icon-circle"><i class="fa-solid fa-building-magnifying-glass empty-icon"></i></div><h3>No Verified Leads Extracted Yet</h3><p>Configure your target State, District, and Category on the left panel, then click <strong>Start Auto Process &amp; Export</strong> or <strong>Search &amp; Discover URLs</strong>.</p></div></td></tr>`;
        document.getElementById("leadsCountHeader").textContent = "0";
        document.getElementById("statDiscovered").textContent = "0";
        document.getElementById("statTotalLeads").textContent = "0";
        document.getElementById("statPhones").textContent = "0";
        document.getElementById("statEmails").textContent = "0";
        document.getElementById("statChildPages").textContent = "0";
        document.getElementById("progressBar").style.width = "0%";
        document.getElementById("progressPercent").textContent = "0%";
        document.getElementById("activeTargetText").textContent = "Waiting...";
        document.getElementById("activeSiteText").textContent = "-";
        document.getElementById("consoleBody").innerHTML = "";
    } else {
        alert(data.message);
    }
}

// ── POLLING ──────────────────────────────────────────────────────────────────
function startPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    pollingTimer = setInterval(async () => {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            renderStatus(data);

            // Always fetch discovered URLs if status is awaiting_selection or completed and panel is not visible
            const panelVisible = document.getElementById("discoveredPanel").style.display === "block";
            if ((data.status === "awaiting_selection" || data.status === "completed" || data.status === "running") && data.discovered_count > 0 && !panelVisible) {
                await fetchDiscovered();
            }

            if (data.status === "running" || data.total_leads > allLeads.length) {
                await fetchLeads();
            }
        } catch (err) {}
    }, 1500);
}

function renderStatus(data) {
    currentStatus = data.status;
    updateControlsState(data.status);

    const dot = document.querySelector(".status-dot");
    dot.className = `status-dot dot-${data.status}`;
    document.getElementById("statusText").textContent = data.status.toUpperCase().replace('_', ' ');

    document.getElementById("statDiscovered").textContent = data.discovered_count || 0;
    document.getElementById("statTotalLeads").textContent = data.total_leads;
    document.getElementById("statPhones").textContent = data.leads_with_phone;
    document.getElementById("statEmails").textContent = data.leads_with_email;
    document.getElementById("statChildPages").textContent = data.total_child_pages;

    const pct = `${data.progress_percent}%`;
    document.getElementById("progressBar").style.width = pct;
    document.getElementById("progressPercent").textContent = pct;

    if (data.current_task) document.getElementById("activeTargetText").textContent = data.current_task;
    if (data.current_site) document.getElementById("activeSiteText").textContent = data.current_site;

    // Master State / Pan-India Excel banner & Auto-download handling
    const masterBanner = document.getElementById("masterDownloadBanner");
    const btnDownloadMaster = document.getElementById("btnDownloadMaster");
    const masterTitle = document.getElementById("masterBannerTitle");
    const masterSubtitle = document.getElementById("masterBannerSubtitle");

    if (data.latest_master_url && masterBanner && btnDownloadMaster) {
        masterBanner.style.display = "flex";
        btnDownloadMaster.href = data.latest_master_url;

        const isPanIndia = data.is_pan_india || (data.latest_master_file && data.latest_master_file.includes("PAN_INDIA"));
        if (isPanIndia) {
            if (masterTitle) masterTitle.innerHTML = `<i class="fa-solid fa-earth-asia" style="color:#fde047"></i> Pan-India Master Excel Ready!`;
            if (masterSubtitle) {
                masterSubtitle.textContent = `All state & district files saved to backend/exports/. Pan-India Master consolidated Excel file ready with ${data.total_leads} verified leads!`;
            }
            btnDownloadMaster.innerHTML = `<i class="fa-solid fa-cloud-arrow-down"></i> Download Pan-India Master Excel`;
        } else {
            if (masterTitle) masterTitle.innerHTML = `<i class="fa-solid fa-file-excel"></i> Master State Excel Ready!`;
            if (masterSubtitle) {
                masterSubtitle.textContent = `All district files saved to backend/exports/. Master consolidated Excel file ready with ${data.total_leads} verified leads!`;
            }
            btnDownloadMaster.innerHTML = `<i class="fa-solid fa-cloud-arrow-down"></i> Download Master State Excel`;
        }

        // Auto trigger download once when auto mode completes
        if (data.is_auto_mode && data.status === "completed" && !hasAutoDownloaded) {
            hasAutoDownloaded = true;
            const dlLink = document.createElement("a");
            dlLink.href = data.latest_master_url;
            dlLink.download = data.latest_master_file || (isPanIndia ? "Pan_India_Master_Leads.xlsx" : "State_Master_Leads.xlsx");
            document.body.appendChild(dlLink);
            dlLink.click();
            document.body.removeChild(dlLink);
        }
    }

    renderLogs(data.recent_logs || []);
}

function renderLogs(logs) {
    const consoleBody = document.getElementById("consoleBody");
    const autoScroll = document.getElementById("autoScrollToggle").checked;
    logs.forEach(log => {
        const logId = `log-${log.timestamp}-${(log.message || '').slice(0, 10).replace(/\W/g, '')}`;
        if (!document.getElementById(logId)) {
            const line = document.createElement("div");
            line.id = logId; line.className = `log-line log-${log.level}`;
            line.innerHTML = `<span class="log-time">[${log.timestamp}]</span> <span class="log-msg">${escapeHtml(log.message)}</span>`;
            consoleBody.appendChild(line);
        }
    });
    if (autoScroll) consoleBody.scrollTop = consoleBody.scrollHeight;
}

// ── DISCOVERED URLS PANEL ───────────────────────────────────────────────────
async function fetchDiscovered() {
    try {
        const res = await fetch('/api/discovered');
        const data = await res.json();
        discoveredCandidates = data.candidates || [];
        if (discoveredCandidates.length > 0) {
            renderDiscoveredPanel(discoveredCandidates);
            document.getElementById("discoveredPanel").style.display = "block";
            document.getElementById("statDiscovered").textContent = discoveredCandidates.length;
            // Auto-enable scrape buttons
            document.getElementById("btnScrapeAll").disabled = false;
            document.getElementById("btnScrapeSelected").disabled = false;
        }
    } catch (err) {}
}

function renderDiscoveredPanel(candidates) {
    const list = document.getElementById("discList");
    list.innerHTML = "";
    candidates.forEach((cand, idx) => {
        const item = document.createElement("div");
        item.className = "disc-item";

        const cb = document.createElement("input");
        cb.type = "checkbox"; cb.value = cand.url; cb.checked = true;
        cb.addEventListener("change", () => {
            item.classList.toggle("selected", cb.checked);
            updateDiscSelectedCount();
        });
        item.classList.add("selected");

        const urlSpan = document.createElement("div");
        urlSpan.style.overflow = "hidden";
        urlSpan.innerHTML = `
            <div class="disc-url">${escapeHtml(cand.url)}</div>
            <div class="disc-title">${escapeHtml(cand.title || '')}</div>
        `;

        const engineBadge = document.createElement("span");
        engineBadge.className = "disc-engine-badge";
        engineBadge.textContent = cand.engine || 'Web';

        const openLink = document.createElement("a");
        openLink.href = cand.url; openLink.target = "_blank"; openLink.rel = "noopener";
        openLink.className = "disc-open"; openLink.innerHTML = '<i class="fa-solid fa-arrow-up-right-from-square"></i>';

        item.appendChild(cb); item.appendChild(urlSpan);
        item.appendChild(engineBadge); item.appendChild(openLink);
        list.appendChild(item);
    });
    updateDiscSelectedCount();
}

function updateDiscSelectedCount() {
    const count = document.querySelectorAll(".disc-item input:checked").length;
    document.getElementById("discSelectedCount").textContent = `${count} selected`;
}

// ── LEADS TABLE ──────────────────────────────────────────────────────────────
async function fetchLeads() {
    try {
        const res = await fetch('/api/leads');
        const data = await res.json();
        allLeads = data.leads || [];
        document.getElementById("leadsCountHeader").textContent = allLeads.length;
        renderLeadsTable(allLeads);
    } catch (err) {}
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById("leadsTableBody");
    if (!leads || !leads.length) {
        tbody.innerHTML = `<tr class="empty-row"><td colspan="13"><div class="table-empty-state"><div class="empty-icon-circle"><i class="fa-solid fa-building-magnifying-glass empty-icon"></i></div><h3>No Verified Leads Extracted Yet</h3><p>Configure your target State, District, and Category on the left panel, then click <strong>Search &amp; Discover URLs</strong>.</p></div></td></tr>`;
        return;
    }
    tbody.innerHTML = "";
    leads.forEach((lead, idx) => {
        const tr = document.createElement("tr");
        const ratingBadge = lead.rating
            ? `<span class="badge-tag badge-rating"><i class="fa-solid fa-star"></i> ${escapeHtml(lead.rating)}</span>`
            : '<span style="color:#94a3b8">—</span>';
        const phoneBadges = lead.mobile_numbers
            ? `<div class="badge-group">${lead.mobile_numbers.split(',').map(p => {
                const cleanTel = p.trim().replace(/\s+/g, '');
                return `<a href="tel:${escapeHtml(cleanTel)}" class="badge-tag badge-phone" title="Click to call ${escapeHtml(p.trim())}"><i class="fa-solid fa-phone"></i> ${escapeHtml(p.trim())}</a>`;
            }).join('')}</div>`
            : '<span style="color:#94a3b8">—</span>';
        const officeBadges = lead.office_numbers
            ? `<div class="badge-group">${lead.office_numbers.split(',').map(o => `<span class="badge-tag badge-office"><i class="fa-solid fa-tty"></i> ${escapeHtml(o.trim())}</span>`).join('')}</div>`
            : '<span style="color:#94a3b8">—</span>';
        const emailBadges = lead.email_addresses
            ? `<div class="badge-group">${lead.email_addresses.split(',').map(e => `<a href="mailto:${escapeHtml(e.trim())}" class="badge-tag badge-email"><i class="fa-solid fa-envelope"></i> ${escapeHtml(e.trim())}</a>`).join('')}</div>`
            : '<span style="color:#94a3b8">—</span>';
        const websiteLink = lead.website
            ? `<a href="${lead.website}" target="_blank" rel="noopener" class="link-out"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit</a>` : '<span style="color:#94a3b8">—</span>';
        const sourceLink = lead.source_url
            ? `<a href="${lead.source_url}" target="_blank" rel="noopener" class="link-out-url" title="${escapeHtml(lead.source_url)}"><i class="fa-solid fa-link"></i> ${escapeHtml(lead.source_url)}</a>` : '<span style="color:#94a3b8">—</span>';

        tr.innerHTML = `
            <td class="col-idx" style="font-weight:700;color:#64748b">${idx + 1}</td>
            <td class="col-name"><span class="biz-name-cell">${escapeHtml(lead.business_name)}</span></td>
            <td class="col-cat"><span class="badge-tag badge-cat">${escapeHtml(lead.category)}</span></td>
            <td class="col-rating">${ratingBadge}</td>
            <td class="col-loc"><span class="loc-primary">${escapeHtml(lead.city_area || lead.district)}</span><span class="loc-sub">${escapeHtml(lead.state)}</span></td>
            <td class="col-phone">${phoneBadges}</td>
            <td class="col-office">${officeBadges}</td>
            <td class="col-email">${emailBadges}</td>
            <td class="col-addr"><div class="addr-snippet" title="${escapeHtml(lead.address || '')}">${escapeHtml((lead.address || '—').slice(0, 140))}</div></td>
            <td class="col-web">${websiteLink}</td>
            <td class="col-source">${sourceLink}</td>
            <td class="col-pages" style="text-align:center;font-weight:600;color:#475569">${lead.child_pages_crawled || 0}</td>
            <td class="col-status"><span class="badge-tag badge-verified"><i class="fa-solid fa-check-double"></i> Verified</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function filterLeadsTable(query) {
    if (!query) { renderLeadsTable(allLeads); return; }
    const q = query.toLowerCase();
    renderLeadsTable(allLeads.filter(l =>
        (l.business_name || '').toLowerCase().includes(q) ||
        (l.district || '').toLowerCase().includes(q) ||
        (l.category || '').toLowerCase().includes(q) ||
        (l.mobile_numbers || '').includes(q) ||
        (l.email_addresses || '').toLowerCase().includes(q) ||
        (l.address || '').toLowerCase().includes(q)
    ));
}

// ── BUTTON STATE ─────────────────────────────────────────────────────────────
function updateControlsState(status) {
    const btnAuto = document.getElementById("btnAutoProcess");
    const btnPanIndia = document.getElementById("btnPanIndiaAutoProcess");
    const btnDiscover = document.getElementById("btnDiscover");
    const btnScrapeAll = document.getElementById("btnScrapeAll");
    const btnScrapeSelected = document.getElementById("btnScrapeSelected");
    const btnPause = document.getElementById("btnPause");
    const btnResume = document.getElementById("btnResume");
    const btnStop = document.getElementById("btnStop");

    const isBusy = (status === "running" || status === "discovering");
    if (btnAuto) btnAuto.disabled = isBusy;
    if (btnPanIndia) btnPanIndia.disabled = isBusy;

    if (status === "running" || status === "discovering") {
        btnDiscover.disabled = true; btnScrapeAll.disabled = true; btnScrapeSelected.disabled = true;
        btnPause.disabled = false; btnResume.disabled = true; btnStop.disabled = false;
    } else if (status === "paused") {
        btnDiscover.disabled = true; btnScrapeAll.disabled = true; btnScrapeSelected.disabled = true;
        btnPause.disabled = true; btnResume.disabled = false; btnStop.disabled = false;
    } else if (status === "awaiting_selection") {
        btnDiscover.disabled = false;
        btnScrapeAll.disabled = (discoveredCandidates.length === 0);
        btnScrapeSelected.disabled = (discoveredCandidates.length === 0);
        btnPause.disabled = true; btnResume.disabled = true; btnStop.disabled = true;
    } else { // idle, stopped, completed
        btnDiscover.disabled = false;
        btnScrapeAll.disabled = (discoveredCandidates.length === 0);
        btnScrapeSelected.disabled = (discoveredCandidates.length === 0);
        btnPause.disabled = true; btnResume.disabled = true; btnStop.disabled = true;
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
