/* ── Smart Monitor Class — Dashboard JS ──────────────────────── */
let performanceChart;
let studentsData  = [];
let cameraActive  = false;
let currentMode   = 'camera';   // set by initSourceMode()

// ── Toast notifications ──────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast-smc toast-${type}`;
    toast.setAttribute('role', 'status');
    const icons = { success: 'check-circle', error: 'exclamation-circle', info: 'info-circle' };
    toast.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ── Performance chart ────────────────────────────────────────
function calculatePerformanceDistribution() {
    const labels = [T.perf_very_low, T.perf_low, T.perf_medium, T.perf_high, T.perf_very_high];
    const counts = [0, 0, 0, 0, 0];
    studentsData.forEach(student => {
        const positive = (student.emotions.happy?.score || 0) +
                         (student.emotions.surprise?.score || 0);
        const negative = (student.emotions.angry?.score || 0) +
                         (student.emotions.disgust?.score || 0) +
                         (student.emotions.fear?.score || 0) +
                         (student.emotions.sad?.score || 0);
        const performance = (positive - negative) / 2;
        if      (performance < -0.5) counts[0]++;
        else if (performance < -0.1) counts[1]++;
        else if (performance <  0.3) counts[2]++;
        else if (performance <  0.7) counts[3]++;
        else                         counts[4]++;
    });
    return { labels, counts };
}

function initializeChart() {
    const canvas = document.getElementById('performanceChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const performanceData = calculatePerformanceDistribution();
    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: performanceData.labels,
            datasets: [{
                label: T.num_students,
                data: performanceData.counts,
                backgroundColor: ['#e74c3c','#f39c12','#f1c40f','#2ecc71','#27ae60'],
                borderColor:     ['#c0392b','#e67e22','#f39c12','#27ae60','#229954'],
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    title: { display: true, text: T.num_students }
                },
                x: {
                    title: { display: true, text: T.perf_level }
                }
            }
        }
    });
}

// ── Stats ────────────────────────────────────────────────────
function calculatePositiveScore() {
    if (studentsData.length === 0) return 0;
    let totalPositive = 0;
    studentsData.forEach(student => {
        const positive = (student.emotions.happy?.score || 0) +
                         (student.emotions.surprise?.score || 0);
        const negative = (student.emotions.angry?.score || 0) +
                         (student.emotions.disgust?.score || 0) +
                         (student.emotions.fear?.score || 0) +
                         (student.emotions.sad?.score || 0);
        totalPositive += Math.max(0, (positive - negative) / 2);
    });
    return Math.round((totalPositive / studentsData.length) * 100);
}

function updateStats() {
    const totalEl = document.getElementById('totalStudents');
    if (totalEl) totalEl.textContent = studentsData.length;
    
    if (studentsData.length > 0) {
        const avg = (key) => studentsData.reduce((s, st) => s + (st.emotions[key]?.score || 0), 0) / studentsData.length;
        
        const hapEl = document.getElementById('avgHappiness');
        const conEl = document.getElementById('avgConfidence');
        const ferEl = document.getElementById('avgFear');
        
        if (hapEl) hapEl.textContent = Math.round(avg('happy')    * 100) + '%';
        if (conEl) conEl.textContent = Math.round(avg('surprise') * 100) + '%';
        if (ferEl) ferEl.textContent = Math.round(avg('fear')     * 100) + '%';
    }
    
    const posEl = document.getElementById('positiveScore');
    if (posEl) posEl.textContent = calculatePositiveScore() + '%';
}

