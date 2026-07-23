/* =====================================================================
   Sundae Social — admin.js
   ---------------------------------------------------------------------
   Admin dashboard logic:
     - Fetch aggregate stats (total, averages, recommend %)
     - Fetch paginated / filtered / sorted feedback list
     - Render table rows, empty state, and pagination
     - View feedback detail in a modal
     - Delete feedback with confirmation modal
   Relies on API_CONFIG defined in script.js (loaded before this file).
   ===================================================================== */

(function initAdminDashboard() {
  const tableBody = document.getElementById("feedbackTableBody");
  if (!tableBody) return; // Not on the admin page — skip entirely.

  // ---- Element references ----
  const statTotal = document.getElementById("statTotal");
  const statAvgRating = document.getElementById("statAvgRating");
  const statRecommend = document.getElementById("statRecommend");
  const statVisitAgain = document.getElementById("statVisitAgain");

  const searchInput = document.getElementById("searchInput");
  const minRatingFilter = document.getElementById("minRatingFilter");
  const maxRatingFilter = document.getElementById("maxRatingFilter");
  const startDateFilter = document.getElementById("startDateFilter");
  const endDateFilter = document.getElementById("endDateFilter");
  const applyFiltersBtn = document.getElementById("applyFiltersBtn");
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");
  const sortBySelect = document.getElementById("sortBySelect");
  const sortOrderSelect = document.getElementById("sortOrderSelect");

  const resultsSummary = document.getElementById("resultsSummary");
  const emptyState = document.getElementById("emptyState");
  const paginationControls = document.getElementById("paginationControls");
  const adminErrorBanner = document.getElementById("adminErrorBanner");

  const detailModalBody = document.getElementById("detailModalBody");
  const detailModalEl = document.getElementById("detailModal");
  const deleteModalEl = document.getElementById("deleteModal");
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");

  const detailModal = new bootstrap.Modal(detailModalEl);
  const deleteModal = new bootstrap.Modal(deleteModalEl);

  // ---- State ----
  let currentPage = 1;
  const pageSize = 10;
  let pendingDeleteId = null;

  // -----------------------------------------------------------------
  // Utility helpers
  // -----------------------------------------------------------------
  function showAdminError(message) {
    adminErrorBanner.textContent = message;
    adminErrorBanner.classList.remove("d-none");
  }

  function clearAdminError() {
    adminErrorBanner.classList.add("d-none");
    adminErrorBanner.textContent = "";
  }

  function formatDate(dateStr) {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }

  function formatDateTime(dateStr) {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return dateStr;
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function starString(rating) {
    const filled = "★".repeat(rating);
    const empty = "☆".repeat(5 - rating);
    return filled + empty;
  }

  function badgeFor(value) {
    return value === "Yes"
      ? `<span class="badge-yes">Yes</span>`
      : `<span class="badge-no">No</span>`;
  }

  // -----------------------------------------------------------------
  // Fetch and render aggregate stats
  // -----------------------------------------------------------------
  async function loadStats() {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.FEEDBACK_ENDPOINT}/stats`);
      if (!response.ok) throw new Error(`Failed to load stats (status ${response.status})`);
      const stats = await response.json();

      statTotal.textContent = stats.total_feedback;
      statAvgRating.textContent = stats.total_feedback > 0 ? `${stats.average_overall_rating.toFixed(1)} / 5` : "—";
      statRecommend.textContent = stats.total_feedback > 0 ? `${stats.recommend_percentage.toFixed(0)}%` : "—";
      statVisitAgain.textContent = stats.total_feedback > 0 ? `${stats.visit_again_percentage.toFixed(0)}%` : "—";
    } catch (err) {
      statTotal.textContent = "—";
      statAvgRating.textContent = "—";
      statRecommend.textContent = "—";
      statVisitAgain.textContent = "—";
      showAdminError(`Could not load dashboard stats. Is the backend running at ${API_CONFIG.BASE_URL}? (${err.message})`);
    }
  }

  // -----------------------------------------------------------------
  // Build query params from current filter/sort/page state
  // -----------------------------------------------------------------
  function buildQueryParams() {
    const params = new URLSearchParams();
    params.set("page", currentPage);
    params.set("page_size", pageSize);
    params.set("sort_by", sortBySelect.value);
    params.set("sort_order", sortOrderSelect.value);

    const search = searchInput.value.trim();
    if (search) params.set("search", search);

    if (minRatingFilter.value) params.set("min_rating", minRatingFilter.value);
    if (maxRatingFilter.value) params.set("max_rating", maxRatingFilter.value);
    if (startDateFilter.value) params.set("start_date", startDateFilter.value);
    if (endDateFilter.value) params.set("end_date", endDateFilter.value);

    return params;
  }

  // -----------------------------------------------------------------
  // Fetch and render the feedback table
  // -----------------------------------------------------------------
  async function loadFeedbackList() {
    clearAdminError();
    resultsSummary.textContent = "Loading feedback...";
    tableBody.innerHTML = "";
    emptyState.classList.add("d-none");

    try {
      const params = buildQueryParams();
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.FEEDBACK_ENDPOINT}?${params.toString()}`);
      if (!response.ok) throw new Error(`Failed to load feedback (status ${response.status})`);
      const data = await response.json();

      renderTable(data.results);
      renderPagination(data.total, data.page, data.page_size);

      const start = data.total === 0 ? 0 : (data.page - 1) * data.page_size + 1;
      const end = Math.min(data.page * data.page_size, data.total);
      resultsSummary.textContent = data.total === 0
        ? "No feedback records match your filters."
        : `Showing ${start}–${end} of ${data.total} feedback record${data.total === 1 ? "" : "s"}`;

      if (data.results.length === 0) {
        emptyState.classList.remove("d-none");
      }
    } catch (err) {
      resultsSummary.textContent = "";
      showAdminError(`Could not load feedback records. Is the backend running at ${API_CONFIG.BASE_URL}? (${err.message})`);
    }
  }

  function renderTable(records) {
    tableBody.innerHTML = records
      .map(
        (record) => `
        <tr>
          <td>${record.id}</td>
          <td>
            <div class="fw-bold">${escapeHtml(record.customer_name)}</div>
            <div class="text-secondary small">${escapeHtml(record.email)}</div>
          </td>
          <td>${escapeHtml(record.flavour)}</td>
          <td>${formatDate(record.visit_date)}</td>
          <td><span class="rating-pill">${starString(record.overall_rating)}</span></td>
          <td>${badgeFor(record.recommend_shop)}</td>
          <td>${badgeFor(record.visit_again)}</td>
          <td class="text-secondary small">${formatDateTime(record.created_at)}</td>
          <td class="text-end">
            <button class="btn btn-sm btn-cone me-1 view-btn" data-id="${record.id}" title="View details">
              <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-icon-delete delete-btn" data-id="${record.id}" title="Delete feedback">
              <i class="bi bi-trash3"></i>
            </button>
          </td>
        </tr>`
      )
      .join("");

    // Wire up view/delete buttons for the newly rendered rows
    tableBody.querySelectorAll(".view-btn").forEach((btn) => {
      btn.addEventListener("click", () => openDetailModal(btn.dataset.id));
    });
    tableBody.querySelectorAll(".delete-btn").forEach((btn) => {
      btn.addEventListener("click", () => openDeleteModal(btn.dataset.id));
    });
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // -----------------------------------------------------------------
  // Pagination controls
  // -----------------------------------------------------------------
  function renderPagination(total, page, size) {
    const totalPages = Math.max(1, Math.ceil(total / size));
    paginationControls.innerHTML = "";

    if (totalPages <= 1) return;

    const createPageItem = (label, targetPage, disabled = false, active = false) => {
      const li = document.createElement("li");
      li.className = `page-item ${disabled ? "disabled" : ""} ${active ? "active" : ""}`;
      const a = document.createElement("a");
      a.className = "page-link";
      a.href = "#";
      a.textContent = label;
      a.addEventListener("click", (e) => {
        e.preventDefault();
        if (!disabled && targetPage !== page) {
          currentPage = targetPage;
          loadFeedbackList();
        }
      });
      li.appendChild(a);
      return li;
    };

    paginationControls.appendChild(createPageItem("Previous", page - 1, page === 1));

    const windowSize = 5;
    let startPage = Math.max(1, page - Math.floor(windowSize / 2));
    let endPage = Math.min(totalPages, startPage + windowSize - 1);
    startPage = Math.max(1, endPage - windowSize + 1);

    for (let p = startPage; p <= endPage; p++) {
      paginationControls.appendChild(createPageItem(String(p), p, false, p === page));
    }

    paginationControls.appendChild(createPageItem("Next", page + 1, page === totalPages));
  }

  // -----------------------------------------------------------------
  // Detail modal
  // -----------------------------------------------------------------
  async function openDetailModal(id) {
    detailModalBody.innerHTML = `<div class="text-center py-4"><div class="spinner-border text-danger"></div></div>`;
    detailModal.show();

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.FEEDBACK_ENDPOINT}/${id}`);
      if (!response.ok) throw new Error(`Record not found (status ${response.status})`);
      const record = await response.json();

      detailModalBody.innerHTML = `
        <div class="row g-3">
          <div class="col-md-6">
            <div class="text-secondary small fw-bold text-uppercase">Customer</div>
            <div class="fw-bold">${escapeHtml(record.customer_name)}</div>
            <div>${escapeHtml(record.email)}</div>
            <div>${escapeHtml(record.phone)}</div>
          </div>
          <div class="col-md-6">
            <div class="text-secondary small fw-bold text-uppercase">Visit</div>
            <div>${formatDate(record.visit_date)}</div>
            <div>Flavor: <strong>${escapeHtml(record.flavour)}</strong></div>
          </div>
          <div class="col-12"><hr></div>
          <div class="col-6 col-md-4">
            <div class="text-secondary small">Taste</div>
            <div class="rating-pill">${starString(record.taste_rating)}</div>
          </div>
          <div class="col-6 col-md-4">
            <div class="text-secondary small">Quality</div>
            <div class="rating-pill">${starString(record.quality_rating)}</div>
          </div>
          <div class="col-6 col-md-4">
            <div class="text-secondary small">Staff Service</div>
            <div class="rating-pill">${starString(record.staff_rating)}</div>
          </div>
          <div class="col-6 col-md-4">
            <div class="text-secondary small">Cleanliness</div>
            <div class="rating-pill">${starString(record.cleanliness_rating)}</div>
          </div>
          <div class="col-6 col-md-4">
            <div class="text-secondary small">Overall</div>
            <div class="rating-pill">${starString(record.overall_rating)}</div>
          </div>
          <div class="col-12"><hr></div>
          <div class="col-6">
            <div class="text-secondary small">Would visit again</div>
            ${badgeFor(record.visit_again)}
          </div>
          <div class="col-6">
            <div class="text-secondary small">Would recommend</div>
            ${badgeFor(record.recommend_shop)}
          </div>
          <div class="col-12">
            <div class="text-secondary small fw-bold text-uppercase mt-2">Comments</div>
            <p class="mb-0">${record.comments ? escapeHtml(record.comments) : "<em>No comments left.</em>"}</p>
          </div>
          ${
            record.image_path
              ? `<div class="col-12">
                  <div class="text-secondary small fw-bold text-uppercase mt-2">Photo</div>
                  <img src="${API_CONFIG.BASE_URL}/${record.image_path}" class="img-fluid rounded" style="max-height:260px;" alt="Customer uploaded feedback photo">
                 </div>`
              : ""
          }
          <div class="col-12 text-secondary small mt-2">Submitted ${formatDateTime(record.created_at)} · Record #${record.id}</div>
        </div>
      `;
    } catch (err) {
      detailModalBody.innerHTML = `<div class="alert alert-danger mb-0">Could not load this record: ${escapeHtml(err.message)}</div>`;
    }
  }

  // -----------------------------------------------------------------
  // Delete modal + action
  // -----------------------------------------------------------------
  function openDeleteModal(id) {
    pendingDeleteId = id;
    deleteModal.show();
  }

  confirmDeleteBtn.addEventListener("click", async () => {
    if (!pendingDeleteId) return;
    confirmDeleteBtn.disabled = true;
    confirmDeleteBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Deleting...`;

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.FEEDBACK_ENDPOINT}/${pendingDeleteId}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error(`Failed to delete (status ${response.status})`);

      deleteModal.hide();
      await Promise.all([loadFeedbackList(), loadStats()]);
    } catch (err) {
      showAdminError(`Could not delete feedback record: ${err.message}`);
      deleteModal.hide();
    } finally {
      pendingDeleteId = null;
      confirmDeleteBtn.disabled = false;
      confirmDeleteBtn.innerHTML = "Delete Permanently";
    }
  });

  // -----------------------------------------------------------------
  // Filter bar interactions
  // -----------------------------------------------------------------
  applyFiltersBtn.addEventListener("click", () => {
    currentPage = 1;
    loadFeedbackList();
  });

  clearFiltersBtn.addEventListener("click", () => {
    searchInput.value = "";
    minRatingFilter.value = "";
    maxRatingFilter.value = "";
    startDateFilter.value = "";
    endDateFilter.value = "";
    sortBySelect.value = "created_at";
    sortOrderSelect.value = "desc";
    currentPage = 1;
    loadFeedbackList();
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      currentPage = 1;
      loadFeedbackList();
    }
  });

  sortBySelect.addEventListener("change", () => {
    currentPage = 1;
    loadFeedbackList();
  });
  sortOrderSelect.addEventListener("change", () => {
    currentPage = 1;
    loadFeedbackList();
  });

  // -----------------------------------------------------------------
  // Initial load
  // -----------------------------------------------------------------
  loadStats();
  loadFeedbackList();
})();
