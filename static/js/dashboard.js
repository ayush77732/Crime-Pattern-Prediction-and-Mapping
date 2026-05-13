/* ============================
   dashboard.js - Dashboard Logic
   Upload, Charts, Heatmap, AI Chat, Report
   ============================ */

// ---- State ----
let datasetLoaded = false;
let currentFilters = {};
let map = null;
let mapMarkers = [];
let charts = {};

// ---- DOM Elements ----
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const uploadSuccess = document.getElementById('uploadSuccess');
const filtersSection = document.getElementById('filters-section');
const statsSection = document.getElementById('stats-section');
const analysisSection = document.getElementById('analysis-section');
const alertsSection = document.getElementById('alerts-section');
const heatmapSection = document.getElementById('heatmap-section');
const hotspotSection = document.getElementById('hotspot-section');
const forecastSection = document.getElementById('forecast-section');
const aiSection = document.getElementById('ai-section');
const reportSection = document.getElementById('report-section');
const analyzeBtn = document.getElementById('analyzeBtn');
const statusIndicator = document.getElementById('statusIndicator');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');

// ---- Initialize ----
document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    setupFilters();
    setupChat();
    setupSidebar();
    setupReport();
});

// ---- Sidebar ----
function setupSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Nav item clicks
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            sidebar.classList.remove('open');
        });
    });
}

// ---- Upload ----
function setupUpload() {
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) uploadFile(file);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) uploadFile(fileInput.files[0]);
    });
}

async function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('Please upload a CSV file.');
        return;
    }

    showLoading('Uploading and processing dataset...');
    uploadArea.style.display = 'none';
    uploadProgress.style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();

        hideLoading();

        if (data.status === 'success') {
            uploadProgress.style.display = 'none';
            uploadSuccess.style.display = 'block';
            document.getElementById('successMessage').textContent = data.message;

            const meta = data.metadata;
            let details = [];
            if (meta.filters.states) details.push(`${meta.filters.states.length} States`);
            if (meta.filters.cities) details.push(`${meta.filters.cities.length} Cities`);
            if (meta.filters.crime_types) details.push(`${meta.filters.crime_types.length} Crime Types`);
            if (meta.filters.years) details.push(`${meta.filters.years.length} Years`);
            document.getElementById('successDetails').textContent = details.join(' • ');

            populateFilters(meta.filters);
            datasetLoaded = true;

            // Update status
            statusIndicator.innerHTML = '<span class="status-dot online"></span> Dataset Loaded';

            // Show all sections
            filtersSection.style.display = 'block';
            aiSection.style.display = 'block';
            reportSection.style.display = 'block';

            // Auto-analyze with default filters
            await runAnalysis();
        } else {
            uploadProgress.style.display = 'none';
            uploadArea.style.display = 'block';
            alert('Error: ' + data.message);
        }
    } catch (err) {
        hideLoading();
        uploadProgress.style.display = 'none';
        uploadArea.style.display = 'block';
        alert('Upload failed: ' + err.message);
    }
}

// ---- Filters ----
function setupFilters() {
    analyzeBtn.addEventListener('click', () => runAnalysis());

    // Dynamic city filter based on state
    document.getElementById('stateFilter').addEventListener('change', async (e) => {
        const state = e.target.value;
        try {
            const res = await fetch('/api/cities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state })
            });
            const data = await res.json();
            const citySelect = document.getElementById('cityFilter');
            citySelect.innerHTML = '<option value="all">All Cities</option>';
            (data.cities || []).forEach(city => {
                const opt = document.createElement('option');
                opt.value = city;
                opt.textContent = city;
                citySelect.appendChild(opt);
            });
        } catch (e) {
            console.error('Error fetching cities:', e);
        }
    });
}

