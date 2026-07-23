<template>
  <div class="page">
    <!-- USER PROFILE CARD -->
    <div class="top-row">
      <div class="user-card">
        <div class="user-avatar">
          <i class="fas fa-user"></i>
        </div>
        <div class="user-info">
          <h2 class="user-name">{{ user.name }}</h2>
          <p class="user-email">{{ user.email }}</p>
          <div class="user-id-badge">
            <i class="fas fa-fingerprint"></i>
            <span>{{ user.public_id }}</span>
          </div>
        </div>
      </div>
      <div class="top-actions">
        <div class="date-chip">
          <i class="fas fa-calendar-day"></i>
          <span>{{ currentDate }}</span>
        </div>
        <button class="btn-primary" @click="showRoleModal = true">
          <i class="fas fa-user-shield"></i> Request Role Change
        </button>
      </div>
    </div>

    <!-- STATS ROW (Neomorphic Cards) -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon-wrap blue">
          <i class="fas fa-folder-open stat-icon"></i>
        </div>
        <div class="stat-meta">
          <div class="stat-val">{{ stats.totalRecords }}</div>
          <div class="stat-label">Accessible Records</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap orange">
          <i class="fas fa-clock stat-icon"></i>
        </div>
        <div class="stat-meta">
          <div class="stat-val">{{ stats.recentAdded }}</div>
          <div class="stat-label">Added this week</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap green">
          <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell', 'stat-icon']" :style="{ color: isMuted ? 'var(--error-500)' : undefined }"></i>
        </div>
        <div class="stat-meta">
          <div class="stat-val">{{ stats.unreadNotifs }}</div>
          <div class="stat-label">Unread Notifications</div>
        </div>
      </div>
    </div>

    <!-- RECENT ACTIVITY TABLE -->
    <div class="recent-card">
      <div class="recent-header">
        <div class="header-title">
          <i class="fas fa-history"></i>
          <h2>Recent Records</h2>
        </div>
        <button class="btn-ghost" @click="$router.push('/records')">View All</button>
      </div>
      <div class="recent-body">
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i> Fetching recent records...
        </div>
        <div v-else-if="recentRecords.length === 0" class="empty-state">
          <i class="fas fa-inbox"></i>
          <p>No recent records found.</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Record ID</th>
              <th>Name</th>
              <th>Company</th>
              <th>Date Added</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in recentRecords" :key="r.public_id" class="data-row">
              <td><span class="badge-id">{{ r.public_id }}</span></td>
              <td class="bold">{{ r.name }}</td>
              <td>{{ r.source_company || '—' }}</td>
              <td class="muted">{{ formatDate(r.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ROLE CHANGE MODAL (Glassmorphism & Neomorphism Overlay) -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showRoleModal" @click.self="showRoleModal = false">
        <div class="modal modal-md">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon-wrap">
                <i class="fas fa-user-shield"></i>
              </div>
              <div>
                <h2>Request Role Change</h2>
                <span class="modal-subtitle">Submit governance request to system administrators</span>
              </div>
            </div>
            <button class="modal-close" @click="showRoleModal = false" aria-label="Close">
              <i class="fas fa-times"></i>
            </button>
          </div>

          <div class="modal-body">
            <!-- CURRENT ROLE BANNER -->
            <div class="current-role-banner">
              <i class="fas fa-circle-info banner-icon"></i>
              <div class="banner-text">
                Your account currently has <strong class="role-highlight">{{ user.role || 'VIEWER' }}</strong> access. Select your requested role below:
              </div>
            </div>

            <!-- DESIRED ROLE CARDS -->
            <div class="form-group mt-4">
              <label class="form-label">Select Requested Role</label>
              <div class="role-cards-grid">
                
                <!-- VIEWER CARD -->
                <div 
                  class="role-card" 
                  :class="{ active: requestedRole === 'VIEWER', disabled: (user.role ? user.role.toUpperCase() : 'VIEWER') === 'VIEWER' }"
                  @click="requestedRole = 'VIEWER'"
                >
                  <div class="role-card-header">
                    <div class="role-icon-box viewer">
                      <i class="fas fa-eye"></i>
                    </div>
                    <div class="check-badge" v-if="requestedRole === 'VIEWER'">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                  <div class="role-card-title">Viewer</div>
                  <div class="role-card-desc">Read-only access to view disseminated records &amp; logs.</div>
                  <span class="current-tag" v-if="(user.role ? user.role.toUpperCase() : 'VIEWER') === 'VIEWER'">Current Role</span>
                </div>

                <!-- COLLABORATOR CARD -->
                <div 
                  class="role-card" 
                  :class="{ active: requestedRole === 'COLLABORATOR', disabled: (user.role ? user.role.toUpperCase() : 'VIEWER') === 'COLLABORATOR' }"
                  @click="requestedRole = 'COLLABORATOR'"
                >
                  <div class="role-card-header">
                    <div class="role-icon-box collaborator">
                      <i class="fas fa-pen-to-square"></i>
                    </div>
                    <div class="check-badge" v-if="requestedRole === 'COLLABORATOR'">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                  <div class="role-card-title">Collaborator</div>
                  <div class="role-card-desc">Create, upload, and initiate record workflows.</div>
                  <span class="current-tag" v-if="(user.role ? user.role.toUpperCase() : 'VIEWER') === 'COLLABORATOR'">Current Role</span>
                </div>

              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-ghost" @click="showRoleModal = false">Cancel</button>
            <button 
              class="btn-primary" 
              @click="submitRoleRequest" 
              :disabled="requestingRole || requestedRole === (user.role ? user.role.toUpperCase() : 'VIEWER')"
            >
              <i class="fas fa-spinner fa-spin" v-if="requestingRole"></i>
              <i class="fas fa-paper-plane" v-else></i>
              <span>{{ requestingRole ? 'Submitting...' : 'Submit Request' }}</span>
            </button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const currentDate = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })

const { unreadCount, notify, isMuted } = useNotifications()

const stats = ref({
  totalRecords: 0,
  recentAdded: 0,
  unreadNotifs: unreadCount,
})

const recentRecords = ref<any[]>([])
const loading = ref(true)

const showRoleModal = ref(false)
const requestedRole = ref(user.role ? user.role.toUpperCase() : 'VIEWER')
const requestingRole = ref(false)

async function submitRoleRequest() {
  requestingRole.value = true
  try {
    await api.post('workflows/role-change/request/', { role: requestedRole.value })
    notify('Request Submitted', 'Your role change request has been sent for approval.', 'SUCCESS')
    showRoleModal.value = false
  } catch (err: any) {
    console.error(err)
    const msg = err?.response?.data?.error || 'Failed to submit role change request'
    notify('Request Failed', msg, 'ERROR')
  } finally {
    requestingRole.value = false
  }
}

async function fetchDashboardData() {
  try {
    const res = await api.get('records/', { params: { page: 1, page_size: 5 } })
    recentRecords.value = res.data.results
    stats.value.totalRecords = res.data.count

    const oneWeekAgo = new Date()
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7)
    stats.value.recentAdded = recentRecords.value.filter(
      r => new Date(r.created_at) >= oneWeekAgo
    ).length

  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(fetchDashboardData)
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.top-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.top-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.date-chip {
  background: var(--bg-base);
  box-shadow: var(--neu-btn);
  padding: 8px 16px;
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  color: var(--orange-accent);
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: var(--radius-pill);
}

/* ── User Card (Neomorphism) ─────────────────────────────────── */
.user-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--bg-base);
  box-shadow: var(--neu-card);
  border-radius: var(--radius-2xl);
  padding: 20px 24px;
  flex: 1;
  max-width: 460px;
  transition: transform var(--duration-base) var(--ease-out);
}
.user-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--neu-card-hover);
}

