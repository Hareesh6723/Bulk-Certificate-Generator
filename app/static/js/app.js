// CertForge Dashboard Application Logic

let selectedTheme = "classic_gold";
let currentPollingJobId = null;
let pollTimer = null;

// Initial sample data for zero-friction testing
const INITIAL_RECIPIENTS = [
  { name: "Alice Johnson", email: "alice.johnson@example.com", grade: "Distinction" },
  { name: "Bob Smith", email: "bob.smith@example.com", grade: "Merit" },
  { name: "Carol Williams", email: "carol.williams@example.com", grade: "Excellence" },
  { name: "FAIL_TEST_RECIPIENT", email: "test.fail@example.com", grade: "Simulated Error Test" }
];

document.addEventListener("DOMContentLoaded", () => {
  renderRecipients(INITIAL_RECIPIENTS);
  setupDropzone();
});

function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));

  const targetBtn = document.getElementById(`tab-btn-${tabName}`);
  const targetPane = document.getElementById(`tab-${tabName}`);

  if (targetBtn && targetPane) {
    targetBtn.classList.add("active");
    targetPane.classList.add("active");
  }

  if (tabName === "monitor") {
    fetchJobHistory();
  }
}

function selectTheme(theme) {
  selectedTheme = theme;
  document.querySelectorAll(".theme-card").forEach(el => el.classList.remove("selected"));
  if (theme === "classic_gold") document.getElementById("theme-gold")?.classList.add("selected");
  if (theme === "sapphire_modern") document.getElementById("theme-sapphire")?.classList.add("selected");
  if (theme === "emerald_academic") document.getElementById("theme-emerald")?.classList.add("selected");
}

function updateRecipientCount() {
  const count = document.querySelectorAll("#recipients-tbody tr").length;
  document.getElementById("recipients-count").textContent = count;
}

function renderRecipients(list) {
  const tbody = document.getElementById("recipients-tbody");
  tbody.innerHTML = "";
  list.forEach(item => {
    appendRecipientRow(item.name, item.email, item.grade || "");
  });
  updateRecipientCount();
}