function populateFilters(filters) {
    const stateSelect = document.getElementById('stateFilter');
    const citySelect = document.getElementById('cityFilter');
    const crimeSelect = document.getElementById('crimeFilter');
    const yearSelect = document.getElementById('yearFilter');

    stateSelect.innerHTML = '<option value="all">All States</option>';
    (filters.states || []).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s; opt.textContent = s;
        stateSelect.appendChild(opt);
    });

    citySelect.innerHTML = '<option value="all">All Cities</option>';
    (filters.cities || []).forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.textContent = c;
        citySelect.appendChild(opt);
    });

    crimeSelect.innerHTML = '<option value="all">All Crime Types</option>';
    (filters.crime_types || []).forEach(ct => {
        const opt = document.createElement('option');
        opt.value = ct; opt.textContent = ct;
        crimeSelect.appendChild(opt);
    });

    yearSelect.innerHTML = '<option value="all">All Years</option>';
    (filters.years || []).forEach(y => {
        const opt = document.createElement('option');
        opt.value = y; opt.textContent = y;
        yearSelect.appendChild(opt);
    });
}

function getFilters() {
    return {
        state: document.getElementById('stateFilter').value,
        city: document.getElementById('cityFilter').value,
        crime_type: document.getElementById('crimeFilter').value,
        year: document.getElementById('yearFilter').value
    };
}

// ---- Analysis ----
async function runAnalysis() {
    if (!datasetLoaded) return;

    const filters = getFilters();
    currentFilters = filters;
    showLoading('Analyzing crime data...');

    try {
        // Parallel API calls
        const [analysisRes, predictRes, heatmapRes] = await Promise.all([
            fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(filters)
            }),
            fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(filters)
            }),
            fetch('/api/heatmap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(filters)
            })
        ]);

        const analysis = await analysisRes.json();
        const prediction = await predictRes.json();
        const heatmapData = await heatmapRes.json();

        hideLoading();

        if (analysis.status === 'success') {
            // Show sections
            statsSection.style.display = 'block';
            analysisSection.style.display = 'block';
            heatmapSection.style.display = 'block';
            hotspotSection.style.display = 'block';
            forecastSection.style.display = 'block';
            alertsSection.style.display = 'block';

            // Update stats
            updateStats(analysis.stats, analysis.risk_zones);

            // Render charts
            renderCrimeTypeChart(analysis.crime_type_distribution);
            renderYearlyTrendChart(analysis.yearly_trend);
            renderReportedSolvedChart(analysis.reported_vs_solved);
            renderCityComparisonChart(analysis.city_comparison);

            // Render alerts
            renderAlerts(analysis.high_risk_alerts);
        }

        if (prediction.status === 'success') {
            renderHotspots(prediction.hotspots);
            renderForecast(prediction.forecast, prediction.prediction);
        }

        if (heatmapData.status === 'success') {
            renderHeatmap(heatmapData.heatmap);
        }

    } catch (err) {
        hideLoading();
        console.error('Analysis error:', err);
        alert('Error during analysis: ' + err.message);
    }
}

// ---- Stats ----
function updateStats(stats, riskZones) {
    animateNumber('statTotalCases', stats.total_cases || 0);
    document.getElementById('statHighRisk').textContent = riskZones ? riskZones.high.length : 0;
    document.getElementById('statAreas').textContent = (stats.total_cities || stats.total_states || 0);
    document.getElementById('statYears').textContent = stats.year_range || '-';
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    const duration = 1000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        el.textContent = current.toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// ---- Charts ----
const chartColors = {
    primary: '#4f46e5',
    purple: '#7c3aed',
    pink: '#ec4899',
    red: '#ef4444',
    orange: '#f59e0b',
    green: '#10b981',
    blue: '#3b82f6',
    teal: '#14b8a6',
    palette: [
        '#4f46e5', '#7c3aed', '#ec4899', '#ef4444', '#f59e0b',
        '#10b981', '#3b82f6', '#14b8a6', '#8b5cf6', '#f97316',
        '#06b6d4', '#84cc16', '#e11d48', '#6366f1', '#d946ef'
    ]
};

function getChartDefaults() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: '#9ca3af', font: { family: 'Inter', size: 11 } }
            }
        },
        scales: {
            x: {
                ticks: { color: '#6b7280', font: { family: 'Inter', size: 10 } },
                grid: { color: 'rgba(255,255,255,0.04)' }
            },
            y: {
                ticks: { color: '#6b7280', font: { family: 'Inter', size: 10 } },
                grid: { color: 'rgba(255,255,255,0.04)' }
            }
        }
    };
}

