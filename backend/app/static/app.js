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

    // Sample Dataset Generator (Retail & Sales)
    loadSampleBtn.addEventListener("click", () => {
        const rows = [
            "customer_id,customer_age,region,service_type,time_of_day,waiting_time,purchase_amount,spending_score,transaction_timestamp",
        ];

        const regions = ["East", "West", "North", "South"];
        const services = ["Standard", "Express", "VIP"];
        const times = ["Morning", "Afternoon", "Evening"];

        for (let i = 1; i <= 150; i++) {
            const age = 18 + Math.floor(Math.random() * 55);
            const region = regions[i % regions.length];
            const service = services[i % services.length];
            const time = times[i % times.length];
            
            // Interaction effect on wait time: Express in Evening takes longer
            let wait = 12 + Math.floor(Math.random() * 8);
            if (service === "Express" && time === "Evening") {
                wait += 42;
            } else if (service === "VIP") {
                wait = 4;
            }

            // Strong correlation: Age directly scales purchase amount
            const basePurchase = 20 + (age * 4.5) + (Math.random() * 15);
            // East group has much higher spending score (+50%)
            const spending = region === "East" ? 184.2 : 110.5;

            const hour = time === "Morning" ? "09" : (time === "Afternoon" ? "14" : "19");
            const timestamp = `2026-03-${String(10 + (i % 15)).padStart(2, '0')} ${hour}:15:00`;

            rows.push(`${i},${age},${region},${service},${time},${wait},${basePurchase.toFixed(2)},${spending},${timestamp}`);
        }

        const csvContent = rows.join("\n");
        const blob = new Blob([csvContent], { type: "text/csv" });
        const file = new File([blob], "retail_sales_demo.csv", { type: "text/csv" });
        handleFileUpload(file);
    });

    async function handleFileUpload(file) {
        if (!file.name.toLowerCase().endsWith(".csv")) {
            alert("Please upload a .csv file.");
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
            discovery_score: f.discovery_score
        }, null, 2);

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
});