function appendRecipientRow(name = "", email = "", grade = "") {
  const tbody = document.getElementById("recipients-tbody");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input type="text" class="table-input row-name" placeholder="Full Name" value="${escapeHtml(name)}"></td>
    <td><input type="email" class="table-input row-email" placeholder="Email Address" value="${escapeHtml(email)}"></td>
    <td><input type="text" class="table-input row-grade" placeholder="e.g. Distinction" value="${escapeHtml(grade)}"></td>
    <td><button class="btn btn-danger btn-sm" onclick="removeRow(this)">✕</button></td>
  `;
  tbody.appendChild(tr);
  updateRecipientCount();
}

function addRecipientRow() {
  appendRecipientRow();
}

function removeRow(btn) {
  const row = btn.closest("tr");
  row.remove();
  updateRecipientCount();
}

function loadSampleData() {
  renderRecipients([
    { name: "Sophia Martinez", email: "sophia.m@example.com", grade: "Distinction" },
    { name: "Liam Chen", email: "liam.chen@example.com", grade: "Honors" },
    { name: "Emily Watson", email: "emily.watson@example.com", grade: "High Merit" },
    { name: "Lucas Vance", email: "lucas.v@example.com", grade: "First Class" },
    { name: "FAIL_TEST_RECIPIENT", email: "error.case@example.com", grade: "Demonstrates Failure Isolation" }
  ]);
  showToast("Loaded 5 demo recipients (including 1 isolation test case)", "info");
}

function setupDropzone() {
  const dropzone = document.getElementById("csv-dropzone");
  if (!dropzone) return;

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
    if (e.dataTransfer.files.length) {
      parseCSVFile(e.dataTransfer.files[0]);
    }
  });
}

function handleCSVUpload(event) {
  const file = event.target.files[0];
  if (file) {
    parseCSVFile(file);
  }
}

function parseCSVFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const text = e.target.result;
    const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0);
    if (lines.length < 2) {
      showToast("CSV file must have a header and at least one recipient row.", "error");
      return;
    }

    const headers = lines[0].split(",").map(h => h.trim().toLowerCase());
    const nameIdx = headers.indexOf("name");
    const emailIdx = headers.indexOf("email");
    const gradeIdx = headers.indexOf("grade");

    if (nameIdx === -1 || emailIdx === -1) {
      showToast("CSV must contain 'name' and 'email' column headers.", "error");
      return;
    }

    const parsed = [];
    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].split(",").map(p => p.trim());
      if (parts[nameIdx] && parts[emailIdx]) {
        parsed.push({
          name: parts[nameIdx],
          email: parts[emailIdx],
          grade: gradeIdx !== -1 && parts[gradeIdx] ? parts[gradeIdx] : ""
        });
      }
    }

    if (parsed.length === 0) {
      showToast("No valid recipient rows found in CSV.", "error");
      return;
    }

    renderRecipients(parsed);
    showToast(`Successfully parsed ${parsed.length} recipients from CSV!`, "success");
  };
  reader.readAsText(file);
}

async function submitBulkJob() {
  const eventTitle = document.getElementById("input-event-title").value.trim();
  const issuerName = document.getElementById("input-issuer").value.trim();
  const signatoryName = document.getElementById("input-signatory-name").value.trim();
  const signatoryTitle = document.getElementById("input-signatory-title").value.trim();
  const issueDate = document.getElementById("input-issue-date").value.trim();

  if (!eventTitle) {
    showToast("Please enter a course or event title.", "error");
    return;
  }

  // Collect recipients
  const rows = document.querySelectorAll("#recipients-tbody tr");
  const recipients = [];
  rows.forEach(tr => {
    const name = tr.querySelector(".row-name")?.value.trim();
    const email = tr.querySelector(".row-email")?.value.trim();
    const grade = tr.querySelector(".row-grade")?.value.trim();

    if (name && email) {
      recipients.push({
        name: name,
        email: email,
        metadata: grade ? { grade: grade } : {}
      });
    }
  });

  if (recipients.length === 0) {
    showToast("Please enter at least one recipient with name and email.", "error");
    return;
  }

  const payload = {
    event_title: eventTitle,
    issuer_name: issuerName,
    signatory_name: signatoryName,
    signatory_title: signatoryTitle,
    issue_date: issueDate,
    template_theme: selectedTheme,
    recipients: recipients
  };

  const submitBtn = document.getElementById("btn-submit-job");
  submitBtn.disabled = true;
  submitBtn.innerHTML = "⏳ Dispatching Job...";

  try {
    const response = await fetch("/api/v1/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail ? (typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)) : "Failed to create job");
    }

    const data = await response.json();
    showToast(`Job submitted! Tracking progress for ${data.total_recipients} certificates.`, "success");

    // Start live tracking
    startJobTracking(data.job_id);

  } catch (error) {
    showToast(`Submission error: ${error.message}`, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "⚡ Generate Bulk Certificates Now";
  }
}

function startJobTracking(jobId) {
  if (pollTimer) clearInterval(pollTimer);
  currentPollingJobId = jobId;

  const section = document.getElementById("live-job-section");
  section.style.display = "block";
  section.scrollIntoView({ behavior: "smooth" });

  document.getElementById("job-id-text").textContent = jobId;
  
  // Instant fetch and setup interval
  pollJobStatus();
  pollTimer = setInterval(pollJobStatus, 1200);
}

function pollJobStatusManual() {
  if (currentPollingJobId) {
    pollJobStatus();
    showToast("Refreshed job progress", "info");
  }
}

async function pollJobStatus() {
  if (!currentPollingJobId) return;

  try {
    const res = await fetch(`/api/v1/jobs/${currentPollingJobId}`);
    if (!res.ok) throw new Error("Could not fetch job status");

    const job = await res.json();
    updateLiveTrackerUI(job);

    // Stop polling when terminal state is reached
    if (["COMPLETED", "PARTIALLY_COMPLETED", "FAILED"].includes(job.status)) {
      clearInterval(pollTimer);
      pollTimer = null;
      if (job.status === "COMPLETED") {
        showToast("🎉 All certificates generated successfully!", "success");
      } else if (job.status === "PARTIALLY_COMPLETED") {
        showToast("⚠️ Job finished with partial failures (handled cleanly without blocking others).", "warning");
      } else {
        showToast("Job finished with failures.", "error");
      }
    }
  } catch (err) {
    console.error("Polling error:", err);
  }
}

function updateLiveTrackerUI(job) {
  document.getElementById("job-event-title-display").textContent = job.event_title;
  
  // Status Badge
  const badge = document.getElementById("job-status-badge");
  badge.textContent = job.status.replace("_", " ");
  badge.className = "badge";
  if (job.status === "PENDING") badge.classList.add("badge-pending");
  else if (job.status === "PROCESSING") badge.classList.add("badge-processing");
  else if (job.status === "COMPLETED") badge.classList.add("badge-completed");
  else if (job.status === "PARTIALLY_COMPLETED") badge.classList.add("badge-partial");
  else badge.classList.add("badge-failed");

  // Counters
  document.getElementById("stat-total").textContent = job.total_recipients;
  document.getElementById("stat-processed").textContent = job.processed_count;
  document.getElementById("stat-succeeded").textContent = job.success_count;
  document.getElementById("stat-failed").textContent = job.failure_count;

  // Progress Bar
  const fill = document.getElementById("progress-bar-fill");
  fill.style.width = `${job.progress_percentage}%`;

  // ZIP Download button
  const zipBtn = document.getElementById("btn-download-all-zip");
  if (job.success_count > 0 && job.zip_download_url) {
    zipBtn.href = job.zip_download_url;
    zipBtn.style.display = "inline-flex";
  } else {
    zipBtn.style.display = "none";
  }

  // Populate individual recipients breakdown
  const tbody = document.getElementById("job-certs-tbody");
  tbody.innerHTML = "";

  (job.certificates || []).forEach(cert => {
    const tr = document.createElement("tr");

    let statusPill = "";
    if (cert.status === "SUCCESS") {
      statusPill = `<span class="badge badge-completed">✓ Ready</span>`;
    } else if (cert.status === "FAILED") {
      statusPill = `<span class="badge badge-failed">✕ Failed</span>`;
    } else {
      statusPill = `<span class="badge badge-processing">⏳ ${cert.status}</span>`;
    }

    let actions = "";
    if (cert.status === "SUCCESS") {
      actions = `
        <div style="display: flex; gap: 0.4rem;">
          <a href="${cert.download_url}" class="btn btn-table-pdf btn-sm" download title="Download PDF">⬇ PDF</a>
          <button class="btn btn-table-preview btn-sm" onclick="openPreview('${cert.preview_url}', '${escapeHtml(cert.recipient_name)}')" title="Preview Inline">👁 Preview</button>
          <a href="${cert.verification_url}" target="_blank" class="btn btn-table-verify btn-sm" title="Public Verification Portal">🛡 Verify</a>
        </div>
      `;
    } else {
      actions = `<span style="color: var(--text-muted); font-size: 0.8rem;">Unavailable</span>`;
    }

    let errorCell = "";
    if (cert.error_message) {
      errorCell = `<span style="color: #991b1b; font-size: 0.8rem; background: #fef2f2; border: 1px solid #fecaca; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 500;">${escapeHtml(cert.error_message)}</span>`;
    } else {
      errorCell = `<span style="color: var(--text-muted);">-</span>`;
    }

    tr.innerHTML = `
      <td><strong>${escapeHtml(cert.recipient_name)}</strong></td>
      <td style="color: var(--text-secondary);">${escapeHtml(cert.recipient_email)}</td>
      <td>${statusPill}</td>
      <td>${actions}</td>
      <td>${errorCell}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function fetchJobHistory() {
  const tbody = document.getElementById("history-tbody");
  tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading jobs...</td></tr>`;

  try {
    const res = await fetch("/api/v1/jobs");
    if (!res.ok) throw new Error("Could not load jobs");

    const jobs = await res.json();
    if (jobs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-secondary); padding: 2rem;">No jobs generated yet. Create your first bulk job!</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    jobs.forEach(job => {
      const tr = document.createElement("tr");

      let badgeClass = "badge-pending";
      if (job.status === "COMPLETED") badgeClass = "badge-completed";
      if (job.status === "PARTIALLY_COMPLETED") badgeClass = "badge-partial";
      if (job.status === "FAILED") badgeClass = "badge-failed";
      if (job.status === "PROCESSING") badgeClass = "badge-processing";

      const createdDate = new Date(job.created_at).toLocaleString();

      tr.innerHTML = `
        <td><code style="color: #0f172a; font-weight: 600; background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 4px;">${job.job_id.substring(0, 8)}...</code></td>
        <td><strong>${escapeHtml(job.event_title)}</strong></td>
        <td style="font-size: 0.8rem; color: var(--text-secondary);">${createdDate}</td>
        <td><span class="badge ${badgeClass}">${job.status.replace("_", " ")}</span></td>
        <td style="font-weight: 600;">${job.success_count} / ${job.total_recipients}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="inspectJobFromHistory('${job.job_id}')">
            🔍 Inspect
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #b91c1c; padding: 2rem;">Error: ${err.message}</td></tr>`;
  }
}