function destroyChart(key) {
    if (charts[key]) {
        charts[key].destroy();
        charts[key] = null;
    }
}

function renderCrimeTypeChart(data) {
    destroyChart('crimeType');
    const ctx = document.getElementById('crimeTypeChart').getContext('2d');

    charts.crimeType = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: chartColors.palette.slice(0, data.labels.length),
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#9ca3af',
                        font: { family: 'Inter', size: 10 },
                        boxWidth: 12,
                        padding: 10,
                        generateLabels: function (chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => ({
                                text: label.length > 22 ? label.substring(0, 22) + '...' : label,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                hidden: false,
                                index: i
                            }));
                        }
                    }
                }
            }
        }
    });
}

function renderYearlyTrendChart(data) {
    destroyChart('yearlyTrend');
    const ctx = document.getElementById('yearlyTrendChart').getContext('2d');

    charts.yearlyTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Total Cases',
                data: data.values,
                borderColor: chartColors.primary,
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: getChartDefaults()
    });
}

function renderReportedSolvedChart(data) {
    destroyChart('reportedSolved');
    const ctx = document.getElementById('reportedSolvedChart').getContext('2d');

    charts.reportedSolved = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Reported',
                    data: data.reported,
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Solved',
                    data: data.solved,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: getChartDefaults()
    });
}

function renderCityComparisonChart(data) {
    destroyChart('cityComparison');
    const ctx = document.getElementById('cityComparisonChart').getContext('2d');

    charts.cityComparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Cases',
                data: data.values,
                backgroundColor: chartColors.palette.slice(0, data.labels.length).map(c => c + 'bb'),
                borderColor: chartColors.palette.slice(0, data.labels.length),
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            ...getChartDefaults(),
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// ---- Alerts ----
function renderAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p style="color: var(--text-2); text-align: center; padding: 20px;">No high-risk alerts at this time ✅</p>';
        return;
    }

    container.innerHTML = alerts.map(a => `
        <div class="alert-card ${a.risk_level.toLowerCase()}">
            <div class="alert-header">
                <span class="alert-badge">⚠️ ${a.risk_level}</span>
                <span class="alert-area">${a.area}</span>
            </div>
            <div class="alert-details">
                <p>Growth: <span style="color: var(--red);">${a.growth_rate > 0 ? '+' : ''}${a.growth_rate}%</span></p>
                <p>Latest: <span>${a.latest_cases.toLocaleString()}</span></p>
                <p>Previous: <span>${a.previous_cases.toLocaleString()}</span></p>
                <p>YoY Change: <span style="color: var(--red);">+${(a.latest_cases - a.previous_cases).toLocaleString()}</span></p>
            </div>
        </div>
    `).join('');
}