.user-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-2xl);
  box-shadow: var(--sku-btn-primary-shadow);
  flex-shrink: 0;
}

.user-info { display: flex; flex-direction: column; gap: 2px; }
.user-name { font-size: var(--text-xl); font-weight: var(--weight-extrabold); color: var(--text-primary); margin: 0; }
.user-email { font-size: var(--text-xs); color: var(--text-secondary); margin: 0; }
.user-id-badge {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--orange-bg-subtle);
  border: 1px solid var(--orange-border);
  color: var(--orange-accent);
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: var(--weight-bold);
  font-family: monospace;
}

/* ── Stats Row ───────────────────────────────────────────────── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg-base);
  box-shadow: var(--neu-card);
  border-radius: var(--radius-xl);
  padding: 20px;
  transition: transform var(--duration-base) var(--ease-out);
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--neu-card-hover);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xl);
  background: var(--bg-base);
  box-shadow: var(--neu-inset);
  flex-shrink: 0;
}
.stat-icon-wrap.blue   { color: var(--info-600); }
.stat-icon-wrap.orange { color: var(--orange-accent); }
.stat-icon-wrap.green  { color: var(--success-600); }

.stat-meta { display: flex; flex-direction: column; }
.stat-val { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); line-height: 1.1; }
.stat-label { font-size: var(--text-xs); color: var(--text-secondary); font-weight: var(--weight-semibold); margin-top: 2px; }

/* ── Table Container (Neomorphism) ───────────────────────────── */
.recent-card {
  background: var(--bg-base);
  border: none;
  border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card);
  overflow: hidden;
}

.recent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid var(--card-divider);
}
.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-title i { color: var(--orange-accent); font-size: var(--text-base); }
.recent-header h2 { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }

.loading-state, .empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-muted);
  font-size: var(--text-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.empty-state i { font-size: 28px; color: var(--neutral-400); }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  padding: 12px 24px;
  text-align: left;
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--neutral-700);
  border-bottom: 1px solid var(--card-divider);
  background: var(--bg-base);
}
.data-row {
  border-bottom: 1px solid var(--card-divider);
  transition: background var(--duration-fast);
}
.data-row:last-child { border-bottom: none; }
.data-row:hover {
  background: var(--orange-bg-subtle);
}
.data-table td { padding: 14px 24px; font-size: var(--text-sm); color: var(--text-primary); }
.bold { font-weight: var(--weight-bold); color: var(--text-primary); }
.muted { color: var(--text-secondary); font-size: var(--text-xs); }

.badge-id {
  background: var(--bg-base);
  color: var(--neutral-700);
  border: none;
  border-radius: var(--radius-xs);
  padding: 2px 8px;
  font-size: 11px;
  font-weight: var(--weight-bold);
  font-family: monospace;
}

/* ── Modal (Glassmorphism & Neomorphism) ────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.55);
  backdrop-filter: blur(12px) saturate(1.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: 20px;
}

.modal {
  background: var(--bg-app);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 420px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalIn 0.3s var(--ease-spring);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px 14px;
  border-bottom: 1px solid rgba(166, 169, 173, 0.2);
}
.modal-title-group { display: flex; align-items: center; gap: 12px; }
.modal-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  box-shadow: var(--sku-btn-primary-shadow);
  flex-shrink: 0;
}
.modal-header h2 { font-size: 15px; font-weight: 800; color: var(--text-primary); margin: 0; line-height: 1.2; }
.modal-subtitle { font-size: 10.5px; color: var(--text-muted); font-weight: var(--weight-medium); }

.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-input);
  box-shadow: var(--neu-inset);
  border: 1px solid rgba(166, 169, 173, 0.3);
  cursor: pointer;
  font-size: 11px;
  color: var(--text-muted);
  transition: all var(--duration-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-close:hover {
  background: var(--orange-bg-subtle);
  color: var(--orange-accent);
}

.modal-body { padding: 18px 22px; }

.current-role-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--orange-bg-light);
  border: 1px solid var(--orange-border);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  color: var(--orange-800);
  font-size: 11.5px;
  line-height: 1.35;
}
.banner-icon { font-size: 14px; color: var(--orange-600); }
.role-highlight { color: var(--orange-700); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px; }

.mt-4 { margin-top: 16px; }

.form-label {
  font-size: 11px;
  font-weight: 800;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  display: block;
}

/* Compact Role Cards Grid */
.role-cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.role-card {
  background: var(--bg-card);
  border: 2px solid rgba(166, 169, 173, 0.3);
  border-radius: var(--radius-lg);
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xs);
}

.role-card:hover:not(.disabled) {
  border-color: var(--orange-border);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.role-card.active {
  border-color: var(--orange-accent);
  background: linear-gradient(135deg, rgba(234, 108, 0, 0.08) 0%, rgba(255, 255, 255, 0.95) 100%);
  box-shadow: 0 3px 10px rgba(234, 108, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.role-card.disabled {
  opacity: 0.55;
  cursor: not-allowed;
  background: rgba(224, 216, 204, 0.4);
}

.role-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.role-icon-box {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}

.role-icon-box.viewer {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}

.role-icon-box.collaborator {
  background: rgba(234, 108, 0, 0.12);
  color: var(--orange-accent);
}

.check-badge {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--orange-accent);
  color: white;
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(234, 108, 0, 0.35);
}

.role-card-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.role-card-desc {
  font-size: 10.5px;
  color: var(--text-muted);
  line-height: 1.3;
  flex: 1;
}

.current-tag {
  margin-top: 6px;
  font-size: 8.5px;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--neutral-600);
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 5px;
  border-radius: 4px;
  align-self: flex-start;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 22px 18px;
  border-top: 1px solid rgba(166, 169, 173, 0.15);
  background: var(--bg-app);
}

/* Buttons (Skeuomorphism) */
.btn-primary {
  background: var(--orange-gradient);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--sku-btn-primary-shadow);
}
.btn-primary:hover:not(:disabled) {
  box-shadow: var(--sku-btn-primary-shadow-hover);
  transform: translateY(-1px);
}
.btn-primary:active:not(:disabled) {
  box-shadow: var(--sku-btn-primary-shadow-active);
  transform: translateY(0);
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  background: var(--bg-base);
  color: var(--text-secondary);
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--sku-btn-secondary-shadow);
}
.btn-ghost:hover {
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}
.btn-ghost:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@media (max-width: 900px) {
  .top-row { flex-direction: column; }
  .user-card { max-width: 100%; width: 100%; }
  .stats-row { grid-template-columns: 1fr; }
}
</style>