function inspectJobFromHistory(jobId) {
  switchTab("generator");
  startJobTracking(jobId);
}

async function handleManualVerify() {
  const id = document.getElementById("input-verify-id").value.trim();
  const box = document.getElementById("verify-result-box");

  if (!id) {
    showToast("Please enter a Certificate ID", "error");
    return;
  }

  box.style.display = "block";
  box.innerHTML = `<div style="text-align: center; padding: 1.5rem; color: var(--text-secondary);">Querying credential registry...</div>`;

  try {
    const res = await fetch(`/api/v1/verify/${id}`);
    const data = await res.json();

    if (data.is_valid) {
      box.innerHTML = `
        <div style="background: #ffffff; border: 1px solid var(--border-light); border-radius: 12px; padding: 1.5rem; box-shadow: var(--shadow-sm);">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span class="badge badge-completed">✓ OFFICIAL CREDENTIAL VERIFIED</span>
          </div>
          <h3 style="font-size: 1.35rem; color: #0f172a; font-weight: 700; margin-bottom: 0.25rem;">${escapeHtml(data.recipient_name)}</h3>
          <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 1rem;">Recipient: ${escapeHtml(data.recipient_email_masked)}</p>
          <div style="border-top: 1px solid var(--border-light); padding-top: 0.75rem; font-size: 0.875rem; color: #334155; line-height: 1.8;">
            <div><strong>Program:</strong> ${escapeHtml(data.event_title)}</div>
            <div><strong>Authority:</strong> ${escapeHtml(data.issuer_name)}</div>
            <div><strong>Date of Issue:</strong> ${escapeHtml(data.issue_date)}</div>
          </div>
          <div style="margin-top: 1.25rem; display: flex; gap: 0.5rem;">
            <a href="${data.download_url}" class="btn btn-primary btn-sm" download>⬇ Download Official PDF</a>
            <a href="/verify/${data.certificate_id}" target="_blank" class="btn btn-secondary btn-sm">🔗 Public Badge Page</a>
          </div>
        </div>
      `;
    } else {
      box.innerHTML = `
        <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 1.5rem; text-align: center;">
          <div class="badge badge-failed" style="margin-bottom: 0.5rem;">✕ UNVERIFIED</div>
          <p style="color: #991b1b; font-weight: 600; font-size: 0.9rem;">No active verified credential found for ID <code>${escapeHtml(id)}</code></p>
        </div>
      `;
    }
  } catch (err) {
    box.innerHTML = `<div style="color: #991b1b; padding: 1rem;">Verification error: ${err.message}</div>`;
  }
}

function openPreview(previewUrl, recipientName) {
  const modal = document.getElementById("preview-modal");
  const iframe = document.getElementById("modal-iframe");
  const title = document.getElementById("modal-title");
  const newTab = document.getElementById("modal-new-tab");

  title.textContent = `Certificate Preview • ${recipientName}`;
  iframe.src = previewUrl;
  newTab.href = previewUrl;
  modal.classList.add("active");
}

function closePreviewModal(event) {
  const modal = document.getElementById("preview-modal");
  const iframe = document.getElementById("modal-iframe");
  iframe.src = "about:blank";
  modal.classList.remove("active");
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";

  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "❌";
  if (type === "warning") icon = "⚠️";

  toast.innerHTML = `<span>${icon}</span><span style="font-size: 0.9rem;">${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