// ---- Heatmap ----
function renderHeatmap(data) {
    if (!data || data.length === 0) return;

    if (map) {
        map.remove();
        map = null;
    }

    // Update custom title text based on filters
    const locSpan = document.getElementById('mapTitleLocation');
    if (locSpan) {
        if (currentFilters.city && currentFilters.city !== 'all') {
            locSpan.textContent = "in " + currentFilters.city;
        } else if (currentFilters.state && currentFilters.state !== 'all') {
            locSpan.textContent = "in " + currentFilters.state;
        } else {
            locSpan.textContent = "in India";
        }
    }

    // Initialize map with a dark theme tile layer (CartoDB Dark Matter)
    map = L.map('crimeMap', { zoomControl: false }).setView([22.5, 78.9], 5);

    // Add zoom control to top right to not block legend/title
    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap, © CARTO',
        maxZoom: 18
    }).addTo(map);

    mapMarkers = [];
    const heatPoints = [];

    data.forEach(point => {
        // Collect points for L.heatLayer
        // Intensity should be scaled for visual weight in the heatmap
        const heatWeight = Math.max(0.1, point.intensity);
        heatPoints.push([point.lat, point.lng, heatWeight]);

        // Create invisible interactive points for tooltips
        const marker = L.circleMarker([point.lat, point.lng], {
            radius: 25,
            fillOpacity: 0,
            color: 'transparent',
            weight: 0
        }).addTo(map);

        const tooltipHtml = `
            <div class="custom-map-popup">
                <h4>${point.name}</h4>
                <ul>
                    <li>High Crime Area</li>
                    <li>Total Crimes: ${point.cases.toLocaleString()}</li>
                    <li>Most Common Crime: ${point.most_common_crime || 'Unknown'}</li>
                </ul>
            </div>
        `;

        marker.bindTooltip(tooltipHtml, {
            direction: 'top',
            className: 'custom-map-popup-container',
            opacity: 1,
            offset: L.point(0, -10)
        });

        mapMarkers.push(marker);
    });

    // Add True Heatmap Layer
    if (typeof L.heatLayer !== 'undefined') {
        L.heatLayer(heatPoints, {
            radius: 45,
            blur: 35,
            maxZoom: 14,
            max: 1.0,
            minOpacity: 0.4, // Forces baseline opacity/color to be highly visible
            gradient: {
                0.4: '#4ade80', // Maps minimum opacity to Green
                0.6: '#facc15', // Yellow
                0.8: '#ef4444', // Red
                1.0: '#b91c1c'  // Intense Red
            }
        }).addTo(map);
    } else {
        console.error("Leaflet.heat plugin not loaded.");
    }

    // Fit bounds
    if (mapMarkers.length > 0) {
        const group = L.featureGroup(mapMarkers);
        map.fitBounds(group.getBounds().pad(0.1), { maxZoom: 11 });
    }

    // Fix map rendering
    setTimeout(() => map.invalidateSize(), 100);
}

// ---- Hotspots ----
function renderHotspots(hotspots) {
    const tbody = document.getElementById('hotspotBody');
    if (!hotspots || hotspots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-2); padding:24px;">No hotspot data available</td></tr>';
        return;
    }

    tbody.innerHTML = hotspots.map((h, i) => {
        const riskClass = h.risk_score > 70 ? 'risk-high' : (h.risk_score > 40 ? 'risk-moderate' : 'risk-low');
        const trendClass = h.trend === 'increasing' ? 'trend-up' : 'trend-down';
        const trendIcon = h.trend === 'increasing' ? '📈' : '📉';

        return `
            <tr>
                <td><strong>${i + 1}</strong></td>
                <td><strong>${h.area}</strong></td>
                <td>${h.current_cases.toLocaleString()}</td>
                <td>${h.predicted_cases.toLocaleString()}</td>
                <td class="${trendClass}">${h.growth_rate > 0 ? '+' : ''}${h.growth_rate}%</td>
                <td><span class="risk-badge ${riskClass}">${h.risk_score.toFixed(0)}/100</span></td>
                <td class="${trendClass}">${trendIcon} ${h.trend}</td>
            </tr>
        `;
    }).join('');
}

