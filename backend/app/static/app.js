document.addEventListener("DOMContentLoaded", () => {
    let currentDatasetId = null;
    let currentFilename = "dataset.csv";

    // DOM Elements
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const loadSampleBtn = document.getElementById("loadSampleBtn");
    const datasetMetaPanel = document.getElementById("datasetMetaPanel");
    const metaFilename = document.getElementById("metaFilename");
    const metaRowCount = document.getElementById("metaRowCount");
    const metaColCount = document.getElementById("metaColCount");
    const metaMemory = document.getElementById("metaMemory");
    const metaColumnsList = document.getElementById("metaColumnsList");
    const discoverBtn = document.getElementById("discoverBtn");

    const loadingSection = document.getElementById("loadingSection");
    const loadingStatusText = document.getElementById("loadingStatusText");
    const progressFill = document.getElementById("progressFill");

    const reportSection = document.getElementById("reportSection");
    const reportDatasetTitle = document.getElementById("reportDatasetTitle");
    const statExamined = document.getElementById("statExamined");
    const statReturned = document.getElementById("statReturned");
    const statTime = document.getElementById("statTime");
    const discoveryCardsList = document.getElementById("discoveryCardsList");
    const providerBadge = document.getElementById("providerBadge");

    // Fetch initial health/provider
    fetch("/health")
        .then(res => res.json())
        .then(data => {
            if (data.gemini_model) {
                providerBadge.textContent = `${data.gemini_model} Ready`;
            }
        })
        .catch(() => {});

    // Drag and Drop
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Sample Dataset Loader (3,500 rows)
    loadSampleBtn.addEventListener("click", async () => {
        try {
            loadSampleBtn.textContent = "Loading 3,500 rows...";
            const res = await fetch("/static/samples/retail_sales_3500_records.csv");
            if (!res.ok) throw new Error("Could not fetch sample dataset");
            const blob = await res.blob();
            const file = new File([blob], "retail_sales_3500_records.csv", { type: "text/csv" });
            await handleFileUpload(file);
        } catch (err) {
            alert(`Error loading sample: ${err.message}`);
        } finally {
            loadSampleBtn.textContent = "⚡ Quick Load 3,500 Rows";
        }
    });

    async function handleFileUpload(file) {
        const lower = file.name.toLowerCase();
        if (!lower.endsWith(".csv") && !lower.endsWith(".xlsx") && !lower.endsWith(".xls")) {
            alert("Please upload a .csv or .xlsx file.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/v1/datasets/upload", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                alert(`Upload failed: ${err.detail || "Server error"}`);
                return;
            }

            const data = await res.json();
            currentDatasetId = data.dataset_id;
            currentFilename = data.filename;

            // Render metadata
            metaFilename.textContent = data.filename;
            metaRowCount.textContent = Number(data.row_count).toLocaleString();
            metaColCount.textContent = data.column_count;
            metaMemory.textContent = data.memory_mb;

            metaColumnsList.innerHTML = "";
            data.columns.forEach(col => {
                const badge = document.createElement("span");
                badge.className = "column-badge";
                badge.textContent = col;
                metaColumnsList.appendChild(badge);
            });

            datasetMetaPanel.style.display = "block";
            reportSection.style.display = "none";
        } catch (err) {
            alert(`Error uploading file: ${err.message}`);
        }
    }

    // Discover Action
    discoverBtn.addEventListener("click", async () => {
        if (!currentDatasetId) return;

        // UI Transition to Loading State
        datasetMetaPanel.style.opacity = "0.6";
        discoverBtn.disabled = true;
        loadingSection.style.display = "block";
        reportSection.style.display = "none";

        // Animated progress steps
        const steps = [
            { text: "Profiling dataset dimensions...", progress: "15%" },
            { text: "Testing numerical correlations...", progress: "35%" },
            { text: "Comparing categorical subgroups...", progress: "55%" },
            { text: "Scanning for non-additive interactions...", progress: "70%" },
            { text: "Auditing data quality & anomalies...", progress: "85%" },
            { text: "Generating reasoning explanations with AI...", progress: "95%" },
        ];

        let stepIdx = 0;
        const interval = setInterval(() => {
            if (stepIdx < steps.length) {
                loadingStatusText.textContent = steps[stepIdx].text;
                progressFill.style.width = steps[stepIdx].progress;
                stepIdx++;
            }
        }, 350);

        try {
            const response = await fetch("/api/v1/discovery", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    max_findings: 5,
                }),
            });

            clearInterval(interval);
            progressFill.style.width = "100%";

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Discovery engine encountered an error.");
            }

            const discoveryData = await response.json();
            renderDiscoveryReport(discoveryData);
        } catch (err) {
            clearInterval(interval);
            alert(`Discovery error: ${err.message}`);
        } finally {
            loadingSection.style.display = "none";
            datasetMetaPanel.style.opacity = "1";
            discoverBtn.disabled = false;
        }
    });

    function renderDiscoveryReport(report) {
        reportDatasetTitle.textContent = report.filename || currentFilename;
        statExamined.textContent = report.summary.candidates_examined;
        statReturned.textContent = report.summary.findings_returned;
        statTime.textContent = `${report.summary.execution_time_ms}ms`;

        discoveryCardsList.innerHTML = "";

        if (!report.findings || report.findings.length === 0) {
            discoveryCardsList.innerHTML = `
                <div class="card" style="padding: 2rem; text-align: center; color: var(--text-muted);">
                    No significant statistical anomalies or relationships were identified in this sample.
                </div>
            `;
            reportSection.style.display = "block";
            return;
        }

        report.findings.forEach((finding, index) => {
            const card = createDiscoveryCard(finding, index + 1);
            discoveryCardsList.appendChild(card);
        });

        reportSection.style.display = "block";
        reportSection.scrollIntoView({ behavior: "smooth" });
    }

    function createDiscoveryCard(f, orderNum) {
        const card = document.createElement("div");
        card.className = "discovery-card";

        // Category Type Formatting
        const typeLabels = {
            correlation: "Strong Relationship",
            group_difference: "Unexpected Group Difference",
            interaction: "Possible Interaction",
            time_pattern: "Temporal Pattern",
            data_quality: "Possible Data Quality Issue",
            category_numeric: "Subgroup Divergence",
        };
        const typeLabel = typeLabels[f.type] || f.type.replace("_", " ").toUpperCase();

        // Key Metric Callout formatting
        let metricHtml = "";
        if (f.type === "correlation") {
            metricHtml = `
                <div class="metric-item">
                    <span class="lbl">Correlation (r)</span>
                    <span class="val highlight-cyan">${f.metric.correlation || "N/A"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Direction</span>
                    <span class="val">${f.metric.direction || "Positive"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Strength</span>
                    <span class="val">${f.metric.strength || "Strong"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Sample Size</span>
                    <span class="val">${Number(f.metric.sample_size || 0).toLocaleString()}</span>
                </div>
            `;
        } else if (f.type === "group_difference") {
            const pct = f.metric.percentage_difference || 0;
            const sign = pct > 0 ? "+" : "";
            metricHtml = `
                <div class="metric-item">
                    <span class="lbl">Subgroup</span>
                    <span class="val">${f.metric.group || "N/A"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Group Average</span>
                    <span class="val">${f.metric.group_mean ?? "N/A"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Overall Average</span>
                    <span class="val">${f.metric.overall_mean ?? "N/A"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Difference</span>
                    <span class="val highlight-green">${sign}${pct}%</span>
                </div>
            `;
        } else if (f.type === "interaction") {
            metricHtml = `
                <div class="metric-item">
                    <span class="lbl">Factors</span>
                    <span class="val">${(f.columns || []).slice(0, 2).join(" + ")}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Effect Ratio</span>
                    <span class="val highlight-cyan">${f.metric.interaction_effect_ratio || "N/A"}</span>
                </div>
            `;
        } else if (f.type === "time_pattern") {
            metricHtml = `
                <div class="metric-item">
                    <span class="lbl">Temporal Unit</span>
                    <span class="val">${f.metric.temporal_unit || "Hour"}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Peak Segment</span>
                    <span class="val highlight-green">${f.metric.peak_segment} (${f.metric.peak_mean})</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Trough Segment</span>
                    <span class="val">${f.metric.trough_segment} (${f.metric.trough_mean})</span>
                </div>
            `;
        } else if (f.type === "data_quality") {
            metricHtml = `
                <div class="metric-item">
                    <span class="lbl">Target Column</span>
                    <span class="val">${(f.columns || []).join(", ")}</span>
                </div>
                <div class="metric-item">
                    <span class="lbl">Audit Detail</span>
                    <span class="val highlight-cyan">${f.metric.missing_percentage ? f.metric.missing_percentage + '% null' : (f.metric.is_exact_duplicate ? '100% Duplicate' : 'Constant Feature')}</span>
                </div>
            `;
        } else {
            metricHtml = `
                <div class="metric-item">
                    <span class="lbl">Columns</span>
                    <span class="val">${(f.columns || []).join(" ↔ ")}</span>
                </div>
            `;
        }

        // Python Evidence formatting text
        let pythonEvidenceText = f.evidence?.description || "";
        if (!pythonEvidenceText) {
            if (f.type === "correlation") {
                pythonEvidenceText = `Pearson correlation computed across ${f.metric?.sample_size || "all"} valid pairs (r = ${f.metric?.correlation}, p-value = ${f.metric?.p_value ?? 0.0}).`;
            } else if (f.type === "group_difference") {
                pythonEvidenceText = `Subgroup '${f.metric?.group}' (n = ${f.metric?.group_size}) shows a mean of ${f.metric?.group_mean} versus population mean ${f.metric?.overall_mean} (delta = ${f.metric?.percentage_difference}%).`;
            } else if (f.type === "data_quality") {
                pythonEvidenceText = `Integrity scan identified data quality anomaly across feature '${(f.columns || []).join(", ")}'.`;
            } else {
                pythonEvidenceText = `Deterministic statistical evaluation calculated across ${f.columns.join(", ")}.`;
            }
        }

        // Caution Box
        const cautionHtml = f.caution ? `
            <div class="info-box caution-box">
                <div class="box-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    Analytical Caution
                </div>
                <div class="box-content">${escapeHtml(f.caution)}</div>
            </div>
        ` : "";

        // Raw technical evidence JSON
        const rawJsonString = JSON.stringify({
            finding_id: f.id,
            category: f.type,
            metric_data: f.metric,
            statistical_evidence: f.evidence,
            visualization: f.visualization,
            discovery_score: f.discovery_score
        }, null, 2);

        const chartHtml = renderDiscoveryChartSvg(f.visualization);

        card.innerHTML = `
            <div class="card-top">
                <span class="type-badge ${f.type}">
                    ${orderNum}. ${typeLabel}
                </span>
                <span class="column-badge">${(f.columns || []).join(" ↔ ")}</span>
            </div>

            <h3 class="card-title">${escapeHtml(f.title)}</h3>

            <div class="metric-callout">
                ${metricHtml}
            </div>

            ${chartHtml}

            <div class="evidence-section">
                <!-- AI Explanation Box -->
                <div class="info-box ai-box">
                    <div class="box-header">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48 2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48 2.83-2.83"></path>
                        </svg>
                        Explanation Generated by AI
                    </div>
                    <div class="box-content">${escapeHtml(f.explanation)}</div>
                </div>

                <!-- Python Evidence Box -->
                <div class="info-box python-box">
                    <div class="box-header">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        Evidence Calculated by DataPilot
                    </div>
                    <div class="box-content">${escapeHtml(pythonEvidenceText)}</div>
                </div>

                ${cautionHtml}
            </div>

            <!-- Technical Evidence Accordion -->
            <div class="tech-details">
                <button type="button" class="tech-toggle" onclick="toggleTechnicalEvidence(this)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    Show Technical Evidence
                </button>
                <pre class="tech-content">${escapeHtml(rawJsonString)}</pre>
            </div>
        `;

        return card;
    }

    window.toggleTechnicalEvidence = function(btn) {
        const content = btn.nextElementSibling;
        if (content.classList.contains("open")) {
            content.classList.remove("open");
            btn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                Show Technical Evidence
            `;
        } else {
            content.classList.add("open");
            btn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                Hide Technical Evidence
            `;
        }
    };

    function escapeHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function renderDiscoveryChartSvg(viz) {
        if (!viz || !viz.data || !Array.isArray(viz.data) || viz.data.length === 0) {
            return "";
        }

        const { chart_type, title, x_label, y_label, x_key, y_key, data } = viz;
        const width = 560;
        const height = 230;
        const padLeft = 60;
        const padRight = 30;
        const padTop = 28;
        const padBottom = 48;
        const plotWidth = width - padLeft - padRight;
        const plotHeight = height - padTop - padBottom;

        let chartBody = "";

        if (chart_type === "scatter") {
            const validPoints = data
                .map(d => ({ x: Number(d[x_key]), y: Number(d[y_key]) }))
                .filter(d => !isNaN(d.x) && !isNaN(d.y));

            if (validPoints.length === 0) return "";

            let minX = Math.min(...validPoints.map(d => d.x));
            let maxX = Math.max(...validPoints.map(d => d.x));
            let minY = Math.min(...validPoints.map(d => d.y));
            let maxY = Math.max(...validPoints.map(d => d.y));

            if (minX === maxX) { minX -= 1; maxX += 1; }
            if (minY === maxY) { minY -= 1; maxY += 1; }

            const padX = (maxX - minX) * 0.06;
            const padY = (maxY - minY) * 0.06;
            minX -= padX; maxX += padX;
            minY -= padY; maxY += padY;

            let gridLines = "";
            for (let i = 0; i <= 3; i++) {
                const frac = i / 3;
                const gy = padTop + plotHeight - (frac * plotHeight);
                const valY = minY + frac * (maxY - minY);
                gridLines += `<line x1="${padLeft}" y1="${gy}" x2="${padLeft + plotWidth}" y2="${gy}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3,3" />`;
                gridLines += `<text x="${padLeft - 8}" y="${gy + 4}" text-anchor="end" font-size="10" fill="#64748b" font-family="monospace">${valY >= 100 ? Math.round(valY) : valY.toFixed(1)}</text>`;

                const gx = padLeft + (frac * plotWidth);
                const valX = minX + frac * (maxX - minX);
                gridLines += `<line x1="${gx}" y1="${padTop}" x2="${gx}" y2="${padTop + plotHeight}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3,3" />`;
                gridLines += `<text x="${gx}" y="${padTop + plotHeight + 16}" text-anchor="middle" font-size="10" fill="#64748b" font-family="monospace">${valX >= 100 ? Math.round(valX) : valX.toFixed(1)}</text>`;
            }

            let circles = "";
            validPoints.forEach(p => {
                const cx = padLeft + ((p.x - minX) / (maxX - minX)) * plotWidth;
                const cy = padTop + plotHeight - ((p.y - minY) / (maxY - minY)) * plotHeight;
                circles += `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="3.2" fill="#38bdf8" opacity="0.8">
                    <title>${escapeHtml(x_label)}: ${p.x}, ${escapeHtml(y_label)}: ${p.y}</title>
                </circle>`;
            });

            chartBody = gridLines + circles;

        } else if (chart_type === "bar") {
            const items = data.map(d => ({
                cat: String(d[x_key] ?? ""),
                val: Number(d[y_key] ?? 0),
            })).filter(d => !isNaN(d.val));

            if (items.length === 0) return "";

            let minY = Math.min(0, Math.min(...items.map(d => d.val)));
            let maxY = Math.max(0, Math.max(...items.map(d => d.val)));
            if (minY === maxY) { maxY += 1; }
            maxY = maxY * 1.18; // Room for value labels

            let gridLines = "";
            for (let i = 0; i <= 3; i++) {
                const frac = i / 3;
                const gy = padTop + plotHeight - (frac * plotHeight);
                const valY = minY + frac * (maxY - minY);
                gridLines += `<line x1="${padLeft}" y1="${gy}" x2="${padLeft + plotWidth}" y2="${gy}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3,3" />`;
                gridLines += `<text x="${padLeft - 8}" y="${gy + 4}" text-anchor="end" font-size="10" fill="#64748b" font-family="monospace">${valY >= 100 ? Math.round(valY) : valY.toFixed(1)}</text>`;
            }

            const baseY = padTop + plotHeight - ((0 - minY) / (maxY - minY)) * plotHeight;
            gridLines += `<line x1="${padLeft}" y1="${baseY}" x2="${padLeft + plotWidth}" y2="${baseY}" stroke="rgba(255,255,255,0.25)" stroke-width="1.2" />`;

            const n = items.length;
            const slotWidth = plotWidth / n;
            const barWidth = Math.min(46, Math.max(14, slotWidth * 0.65));

            let bars = "";
            items.forEach((item, i) => {
                const barX = padLeft + (i * slotWidth) + ((slotWidth - barWidth) / 2);
                const valY = padTop + plotHeight - ((item.val - minY) / (maxY - minY)) * plotHeight;
                const barY = Math.min(baseY, valY);
                const barH = Math.max(2, Math.abs(baseY - valY));

                bars += `<rect x="${barX.toFixed(1)}" y="${barY.toFixed(1)}" width="${barWidth.toFixed(1)}" height="${barH.toFixed(1)}" rx="3" fill="url(#barGradient)" opacity="0.9">
                    <title>${escapeHtml(item.cat)}: ${item.val}</title>
                </rect>`;

                const labelY = item.val >= 0 ? barY - 5 : barY + barH + 12;
                bars += `<text x="${(barX + barWidth / 2).toFixed(1)}" y="${labelY.toFixed(1)}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#cbd5e1" font-family="monospace">${item.val}</text>`;

                const catLabel = item.cat.length > 9 ? item.cat.slice(0, 8) + "…" : item.cat;
                bars += `<text x="${(barX + barWidth / 2).toFixed(1)}" y="${(padTop + plotHeight + 17).toFixed(1)}" text-anchor="middle" font-size="10" fill="#94a3b8">${escapeHtml(catLabel)}</text>`;
            });

            chartBody = gridLines + bars;

        } else if (chart_type === "line") {
            const items = data.map(d => ({
                label: String(d[x_key] ?? ""),
                val: Number(d[y_key] ?? 0),
            })).filter(d => !isNaN(d.val));

            if (items.length === 0) return "";

            let minY = Math.min(...items.map(d => d.val));
            let maxY = Math.max(...items.map(d => d.val));
            if (minY === maxY) { minY -= 1; maxY += 1; }
            const padY = (maxY - minY) * 0.12;
            minY -= padY; maxY += padY;

            let gridLines = "";
            for (let i = 0; i <= 3; i++) {
                const frac = i / 3;
                const gy = padTop + plotHeight - (frac * plotHeight);
                const valY = minY + frac * (maxY - minY);
                gridLines += `<line x1="${padLeft}" y1="${gy}" x2="${padLeft + plotWidth}" y2="${gy}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3,3" />`;
                gridLines += `<text x="${padLeft - 8}" y="${gy + 4}" text-anchor="end" font-size="10" fill="#64748b" font-family="monospace">${valY >= 100 ? Math.round(valY) : valY.toFixed(1)}</text>`;
            }

            const n = items.length;
            const coords = items.map((item, i) => {
                const cx = padLeft + (n === 1 ? plotWidth / 2 : (i / (n - 1)) * plotWidth);
                const cy = padTop + plotHeight - ((item.val - minY) / (maxY - minY)) * plotHeight;
                return { x: cx, y: cy, label: item.label, val: item.val };
            });

            const first = coords[0];
            const last = coords[coords.length - 1];
            const bottomY = padTop + plotHeight;
            let areaD = `M ${first.x.toFixed(1)} ${bottomY} L ${first.x.toFixed(1)} ${first.y.toFixed(1)}`;
            for (let i = 1; i < coords.length; i++) {
                areaD += ` L ${coords[i].x.toFixed(1)} ${coords[i].y.toFixed(1)}`;
            }
            areaD += ` L ${last.x.toFixed(1)} ${bottomY} Z`;

            let lineD = `M ${first.x.toFixed(1)} ${first.y.toFixed(1)}`;
            for (let i = 1; i < coords.length; i++) {
                lineD += ` L ${coords[i].x.toFixed(1)} ${coords[i].y.toFixed(1)}`;
            }

            let lineElements = `
                <path d="${areaD}" fill="url(#lineAreaGrad)" opacity="0.3" />
                <path d="${lineD}" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
            `;

            coords.forEach(pt => {
                lineElements += `<circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="3.8" fill="#6366f1" stroke="#ffffff" stroke-width="1.8">
                    <title>${escapeHtml(pt.label)}: ${pt.val}</title>
                </circle>`;

                if (coords.length <= 12) {
                    lineElements += `<text x="${pt.x.toFixed(1)}" y="${(pt.y - 7).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="600" fill="#cbd5e1" font-family="monospace">${pt.val}</text>`;
                    const segLabel = pt.label.length > 7 ? pt.label.slice(0, 6) + "…" : pt.label;
                    lineElements += `<text x="${pt.x.toFixed(1)}" y="${(padTop + plotHeight + 17).toFixed(1)}" text-anchor="middle" font-size="10" fill="#94a3b8">${escapeHtml(segLabel)}</text>`;
                }
            });

            chartBody = gridLines + lineElements;
        }

        return `
            <div class="discovery-chart-box">
                <div class="chart-header">
                    <div class="chart-header-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                            <line x1="18" y1="20" x2="18" y2="10"></line>
                            <line x1="12" y1="20" x2="12" y2="4"></line>
                            <line x1="6" y1="20" x2="6" y2="14"></line>
                        </svg>
                        <span>${escapeHtml(title)}</span>
                    </div>
                    <span class="chart-badge">${chart_type.toUpperCase()}</span>
                </div>
                <div class="chart-svg-container">
                    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
                        <defs>
                            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stop-color="#38bdf8" />
                                <stop offset="100%" stop-color="#4f46e5" />
                            </linearGradient>
                            <linearGradient id="lineAreaGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stop-color="#818cf8" stop-opacity="0.5" />
                                <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0" />
                            </linearGradient>
                        </defs>
                        ${chartBody}
                        <!-- Axis Labels -->
                        <text x="${(padLeft + plotWidth / 2).toFixed(1)}" y="${height - 8}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#64748b">${escapeHtml(x_label)}</text>
                        <text x="14" y="${(padTop + plotHeight / 2).toFixed(1)}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#64748b" transform="rotate(-90 14 ${(padTop + plotHeight / 2).toFixed(1)})">${escapeHtml(y_label)}</text>
                    </svg>
                </div>
            </div>
        `;
    }
});