// ── Students table ───────────────────────────────────────────
function renderStudentsTable() {
    const EMOTIONS = [
        { key: 'angry',   cls: 'smc-angry'   },
        { key: 'disgust', cls: 'smc-disgust'  },
        { key: 'fear',    cls: 'smc-fear'     },
        { key: 'happy',   cls: 'smc-happy'    },
        { key: 'sad',     cls: 'smc-sad'      },
        { key: 'surprise',cls: 'smc-surprise' },
        { key: 'neutral', cls: 'smc-neutral'  },
    ];
    const tbody = document.getElementById('studentsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (studentsData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">
            <i class="fas fa-users fa-2x d-block mb-2 opacity-25"></i>
            ${T.no_data_camera}
        </td></tr>`;
        return;
    }
    studentsData.forEach((student, index) => {
        // Calculate performance (same logic as chart)
        const pos = (student.emotions.happy?.score || 0) + (student.emotions.surprise?.score || 0);
        const neg = (student.emotions.angry?.score || 0) + (student.emotions.disgust?.score || 0) + 
                    (student.emotions.fear?.score || 0) + (student.emotions.sad?.score || 0);
        const perf = Math.round(((pos - neg) / 2) * 100);
        
        let perfClass = 'text-muted';
        if (perf > 30) perfClass = 'text-success';
        else if (perf < -10) perfClass = 'text-danger';

        let html = `<td class="text-center text-muted">${index + 1}</td>`;
        html += `<td class="fw-semibold">${student.name}</td>`;
        
        EMOTIONS.forEach(({ key, cls }) => {
            const d = student.emotions[key] || { score: 0, duration: 0 };
            html += `<td class="text-center">
                <span class="${cls} fw-bold">${Math.round(d.score * 100)}%</span>
                <br><small class="text-muted">${(+d.duration).toFixed(1)}min</small>
            </td>`;
        });
        
        html += `<td class="text-center fw-bold ${perfClass}">${perf}%</td>`;
        
        const tr = document.createElement('tr');
        tr.innerHTML = html;
        tbody.appendChild(tr);
    });
}

// ── Input text (report textarea) ─────────────────────────────
function fetchInputText() {
    const el = document.getElementById('input_text');
    if (!el) return;
    fetch('/get_input_text')
        .then(r => r.json())
        .then(d => { el.value = d.input_text || ''; })
        .catch(e => console.error('fetchInputText:', e));
}

// ── Report export ────────────────────────────────────────────
function generateReport() {
    const inputEl = document.getElementById('input_text');
    const useAiEl = document.getElementById('use_ai');
    if (!inputEl) {
        showToast(T.input_data_error, 'error');
        return;
    }
    const inputText = inputEl.value;
    const useAI     = useAiEl ? useAiEl.checked : false;
    if (!inputText.trim()) { showToast(T.input_required, 'error'); return; }

    const btn = event.currentTarget;
    const orig = btn.innerHTML;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> ${T.exporting}`;
    btn.disabled = true;

    fetch('/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `input_text=${encodeURIComponent(inputText)}&use_ai=${useAI ? 'on' : ''}`
    })
    .then(r => r.text())
    .then(html => {
        const doc      = new DOMParser().parseFromString(html, 'text/html');
        const el       = doc.querySelector('#mainReport');
        const reportEl = document.getElementById('mainReport');
        if (el) {
            reportEl.textContent = el.textContent;
            if (el.textContent.startsWith('⚠️')) {
                reportEl.classList.remove('ai-report');
            } else {
                reportEl.classList.add('ai-report');
                reportEl.style.fontFamily = '';
            }
            showToast(T.report_created, 'success');
        } else {
            showToast(T.report_error, 'error');
        }
    })
    .catch(() => showToast(T.report_error, 'error'))
    .finally(() => { btn.innerHTML = orig; btn.disabled = false; });
}

// ── Camera ───────────────────────────────────────────────────
function toggleCamera() {
    const img        = document.getElementById('videoFeed');
    const placeholder= document.getElementById('cameraPlaceholder');
    const dot        = document.getElementById('statusDot');
    const statusTxt  = document.getElementById('statusText');
    const toggleBtn  = document.getElementById('toggleBtn');
    const isVideo    = toggleBtn && toggleBtn.dataset.mode === 'video';

    if (!cameraActive) {
        img.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        if (dot)       { dot.classList.remove('bg-danger'); dot.classList.add('bg-success'); }
        if (statusTxt) statusTxt.textContent = T.online;
        if (toggleBtn) toggleBtn.innerHTML = isVideo
            ? `<i class="fas fa-stop me-1"></i> ${T.stop_video}`
            : `<i class="fas fa-stop me-1"></i> ${T.stop_camera}`;
        cameraActive = true;
        img.onerror = () => {
            img.style.display = 'none';
            if (placeholder) placeholder.style.display = 'flex';
            if (dot)       { dot.classList.remove('bg-success'); dot.classList.add('bg-danger'); }
            if (statusTxt) statusTxt.textContent = T.conn_error;
        };
    } else {
        img.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
        if (dot)       { dot.classList.remove('bg-success'); dot.classList.add('bg-danger'); }
        if (statusTxt) statusTxt.textContent = T.status_offline;
        if (toggleBtn) toggleBtn.innerHTML = isVideo
            ? `<i class="fas fa-play me-1"></i> ${T.play_video}`
            : `<i class="fas fa-play me-1"></i> ${T.turn_on_camera}`;
        cameraActive = false;
    }
}

