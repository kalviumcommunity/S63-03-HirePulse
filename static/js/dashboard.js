/**
 * HirePulse Dashboard Client Scripts
 * Handles live data fetching, interactive Chart.js visualizations, filtering, and modal popups.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Global chart instances
    let funnelChart = null;
    let timelineChart = null;
    let departmentChart = null;
    let salaryChart = null;

    let allCandidates = [];
    let allDepartments = [];

    // Initialize
    initTheme();
    setupNavigation();
    setupFilters();
    setupModal();
    loadDashboardData();

    // Refresh button
    document.getElementById("refreshBtn")?.addEventListener("click", () => {
        loadDashboardData();
    });

    // Theme toggle
    function initTheme() {
        const toggleBtn = document.getElementById("themeToggle");
        const savedTheme = localStorage.getItem("hirepulse_theme") || "dark";
        document.documentElement.setAttribute("data-theme", savedTheme);
        updateThemeIcon(savedTheme);

        toggleBtn?.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("hirepulse_theme", newTheme);
            updateThemeIcon(newTheme);
            updateChartsTheme();
        });
    }

    function updateThemeIcon(theme) {
        const icon = document.querySelector("#themeToggle i");
        if (icon) {
            icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
        }
    }

    function updateChartsTheme() {
        if (funnelChart) funnelChart.update();
        if (timelineChart) timelineChart.update();
        if (departmentChart) departmentChart.update();
        if (salaryChart) salaryChart.update();
    }

    // Tab Navigation
    function setupNavigation() {
        const navItems = document.querySelectorAll(".nav-item");
        const tabPanes = document.querySelectorAll(".tab-pane");

        navItems.forEach(item => {
            item.addEventListener("click", () => {
                const targetTab = item.getAttribute("data-tab");

                navItems.forEach(n => n.classList.remove("active"));
                tabPanes.forEach(p => p.classList.remove("active"));

                item.classList.add("active");
                document.getElementById(`tab-${targetTab}`)?.classList.add("active");
            });
        });
    }

    // Load all data
    async function loadDashboardData() {
        await Promise.all([
            fetchSummary(),
            fetchFunnel(),
            fetchTimeline(),
            fetchDepartments(),
            fetchCandidates(),
            fetchAnomalies()
        ]);
    }

    // 1. Executive Summary KPIs
    async function fetchSummary() {
        try {
            const res = await fetch("/api/summary");
            const json = await res.json();
            if (json.status === "success") {
                const d = json.data;
                document.getElementById("metricTotalCandidates").textContent = d.total_candidates.toLocaleString();
                document.getElementById("metricOffersSent").textContent = d.total_offers.toLocaleString();
                document.getElementById("metricOfferAcceptance").textContent = `${d.offer_acceptance_rate}% Acceptance`;
                document.getElementById("metricJoined").textContent = d.joined_count.toLocaleString();
                document.getElementById("metricConversionRate").textContent = `${d.overall_conversion_rate}% Conversion`;
                document.getElementById("metricTimeToHire").innerHTML = `${d.avg_time_to_hire_days} <small>days</small>`;
                document.getElementById("metricAvgSalary").textContent = d.avg_salary > 0 ? `$${d.avg_salary.toLocaleString()}` : "N/A";
                document.getElementById("metricTopDept").textContent = d.top_department;
            }
        } catch (err) {
            console.error("Error fetching summary:", err);
        }
    }

    // 2. Recruitment Funnel
    async function fetchFunnel() {
        try {
            const res = await fetch("/api/funnel");
            const json = await res.json();
            if (json.status === "success") {
                const data = json.data;
                renderFunnelChart(data);
                renderFunnelCards(data);
            }
        } catch (err) {
            console.error("Error fetching funnel:", err);
        }
    }

    function renderFunnelChart(data) {
        const ctx = document.getElementById("funnelChart")?.getContext("2d");
        if (!ctx) return;

        if (funnelChart) funnelChart.destroy();

        const labels = data.map(d => d.stage);
        const counts = data.map(d => d.count);

        funnelChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Candidates in Stage",
                    data: counts,
                    backgroundColor: [
                        "rgba(99, 102, 241, 0.85)",
                        "rgba(59, 130, 246, 0.85)",
                        "rgba(139, 92, 246, 0.85)",
                        "rgba(20, 184, 166, 0.85)",
                        "rgba(245, 158, 11, 0.85)",
                        "rgba(16, 185, 129, 0.85)"
                    ],
                    borderRadius: 8,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: (ctx) => {
                                const idx = ctx.dataIndex;
                                const item = data[idx];
                                return `Drop-off: ${item.drop_off} (${item.drop_off_pct}%)\nOverall Conversion: ${item.overall_conversion_pct}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#9ca3af" }
                    },
                    y: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#9ca3af" }
                    }
                }
            }
        });
    }

    function renderFunnelCards(data) {
        const container = document.getElementById("funnelSummaryList");
        if (!container) return;

        container.innerHTML = data.map(item => `
            <div class="funnel-step-item">
                <div class="step-name">${item.stage}</div>
                <div class="step-count">${item.count}</div>
                <div class="step-drop">${item.drop_off > 0 ? `-${item.drop_off} (${item.drop_off_pct}%)` : 'Top Stage'}</div>
            </div>
        `).join("");
    }

    // 3. Application Inflow Timeline
    async function fetchTimeline() {
        try {
            const res = await fetch("/api/timeline");
            const json = await res.json();
            if (json.status === "success" && json.data.labels) {
                renderTimelineChart(json.data);
            }
        } catch (err) {
            console.error("Error fetching timeline:", err);
        }
    }

    function renderTimelineChart(data) {
        const ctx = document.getElementById("timelineChart")?.getContext("2d");
        if (!ctx) return;

        if (timelineChart) timelineChart.destroy();

        timelineChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Applications Inflow",
                    data: data.values,
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99, 102, 241, 0.15)",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "#8b5cf6",
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#9ca3af" }
                    },
                    y: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { color: "#9ca3af", precision: 0 }
                    }
                }
            }
        });
    }

    // 4. Department Analytics
    async function fetchDepartments() {
        try {
            const res = await fetch("/api/departments");
            const json = await res.json();
            if (json.status === "success") {
                allDepartments = json.data;
                renderDepartmentCharts(allDepartments);
                renderDepartmentTable(allDepartments);
                populateDepartmentFilter(allDepartments);
            }
        } catch (err) {
            console.error("Error fetching departments:", err);
        }
    }

    function renderDepartmentCharts(data) {
        const ctxDept = document.getElementById("departmentChart")?.getContext("2d");
        const ctxSalary = document.getElementById("salaryChart")?.getContext("2d");

        if (ctxDept) {
            if (departmentChart) departmentChart.destroy();
            departmentChart = new Chart(ctxDept, {
                type: "bar",
                data: {
                    labels: data.map(d => d.department),
                    datasets: [
                        {
                            label: "Total Candidates",
                            data: data.map(d => d.total_candidates),
                            backgroundColor: "rgba(99, 102, 241, 0.8)",
                            borderRadius: 6
                        },
                        {
                            label: "Offers Sent",
                            data: data.map(d => d.offers_sent),
                            backgroundColor: "rgba(20, 184, 166, 0.8)",
                            borderRadius: 6
                        },
                        {
                            label: "Joined / Hired",
                            data: data.map(d => d.joined),
                            backgroundColor: "rgba(16, 185, 129, 0.8)",
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { ticks: { color: "#9ca3af" }, grid: { display: false } },
                        y: { ticks: { color: "#9ca3af" }, grid: { color: "rgba(255, 255, 255, 0.05)" } }
                    }
                }
            });
        }

        if (ctxSalary) {
            if (salaryChart) salaryChart.destroy();
            salaryChart = new Chart(ctxSalary, {
                type: "bar",
                data: {
                    labels: data.map(d => d.department),
                    datasets: [{
                        label: "Average Offer Salary ($)",
                        data: data.map(d => d.avg_salary),
                        backgroundColor: "rgba(245, 158, 11, 0.85)",
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { ticks: { color: "#9ca3af" }, grid: { display: false } },
                        y: { ticks: { color: "#9ca3af" }, grid: { color: "rgba(255, 255, 255, 0.05)" } }
                    }
                }
            });
        }
    }

    function renderDepartmentTable(data) {
        const tbody = document.getElementById("deptTableBody");
        if (!tbody) return;

        tbody.innerHTML = data.map(d => `
            <tr>
                <td><strong>${d.department}</strong></td>
                <td>${d.total_candidates}</td>
                <td>${d.offers_sent}</td>
                <td>${d.offers_accepted}</td>
                <td><span class="status-pill status-completed">${d.joined}</span></td>
                <td>${d.hire_rate}%</td>
                <td>${d.avg_salary > 0 ? `$${d.avg_salary.toLocaleString()}` : 'N/A'}</td>
            </tr>
        `).join("");
    }

    function populateDepartmentFilter(data) {
        const select = document.getElementById("departmentFilter");
        if (!select) return;
        select.innerHTML = '<option value="">All Departments</option>' +
            data.map(d => `<option value="${d.department}">${d.department}</option>`).join("");
    }

    // 5. Candidate Explorer
    async function fetchCandidates() {
        try {
            const res = await fetch("/api/candidates");
            const json = await res.json();
            if (json.status === "success") {
                allCandidates = json.data;
                applyCandidateFilters();
            }
        } catch (err) {
            console.error("Error fetching candidates:", err);
        }
    }

    function setupFilters() {
        const searchInput = document.getElementById("candidateSearchInput");
        const deptFilter = document.getElementById("departmentFilter");
        const stageFilter = document.getElementById("stageFilter");
        const statusFilter = document.getElementById("statusFilter");

        searchInput?.addEventListener("input", applyCandidateFilters);
        deptFilter?.addEventListener("change", applyCandidateFilters);
        stageFilter?.addEventListener("change", applyCandidateFilters);
        statusFilter?.addEventListener("change", applyCandidateFilters);
    }

    function applyCandidateFilters() {
        const search = document.getElementById("candidateSearchInput")?.value.toLowerCase().trim() || "";
        const dept = document.getElementById("departmentFilter")?.value || "";
        const stage = document.getElementById("stageFilter")?.value || "";
        const status = document.getElementById("statusFilter")?.value || "";

        const filtered = allCandidates.filter(c => {
            const matchesSearch = !search ||
                c.full_name.toLowerCase().includes(search) ||
                c.email.toLowerCase().includes(search) ||
                String(c.candidate_id).includes(search);

            const matchesDept = !dept || c.department === dept;
            const matchesStage = !stage || c.current_stage === stage;
            const matchesStatus = !status || c.stage_status === status;

            return matchesSearch && matchesDept && matchesStage && matchesStatus;
        });

        renderCandidatesTable(filtered);
    }

    function renderCandidatesTable(candidates) {
        const tbody = document.getElementById("candidatesTableBody");
        const countDisplay = document.getElementById("candidateCountDisplay");
        if (countDisplay) countDisplay.textContent = candidates.length;

        if (!tbody) return;

        if (candidates.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">No candidates matching the criteria.</td></tr>`;
            return;
        }

        tbody.innerHTML = candidates.slice(0, 50).map(c => {
            let statusClass = "status-pending";
            if (c.stage_status === "Completed") statusClass = "status-completed";
            else if (c.stage_status === "In Progress") statusClass = "status-inprogress";
            else if (c.stage_status === "Dropped") statusClass = "status-dropped";

            const offerStr = c.offer_salary ? `$${c.offer_salary.toLocaleString()} (${c.offer_accepted ? 'Accepted' : 'Pending'})` : 'No Offer';
            const safeName = (c.full_name || 'Candidate').replace(/'/g, "\\'").replace(/"/g, '&quot;');

            return `
                <tr>
                    <td>#${c.candidate_id}</td>
                    <td><strong>${c.full_name}</strong><br><small style="color:var(--text-muted)">${c.email}</small></td>
                    <td><span class="badge-dept">${c.department}</span></td>
                    <td>${c.applied_date || 'N/A'}</td>
                    <td>${c.current_stage}</td>
                    <td><span class="status-pill ${statusClass}">${c.stage_status}</span></td>
                    <td>${offerStr}</td>
                    <td>
                        <div class="action-btn-group">
                            <button class="btn-action view" onclick="viewCandidateDetails('${c.candidate_id}')" title="View Candidate Journey">
                                <i class="fa-solid fa-eye"></i>
                            </button>
                            <button class="btn-action edit" onclick="openEditCandidateModal('${c.candidate_id}')" title="Edit Candidate">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn-action delete" onclick="openDeleteCandidateModal('${c.candidate_id}', '${safeName}')" title="Delete Candidate">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    }

    // 6. Anomalies and Quality
    async function fetchAnomalies() {
        try {
            const res = await fetch("/api/anomalies");
            const json = await res.json();
            if (json.status === "success") {
                const list = json.data;
                const badge = document.getElementById("anomalyBadge");
                if (badge) badge.textContent = list.length;

                const container = document.getElementById("anomaliesList");
                if (container) {
                    container.innerHTML = list.map(a => `
                        <div class="anomaly-card glass-card ${a.severity.toLowerCase()}">
                            <div class="anomaly-icon">
                                <i class="fa-solid ${a.severity === 'Warning' ? 'fa-triangle-exclamation' : 'fa-circle-info'}"></i>
                            </div>
                            <div class="anomaly-body">
                                <h4>${a.title}</h4>
                                <p>${a.details}</p>
                            </div>
                        </div>
                    `).join("");
                }
            }
        } catch (err) {
            console.error("Error fetching anomalies:", err);
        }
    }

    // 7. Modals and Candidate Management (CRUD)
    let candidatePendingDeleteId = null;

    function setupModal() {
        // Detail modal close
        const detailModal = document.getElementById("candidateModal");
        const closeDetailBtn = document.getElementById("closeModalBtn");
        closeDetailBtn?.addEventListener("click", () => detailModal?.classList.remove("show"));
        detailModal?.addEventListener("click", (e) => {
            if (e.target === detailModal) detailModal.classList.remove("show");
        });

        // Form modal close
        const formModal = document.getElementById("candidateFormModal");
        const closeFormBtn = document.getElementById("closeCandidateFormModalBtn");
        const cancelFormBtn = document.getElementById("cancelCandidateFormBtn");
        closeFormBtn?.addEventListener("click", () => formModal?.classList.remove("show"));
        cancelFormBtn?.addEventListener("click", () => formModal?.classList.remove("show"));
        formModal?.addEventListener("click", (e) => {
            if (e.target === formModal) formModal.classList.remove("show");
        });

        // Delete modal close
        const deleteModal = document.getElementById("deleteConfirmModal");
        const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");
        cancelDeleteBtn?.addEventListener("click", () => deleteModal?.classList.remove("show"));
        deleteModal?.addEventListener("click", (e) => {
            if (e.target === deleteModal) deleteModal.classList.remove("show");
        });

        // Add candidate trigger button
        const addBtn = document.getElementById("addCandidateBtn");
        addBtn?.addEventListener("click", openAddCandidateModal);

        // Candidate form submit
        const form = document.getElementById("candidateForm");
        form?.addEventListener("submit", handleCandidateFormSubmit);

        // Delete confirm button
        const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
        confirmDeleteBtn?.addEventListener("click", handleCandidateDelete);
    }

    // Open Add Candidate Modal
    function openAddCandidateModal() {
        const modal = document.getElementById("candidateFormModal");
        const title = document.getElementById("candidateFormModalTitle");
        const subtitle = document.getElementById("candidateFormModalSubtitle");
        const form = document.getElementById("candidateForm");
        
        if (title) title.innerHTML = '<i class="fa-solid fa-user-plus"></i> Add New Candidate';
        if (subtitle) subtitle.textContent = 'Enter candidate details to add them to the active recruitment pipeline.';
        if (form) form.reset();

        document.getElementById("formCandidateId").value = "";
        
        // Default today's date
        const todayStr = new Date().toISOString().split("T")[0];
        document.getElementById("formAppliedDate").value = todayStr;
        document.getElementById("formStageName").value = "Applied";
        document.getElementById("formStageStatus").value = "In Progress";
        document.getElementById("formOfferAccepted").value = "false";

        modal?.classList.add("show");
    }

    // Open Edit Candidate Modal
    window.openEditCandidateModal = async function(cid) {
        try {
            const res = await fetch(`/api/candidate/${cid}`);
            const json = await res.json();
            if (json.status !== "success") {
                showToast(json.message || "Failed to load candidate details", "error");
                return;
            }

            const c = json.candidate;
            const stages = json.stages || [];
            const offers = json.offers || [];

            const modal = document.getElementById("candidateFormModal");
            const title = document.getElementById("candidateFormModalTitle");
            const subtitle = document.getElementById("candidateFormModalSubtitle");

            if (title) title.innerHTML = `<i class="fa-solid fa-user-pen"></i> Edit Candidate #${cid}`;
            if (subtitle) subtitle.textContent = `Update recruitment records and profile for ${c.full_name}.`;

            document.getElementById("formCandidateId").value = cid;
            document.getElementById("formFullName").value = c.full_name || "";
            document.getElementById("formEmail").value = c.email || "";
            document.getElementById("formPhone").value = c.phone || "";
            document.getElementById("formDepartment").value = c.department || "Engineering";
            document.getElementById("formAppliedDate").value = c.applied_date || "";

            const lastStage = stages.length > 0 ? stages[stages.length - 1] : null;
            document.getElementById("formStageName").value = lastStage ? lastStage.stage_name : "Applied";
            document.getElementById("formStageStatus").value = lastStage ? lastStage.status : "In Progress";

            const offer = offers.length > 0 ? offers[0] : null;
            document.getElementById("formOfferSalary").value = offer ? (offer.salary || "") : "";
            document.getElementById("formOfferAccepted").value = offer && offer.accepted ? "true" : "false";

            modal?.classList.add("show");
        } catch (err) {
            console.error("Error opening edit modal:", err);
            showToast("Failed to fetch candidate for editing.", "error");
        }
    };

    // Open Delete Candidate Modal
    window.openDeleteCandidateModal = function(cid, name) {
        candidatePendingDeleteId = cid;
        document.getElementById("deleteCandidateName").textContent = name || "Candidate";
        document.getElementById("deleteCandidateId").textContent = `#${cid}`;
        document.getElementById("deleteConfirmModal")?.classList.add("show");
    };

    // Handle Form Submit (Add / Edit)
    async function handleCandidateFormSubmit(e) {
        e.preventDefault();
        const cid = document.getElementById("formCandidateId").value;
        const fullName = document.getElementById("formFullName").value.trim();
        const email = document.getElementById("formEmail").value.trim();
        const phone = document.getElementById("formPhone").value.trim();
        const department = document.getElementById("formDepartment").value;
        const appliedDate = document.getElementById("formAppliedDate").value;
        const stageName = document.getElementById("formStageName").value;
        const stageStatus = document.getElementById("formStageStatus").value;
        const offerSalary = document.getElementById("formOfferSalary").value;
        const offerAccepted = document.getElementById("formOfferAccepted").value === "true";

        if (!fullName || !email) {
            showToast("Full name and email are required.", "error");
            return;
        }

        const payload = {
            full_name: fullName,
            email: email,
            phone: phone,
            department: department,
            applied_date: appliedDate,
            stage_name: stageName,
            stage_status: stageStatus,
            offer_salary: offerSalary ? parseFloat(offerSalary) : null,
            offer_accepted: offerAccepted
        };

        const saveBtn = document.getElementById("saveCandidateBtn");
        const originalBtnHtml = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        try {
            const url = cid ? `/api/candidate/${cid}` : "/api/candidate";
            const method = cid ? "PUT" : "POST";

            const res = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const json = await res.json();
            if (json.status === "success") {
                document.getElementById("candidateFormModal")?.classList.remove("show");
                showToast(json.message || (cid ? "Candidate updated!" : "Candidate added!"), "success");
                await loadDashboardData();
            } else {
                showToast(json.message || "An error occurred.", "error");
            }
        } catch (err) {
            console.error("Error saving candidate:", err);
            showToast("Failed to save candidate. Please try again.", "error");
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalBtnHtml;
        }
    }

    // Handle Delete Execution
    async function handleCandidateDelete() {
        if (!candidatePendingDeleteId) return;

        const deleteBtn = document.getElementById("confirmDeleteBtn");
        const originalBtnHtml = deleteBtn.innerHTML;
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';

        try {
            const res = await fetch(`/api/candidate/${candidatePendingDeleteId}`, {
                method: "DELETE"
            });
            const json = await res.json();

            if (json.status === "success") {
                document.getElementById("deleteConfirmModal")?.classList.remove("show");
                showToast(json.message || "Candidate deleted successfully.", "success");
                candidatePendingDeleteId = null;
                await loadDashboardData();
            } else {
                showToast(json.message || "Failed to delete candidate.", "error");
            }
        } catch (err) {
            console.error("Error deleting candidate:", err);
            showToast("Network error while deleting candidate.", "error");
        } finally {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = originalBtnHtml;
        }
    }

    // Toast Notification helper
    function showToast(message, type = "success") {
        const container = document.getElementById("toastContainer");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        const iconClass = type === "success" ? "fa-circle-check" : "fa-triangle-exclamation";
        toast.innerHTML = `<i class="fa-solid ${iconClass}"></i> <span>${message}</span>`;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(20px)";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    window.viewCandidateDetails = async function(cid) {
        try {
            const res = await fetch(`/api/candidate/${cid}`);
            const json = await res.json();
            if (json.status === "success") {
                const c = json.candidate;
                const stages = json.stages;
                const interviews = json.interviews;
                const offers = json.offers;
                const onboarding = json.onboarding;

                document.getElementById("modalCandidateName").textContent = c.full_name;
                document.getElementById("modalCandidateDept").textContent = c.department;

                const body = document.getElementById("modalCandidateContent");
                body.innerHTML = `
                    <div style="margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <p style="margin-bottom: 4px;"><strong>Email:</strong> ${c.email} &nbsp;|&nbsp; <strong>Phone:</strong> ${c.phone || 'N/A'}</p>
                            <p><strong>Application Date:</strong> ${c.applied_date || 'N/A'}</p>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-detail" onclick="document.getElementById('candidateModal').classList.remove('show'); openEditCandidateModal('${c.candidate_id}')">
                                <i class="fa-solid fa-pen-to-square"></i> Edit Profile
                            </button>
                        </div>
                    </div>

                    <h4 style="margin-bottom: 0.75rem;">Recruitment Stages</h4>
                    <div style="margin-bottom: 1.5rem;">
                        ${stages.length > 0 ? stages.map(s => `
                            <div class="modal-timeline-item">
                                <strong>${s.stage_name}</strong> - <span class="status-pill status-${s.status.toLowerCase().replace(' ', '')}">${s.status}</span>
                                <div style="font-size: 0.8rem; color: var(--text-muted);">${s.stage_date}</div>
                            </div>
                        `).join("") : '<p style="color:var(--text-muted)">No stage records recorded.</p>'}
                    </div>

                    <h4 style="margin-bottom: 0.75rem;">Interview Rounds</h4>
                    <div style="margin-bottom: 1.5rem;">
                        ${interviews.length > 0 ? interviews.map(i => `
                            <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                                <strong>${i.round_name}</strong> (Score: ${i.score}/10) - <em>${i.result}</em>
                                <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">"${i.feedback}"</p>
                                <small style="color:var(--text-muted)">Interviewer: ${i.interviewer_name} on ${i.interview_date}</small>
                            </div>
                        `).join("") : '<p style="color:var(--text-muted)">No interview rounds logged.</p>'}
                    </div>

                    <h4 style="margin-bottom: 0.75rem;">Offer & Onboarding</h4>
                    <div>
                        ${offers.length > 0 ? `
                            <p><strong>Offer Sent:</strong> $${offers[0].salary?.toLocaleString()} on ${offers[0].offer_date} (${offers[0].accepted ? 'Accepted' : 'Pending/Declined'})</p>
                        ` : '<p style="color:var(--text-muted)">No offer record.</p>'}
                        ${onboarding.length > 0 ? `
                            <p><strong>Onboarding Status:</strong> ${onboarding[0].onboarding_status} (Joined: ${onboarding[0].joining_date})</p>
                        ` : ''}
                    </div>
                `;

                document.getElementById("candidateModal")?.classList.add("show");
            }
        } catch (err) {
            console.error("Error viewing candidate:", err);
            showToast("Failed to fetch candidate details.", "error");
        }
    };
});
