/* ClubHub — Main JavaScript */

// ── Date Display ─────────────────────────────────────────────────
(function() {
  const el = document.getElementById('currentDate');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleDateString('en-US', { weekday:'short', year:'numeric', month:'short', day:'numeric' });
  }
})();

// ── Mobile Sidebar ────────────────────────────────────────────────
(function() {
  const toggle  = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  if (!toggle || !sidebar) return;

  // Create overlay
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  });
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
})();

// ── Flash Auto-Dismiss ────────────────────────────────────────────
(function() {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(f => {
    setTimeout(() => {
      f.style.opacity = '0';
      f.style.transform = 'translateY(-8px)';
      f.style.transition = 'all .4s';
      setTimeout(() => f.remove(), 400);
    }, 4000);
  });
})();

// ── Delete Confirmation Modal ─────────────────────────────────────
function confirmDelete(formId, itemName) {
  // Create modal if not exists
  let overlay = document.getElementById('deleteModal');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'deleteModal';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>Confirm Delete</h3>
        <p id="deleteModalMsg">Are you sure you want to delete this item? This action cannot be undone.</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" onclick="closeDeleteModal()">Cancel</button>
          <button class="btn btn-danger" id="confirmDeleteBtn">Delete</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
  }

  document.getElementById('deleteModalMsg').textContent =
    `Are you sure you want to delete "${itemName}"? This action cannot be undone.`;

  overlay.classList.add('active');

  document.getElementById('confirmDeleteBtn').onclick = () => {
    document.getElementById(formId).submit();
  };
}

function closeDeleteModal() {
  const overlay = document.getElementById('deleteModal');
  if (overlay) overlay.classList.remove('active');
}

// Close on overlay click
document.addEventListener('click', (e) => {
  const overlay = document.getElementById('deleteModal');
  if (overlay && e.target === overlay) closeDeleteModal();
});

// ── Role Tabs on Login ────────────────────────────────────────────
(function() {
  const tabs = document.querySelectorAll('.role-tab');
  const roleInput = document.getElementById('roleInput');
  if (!tabs.length || !roleInput) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      roleInput.value = tab.dataset.role;
    });
  });
})();

// ── Table Search Filter ───────────────────────────────────────────
function filterTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(q) ? '' : 'none';
    });
  });
}

// ── Chart.js Initializer ──────────────────────────────────────────
function initMemberChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === 'undefined') return;

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'New Members',
        data,
        backgroundColor: 'rgba(201,168,76,0.25)',
        borderColor: 'rgba(201,168,76,0.8)',
        borderWidth: 1.5,
        borderRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1c2030',
          titleColor: '#e8e6e0',
          bodyColor: '#9a9890',
          borderColor: 'rgba(255,255,255,0.07)',
          borderWidth: 1,
        }
      },
      scales: {
        x: {
          ticks: { color: '#5c5a56', font: { family: 'DM Mono', size: 11 } },
          grid: { color: 'rgba(255,255,255,0.04)' },
          border: { color: 'rgba(255,255,255,0.07)' }
        },
        y: {
          ticks: { color: '#5c5a56', font: { family: 'DM Mono', size: 11 }, stepSize: 1 },
          grid: { color: 'rgba(255,255,255,0.04)' },
          border: { color: 'rgba(255,255,255,0.07)' }
        }
      }
    }
  });
}

function initAffiliationChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === 'undefined') return;

  const colors = [
    'rgba(201,168,76,0.7)',
    'rgba(74,127,165,0.7)',
    'rgba(76,175,129,0.7)',
    'rgba(224,156,58,0.7)',
    'rgba(165,74,127,0.7)',
    'rgba(127,165,74,0.7)',
  ];

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.slice(0, data.length),
        borderColor: '#141720',
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#9a9890',
            font: { family: 'DM Mono', size: 11 },
            boxWidth: 12,
            padding: 12,
          }
        },
        tooltip: {
          backgroundColor: '#1c2030',
          titleColor: '#e8e6e0',
          bodyColor: '#9a9890',
          borderColor: 'rgba(255,255,255,0.07)',
          borderWidth: 1,
        }
      },
      cutout: '65%',
    }
  });
}

// ── Animate stat numbers ──────────────────────────────────────────
function animateCounters() {
  const counters = document.querySelectorAll('.stat-value[data-target]');
  counters.forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    let current = 0;
    const step = Math.ceil(target / 30);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 30);
  });
}

document.addEventListener('DOMContentLoaded', animateCounters);