function captureImage() {
    if (!cameraActive) { showToast(T.turn_on_camera_toast, 'error'); return; }
    fetch('/capture_image', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(r => r.json())
        .then(d => showToast(d.success ? T.capture_success : (`${T.save_error}: ` + d.message), d.success ? 'success' : 'error'))
        .catch(() => showToast(T.not_available, 'error'));
}

// ── Load data ────────────────────────────────────────────────
async function loadData() {
    try {
        const response = await fetch('/api/emotions');
        const data     = await response.json();

        // Update system status indicator
        const dot     = document.getElementById('systemDot');
        const sysTxt  = document.getElementById('systemStatus');
        if (dot)    { dot.classList.remove('bg-danger'); dot.classList.add('bg-success'); }
        if (sysTxt) sysTxt.textContent = T.online;

        studentsData = data.data || [];
        updateStats();
        renderStudentsTable();

        if (performanceChart) { performanceChart.destroy(); }
        initializeChart();

        const lu = document.getElementById('lastUpdate');
        if (lu) lu.textContent = data.last_update
            ? new Date(data.last_update).toLocaleString(document.documentElement.lang || 'vi-VN')
            : (T.no_data || '...');

    } catch (error) {
        console.error('loadData error:', error);
        const dot    = document.getElementById('systemDot');
        const sysTxt = document.getElementById('systemStatus');
        if (dot)    { dot.classList.remove('bg-success'); dot.classList.add('bg-danger'); }
        if (sysTxt) sysTxt.textContent = T.status_offline;
    }
}

function refreshData() {
    const btn = document.getElementById('refreshBtn');
    if (btn) { btn.disabled = true; btn.querySelector('i')?.classList.add('fa-spin'); }
    loadData().finally(() => {
        if (btn) { btn.disabled = false; btn.querySelector('i')?.classList.remove('fa-spin'); }
    });
}

// ── Mode switching ───────────────────────────────────────────
function updateModeUI(mode) {
    currentMode = mode;

    const cameraPanel      = document.getElementById('cameraPanel');
    const videoPanel       = document.getElementById('videoPanel');
    const sourceIcon       = document.getElementById('sourceIcon');
    const sourceTitleText  = document.getElementById('sourceTitleText');
    const switchToCameraBtn= document.getElementById('switchToCameraBtn');
    const switchToVideoBtn = document.getElementById('switchToVideoBtn');
    const statusDot        = document.getElementById('statusDot');
    const statusText       = document.getElementById('statusText');

    if (mode === 'video') {
        if (cameraPanel)      cameraPanel.style.display      = 'none';
        if (videoPanel)       videoPanel.style.display       = 'block';
        if (sourceIcon)       sourceIcon.className           = 'fas fa-film me-2 text-primary';
        if (sourceTitleText)  sourceTitleText.textContent    = T.video_analysis_title;
        if (switchToCameraBtn)switchToCameraBtn.style.display= 'inline-flex';
        if (switchToVideoBtn) switchToVideoBtn.style.display = 'none';
        if (statusDot)  { statusDot.classList.remove('bg-danger'); statusDot.classList.add('bg-success'); }
        if (statusText)       statusText.textContent         = T.analyzing;
    } else {
        if (cameraPanel)      cameraPanel.style.display      = 'block';
        if (videoPanel)       videoPanel.style.display       = 'none';
        if (sourceIcon)       sourceIcon.className           = 'fas fa-camera me-2 text-primary';
        if (sourceTitleText)  sourceTitleText.textContent    = T.live_camera;
        if (switchToCameraBtn)switchToCameraBtn.style.display= 'none';
        if (switchToVideoBtn) switchToVideoBtn.style.display = 'inline-flex';
    }
}

async function switchMode(mode) {
    const btn = mode === 'video'
        ? document.getElementById('switchToVideoBtn')
        : document.getElementById('switchToCameraBtn');
    if (!btn) return;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> ${T.switching}`;

    try {
        const res  = await fetch('/api/switch_mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        });
        const data = await res.json();
        if (data.error) { showToast(data.error, 'error'); return; }

        updateModeUI(data.mode);

        // Reset camera state when switching to camera
        if (data.mode === 'camera' && cameraActive) {
            cameraActive = false;
            const img = document.getElementById('videoFeed');
            const ph  = document.getElementById('cameraPlaceholder');
            if (img) img.style.display = 'none';
            if (ph)  ph.style.display  = 'flex';
            const dot = document.getElementById('statusDot');
            const txt = document.getElementById('statusText');
            if (dot) { dot.classList.remove('bg-success'); dot.classList.add('bg-danger'); }
            if (txt) txt.textContent = 'Offline';
            const tb = document.getElementById('toggleBtn');
            if (tb)  tb.innerHTML = '<i class="fas fa-play me-1"></i> Bật Camera';
        }

        if (data.video_file) {
            const vf = document.getElementById('videoFileName');
            if (vf) vf.textContent = data.video_file;
        }

            showToast(
                mode === 'video' ? `${T.switched_video}: ${data.video_file}` : T.switched_camera,
                'success'
            );
        } catch (e) {
            showToast(T.switch_error, 'error');
            btn.innerHTML = orig;
        } finally {
        btn.disabled = false;
    }
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const cfg = window.SMC_CONFIG || {};
    updateModeUI(cfg.initialMode || 'camera');

    loadData();
    fetchInputText();
    setInterval(loadData,        30000);
    setInterval(fetchInputText,   5000);
});