// ---- Forecast ----
function renderForecast(forecast, prediction) {
    destroyChart('forecast');

    if (!forecast || !forecast.years || forecast.years.length === 0) return;

    const ctx = document.getElementById('forecastChart').getContext('2d');

    const datasets = [
        {
            label: 'Actual Cases',
            data: forecast.actual,
            borderColor: chartColors.primary,
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            borderWidth: 2.5,
            fill: false,
            tension: 0.4,
            pointRadius: 5,
            pointBackgroundColor: chartColors.primary
        },
        {
            label: 'Predicted',
            data: forecast.predicted,
            borderColor: chartColors.orange,
            borderDash: [8, 4],
            borderWidth: 2.5,
            fill: false,
            tension: 0.4,
            pointRadius: 5,
            pointBackgroundColor: chartColors.orange
        }
    ];

    if (forecast.upper_bound) {
        datasets.push({
            label: 'Upper Bound',
            data: forecast.upper_bound,
            borderColor: 'transparent',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            fill: '+1',
            pointRadius: 0
        });
        datasets.push({
            label: 'Lower Bound',
            data: forecast.lower_bound,
            borderColor: 'transparent',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            fill: '-1',
            pointRadius: 0
        });
    }

    charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: forecast.years,
            datasets: datasets
        },
        options: {
            ...getChartDefaults(),
            plugins: {
                legend: {
                    labels: {
                        color: '#9ca3af',
                        font: { family: 'Inter', size: 11 },
                        filter: (item) => item.text !== 'Upper Bound' && item.text !== 'Lower Bound'
                    }
                }
            }
        }
    });

    // Forecast metrics
    const metricsEl = document.getElementById('forecastMetrics');
    if (prediction) {
        metricsEl.innerHTML = `
            <div class="metric-card">
                <h4>Predicted Cases</h4>
                <div class="metric-value">${(prediction.predicted_cases || 0).toLocaleString()}</div>
            </div>
            <div class="metric-card">
                <h4>Confidence Level</h4>
                <div class="metric-value">${prediction.confidence || 0}%</div>
            </div>
            <div class="metric-card">
                <h4>Method</h4>
                <div class="metric-value" style="font-size:13px; color: var(--text-2);">${prediction.method || 'N/A'}</div>
            </div>
        `;
    }
}

// ---- AI Chat ----
function setupChat() {
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');

    chatSend.addEventListener('click', () => sendMessage());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Suggestion chips
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('chip')) {
            const question = e.target.getAttribute('data-q');
            if (question) {
                chatInput.value = question;
                sendMessage();
            }
        }
    });
}

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addChatMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, filters: getFilters() })
        });
        const data = await res.json();

        removeTypingIndicator(typingId);

        if (data.status === 'success') {
            addChatMessage(data.answer, 'bot');
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        addChatMessage('Connection error. Please check if the server is running.', 'bot');
    }
}

function addChatMessage(text, type) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `chat-message ${type}`;

    const icon = type === 'bot' ? 'fa-robot' : 'fa-user';

    div.innerHTML = `
        <div class="message-avatar"><i class="fas ${icon}"></i></div>
        <div class="message-content"><p>${formatMessage(text)}</p></div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function formatMessage(text) {
    // Convert markdown bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert newlines to br
    text = text.replace(/\n/g, '<br>');
    return text;
}

function addTypingIndicator() {
    const container = document.getElementById('chatMessages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'chat-message bot';
    div.id = id;
    div.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <p><span class="typing-dots">
                <span>●</span><span>●</span><span>●</span>
            </span></p>
        </div>
    `;

    // Add typing animation
    const style = document.createElement('style');
    style.textContent = `
        .typing-dots span {
            animation: typingDot 1.4s infinite;
            opacity: 0.3;
            font-size: 18px;
            margin-right: 2px;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typingDot {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }
    `;
    if (!document.getElementById('typing-style')) {
        style.id = 'typing-style';
        document.head.appendChild(style);
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ---- Report ----
function setupReport() {
    document.getElementById('generateReport').addEventListener('click', async () => {
        if (!datasetLoaded) {
            alert('Please upload a dataset first.');
            return;
        }

        showLoading('Generating PDF report...');

        try {
            const res = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(getFilters())
            });

            hideLoading();

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'CrimePredict_Report.pdf';
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const data = await res.json();
                alert('Report generation failed: ' + data.message);
            }
        } catch (err) {
            hideLoading();
            alert('Error generating report: ' + err.message);
        }
    });
}

// ---- Loading ----
function showLoading(text) {
    loadingText.textContent = text || 'Processing...';
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}
