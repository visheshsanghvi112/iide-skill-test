document.addEventListener('DOMContentLoaded', () => {
    // Current Chart instances registry (to destroy and rebuild on reload)
    const charts = {};

    // Elements
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const refreshBtn = document.getElementById('refresh-data-btn');

    // SQL Sandbox Elements
    const sqlEditor = document.getElementById('sql-editor');
    const runSqlBtn = document.getElementById('run-sql-btn');
    const clearSqlBtn = document.getElementById('clear-sql-btn');
    const queryResultMeta = document.getElementById('query-result-meta');
    const queryStatusBadge = document.getElementById('query-status-badge');
    const queryEmptyState = document.getElementById('query-empty-state');
    const queryResultsTable = document.getElementById('query-results-table');
    const queryResultsHeaders = document.getElementById('query-results-headers');
    const queryResultsRows = document.getElementById('query-results-rows');
    const exampleBtns = document.querySelectorAll('.example-query-btn');

    // --- Tab Switching Navigation ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');

            // Set active class on nav links
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Switch content panels
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`tab-${tabId}`).classList.add('active');

            // Scroll main content back to top to prevent header truncation
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.scrollTop = 0;
            }

            // Set header texts
            if (tabId === 'dashboard') {
                pageTitle.innerText = "Executive Dashboard";
                pageSubtitle.innerText = "Real-time placement funnel metrics and recruitment performance analysis";
                refreshBtn.style.display = "inline-flex";
            } else if (tabId === 'schema') {
                pageTitle.innerText = "Relational Schema Model";
                pageSubtitle.innerText = "Third Normal Form (3NF) relational mapping and entity relationships";
                refreshBtn.style.display = "none";
            } else if (tabId === 'sandbox') {
                pageTitle.innerText = "SQL Query Sandbox";
                pageSubtitle.innerText = "Execute ad-hoc analytical queries directly on the live SQLite database";
                refreshBtn.style.display = "none";
            }
        });
    });

    // --- Accordion Reference Panel ---
    const accordions = document.querySelectorAll('.accordion-title');
    accordions.forEach(acc => {
        acc.addEventListener('click', () => {
            const item = acc.parentElement;
            item.classList.toggle('active');
        });
    });

    // --- Load Examples ---
    exampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const sql = btn.getAttribute('data-sql');
            sqlEditor.value = sql;
            runSqlQuery();
        });
    });

    // --- Refresh Data Button ---
    refreshBtn.addEventListener('click', () => {
        loadDashboardStats();
    });

    // --- Load Stats and Populate Charts ---
    async function loadDashboardStats() {
        try {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading...';
            
            const res = await fetch('/api/dashboard-stats');
            const data = await res.json();
            
            populateKPIs(data.funnel);
            renderFunnelChart(data.funnel);
            renderKnockoffsChart(data.knock_off_reasons);
            renderCancellationsChart(data.interview_cancellations);
            renderLocationChart(data.location_dist);
            renderSkillsChart(data.skill_counts);
            renderRolesChart(data.top_roles);
            renderBatchesChart(data.batch_performance);
            populateDiscrepancyTable(data.discrepancies);

        } catch (error) {
            console.error("Error loading dashboard statistics:", error);
            alert("Could not load placement statistics. Make sure the backend server is running.");
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa-solid fa-rotate"></i> Refresh Analytics';
        }
    }

    // --- Helper to Destroy Chart and Get Context ---
    function prepareCanvas(name, canvasId) {
        if (charts[name]) {
            charts[name].destroy();
            charts[name] = null;
        }
        return document.getElementById(canvasId).getContext('2d');
    }

    // --- 1. Populate KPI Cards ---
    function populateKPIs(funnel) {
        document.getElementById('kpi-registered').innerText = funnel.registered;
        document.getElementById('kpi-eligible').innerText = funnel.eligible;
        document.getElementById('kpi-placed').innerText = funnel.placed;
        
        // Percentages
        const eligiblePct = ((funnel.eligible / funnel.registered) * 100).toFixed(1);
        const hiredPct = ((funnel.placed / funnel.eligible) * 100).toFixed(1);
        
        document.getElementById('eligible-pct').innerText = `${eligiblePct}%`;
        document.getElementById('hired-pct').innerText = `${hiredPct}%`;
    }

    // --- 2. Ingestion Funnel Chart ---
    function renderFunnelChart(funnel) {
        const ctx = prepareCanvas('funnel', 'chart-funnel');
        const labels = ['1. Registered Enrolments', '2. Placement Eligible', '3. Submitted Applications', '4. Interviewed Rounds', '5. Final Hired'];
        const values = [funnel.registered, funnel.eligible, funnel.applied, funnel.interviewed, funnel.placed];
        
        charts['funnel'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Candidates Count',
                    data: values,
                    backgroundColor: [
                        'rgba(12, 95, 244, 0.7)',   // Zoho Blue
                        'rgba(14, 165, 233, 0.7)',  // Cyan
                        'rgba(16, 185, 129, 0.7)',  // Emerald Green
                        'rgba(245, 158, 11, 0.7)',  // Amber Orange
                        'rgba(244, 63, 94, 0.7)'    // Rose Red
                    ],
                    borderColor: [
                        '#0c5ff4', '#0ea5e9', '#10b981', '#f59e0b', '#f43f5e'
                    ],
                    borderWidth: 1.5,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const val = context.raw;
                                if (index === 0) return `${val} students`;
                                const prev = context.dataset.data[index - 1];
                                const conversion = ((val / prev) * 100).toFixed(1);
                                return `${val} candidates (${conversion}% stage conversion)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(0,0,0,0.06)' },
                        ticks: { color: '#64748b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 11 } }
                    }
                }
            }
        });
    }

    // --- 3. Enrolment Knock-off Reasons ---
    function renderKnockoffsChart(reasons) {
        const ctx = prepareCanvas('knockoffs', 'chart-knockoffs');
        const labels = reasons.map(r => r.knocked_off_reason);
        const values = reasons.map(r => r.count);
        
        charts['knockoffs'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        'rgba(244, 63, 94, 0.75)',
                        'rgba(124, 58, 237, 0.75)',
                        'rgba(245, 158, 11, 0.75)',
                        'rgba(14, 165, 233, 0.75)',
                        'rgba(16, 185, 129, 0.75)'
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 1.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#64748b', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // --- 4. Interview Cancellations ---
    function renderCancellationsChart(cancels) {
        const ctx = prepareCanvas('cancellations', 'chart-cancellations');
        const labels = cancels.map(c => c.cancellation_reason.substring(0, 25) + (c.cancellation_reason.length > 25 ? '...' : ''));
        const values = cancels.map(c => c.count);
        
        charts['cancellations'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: 'rgba(245, 158, 11, 0.7)',
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { color: 'rgba(0,0,0,0.06)' },
                        ticks: { color: '#64748b' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // --- 5. Locations preference ---
    function renderLocationChart(locations) {
        const ctx = prepareCanvas('locations', 'chart-locations');
        const labels = locations.map(l => l.location);
        const values = locations.map(l => l.count);
        
        charts['locations'] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        'rgba(14, 165, 233, 0.75)',
                        'rgba(124, 58, 237, 0.75)',
                        'rgba(244, 63, 94, 0.75)'
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 1.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#64748b', font: { size: 11 } }
                    }
                }
            }
        });
    }

    // --- 6. Top Skills ---
    function renderSkillsChart(skills) {
        const ctx = prepareCanvas('skills', 'chart-skills');
        const labels = skills.map(s => s.skill).slice(0, 8);
        const values = skills.map(s => s.count).slice(0, 8);
        
        charts['skills'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { color: 'rgba(0,0,0,0.06)' },
                        ticks: { color: '#64748b' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // --- 7. Top Job Roles ---
    function renderRolesChart(roles) {
        const ctx = prepareCanvas('roles', 'chart-roles');
        const labels = roles.map(r => r.role).slice(0, 6);
        const values = roles.map(r => r.count).slice(0, 6);
        
        charts['roles'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: 'rgba(14, 165, 233, 0.7)',
                    borderColor: '#0ea5e9',
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        grid: { color: 'rgba(0,0,0,0.06)' },
                        ticks: { color: '#64748b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 9 } }
                    }
                }
            }
        });
    }

    // --- 8. Batch Performance ---
    function renderBatchesChart(batches) {
        const ctx = prepareCanvas('batches', 'chart-batches');
        
        // Take top 6 batches to avoid cluttering
        const sliced = batches.slice(0, 6);
        const labels = sliced.map(b => b.batch_name.split(' - ')[0].replace('ACDM & PCDMS ', ''));
        const registered = sliced.map(b => b.registered);
        const eligible = sliced.map(b => b.eligible);
        const hired = sliced.map(b => b.hired);
        
        charts['batches'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Registered',
                        data: registered,
                        backgroundColor: 'rgba(124, 58, 237, 0.6)',
                        borderColor: '#7c3aed',
                        borderWidth: 1.5,
                        borderRadius: 4
                    },
                    {
                        label: 'Eligible (Candidates)',
                        data: eligible,
                        backgroundColor: 'rgba(14, 165, 233, 0.6)',
                        borderColor: '#0ea5e9',
                        borderWidth: 1.5,
                        borderRadius: 4
                    },
                    {
                        label: 'Placed (Hired)',
                        data: hired,
                        backgroundColor: 'rgba(16, 185, 129, 0.6)',
                        borderColor: '#10b981',
                        borderWidth: 1.5,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#64748b', font: { size: 10 } }
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(0,0,0,0.06)' },
                        ticks: { color: '#64748b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // --- 9. Populate Discrepancy Table ---
    function populateDiscrepancyTable(discrepancies) {
        const tbody = document.getElementById('discrepancy-rows');
        tbody.innerHTML = '';
        
        discrepancies.forEach(row => {
            const tr = document.createElement('tr');
            
            const desc = row.candidate_id 
                ? "Candidate has 0 Placements/Hired updates in Applications tracker despite Enrolment = 'Hired'"
                : "Missing placement details entirely in candidates tracker";
            
            tr.innerHTML = `
                <td><code>${row.enrolment_id}</code></td>
                <td><code>${row.candidate_id || 'NULL'}</code></td>
                <td>${row.name}</td>
                <td><span class="badge badge-warning">${row.stage}</span></td>
                <td class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> ${desc}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // --- SQL Sandbox Execute Query ---
    async function runSqlQuery() {
        const query = sqlEditor.value.trim();
        if (!query) return;

        // Reset UI States
        queryStatusBadge.className = 'badge status-running';
        queryStatusBadge.innerText = 'Running...';
        queryResultMeta.innerText = 'Sending request to SQLite database...';
        queryEmptyState.style.display = 'none';
        queryResultsTable.style.display = 'none';

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            
            const data = await res.json();
            
            if (data.error) {
                showQueryError(data.error);
                return;
            }
            
            queryStatusBadge.className = 'badge status-success';
            queryStatusBadge.innerText = 'Success';
            
            if (data.columns && data.rows) {
                queryResultMeta.innerText = `Fetched ${data.row_count} rows.`;
                renderQueryResultGrid(data.columns, data.rows);
            } else {
                queryResultMeta.innerText = data.message || "Query completed.";
                queryEmptyState.style.display = 'flex';
                queryEmptyState.innerHTML = `
                    <i class="fa-solid fa-circle-check" style="color: #00ff88;"></i>
                    <p>${data.message || 'Operation successful'}</p>
                    <span style="font-size: 12px; color: #8c88af;">Rows affected: ${data.row_count}</span>
                `;
            }
            
        } catch (error) {
            console.error("SQL query runner error:", error);
            showQueryError(error.message || "Network request failed.");
        }
    }

    // --- Show SQL Error in Table UI ---
    function showQueryError(errText) {
        queryStatusBadge.className = 'badge status-error';
        queryStatusBadge.innerText = 'Error';
        queryResultMeta.innerText = 'Database exception thrown.';
        queryEmptyState.style.display = 'flex';
        queryEmptyState.innerHTML = `
            <div class="warning-alert">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <div>
                    <strong>SQL Error:</strong> ${errText}
                </div>
            </div>
        `;
        queryResultsTable.style.display = 'none';
    }

    // --- Render Query Result Table ---
    function renderQueryResultGrid(cols, rows) {
        queryResultsHeaders.innerHTML = '';
        queryResultsRows.innerHTML = '';
        
        // Render headers
        const trHead = document.createElement('tr');
        cols.forEach(col => {
            const th = document.createElement('th');
            th.innerText = col;
            trHead.appendChild(th);
        });
        queryResultsHeaders.appendChild(trHead);
        
        // Render data rows
        if (rows.length === 0) {
            queryResultsTable.style.display = 'none';
            queryEmptyState.style.display = 'flex';
            queryEmptyState.innerHTML = `
                <i class="fa-solid fa-inbox"></i>
                <p>Empty result set returned.</p>
            `;
            return;
        }
        
        rows.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(val => {
                const td = document.createElement('td');
                if (val === null) {
                    td.innerHTML = '<span style="color: #555; font-style: italic;">NULL</span>';
                } else {
                    td.innerText = val;
                }
                tr.appendChild(td);
            });
            queryResultsRows.appendChild(tr);
        });
        
        queryResultsTable.style.display = 'table';
    }

    // --- Clear Editor Button ---
    clearSqlBtn.addEventListener('click', () => {
        sqlEditor.value = '';
        sqlEditor.focus();
    });

    // --- Run Button Click Event ---
    runSqlBtn.addEventListener('click', runSqlQuery);

    // --- Ctrl+Enter Shortcut ---
    sqlEditor.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runSqlQuery();
        }
    });

    // --- Initialize Page Stats Load ---
    loadDashboardStats();
});
