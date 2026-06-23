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
            {{ user.public_id }}
          </div>
        </div>
      </div>
      <div class="top-actions">
        <div class="date-chip">
          <i class="fas fa-calendar"></i>
          {{ currentDate }}
        </div>
        <button class="btn-primary" @click="showRoleModal = true">
          <i class="fas fa-user-shield"></i> Request Role Change
        </button>
      </div>
    </div>

    <!-- STATS ROW -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon-wrap blue">
          <i class="fas fa-folder-open stat-icon"></i>
        </div>
        <div>
          <div class="stat-val">{{ stats.totalRecords }}</div>
          <div class="stat-label">Accessible Records</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap orange">
          <i class="fas fa-clock stat-icon"></i>
        </div>
        <div>
          <div class="stat-val">{{ stats.recentAdded }}</div>
          <div class="stat-label">Added this week</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap green">
          <i class="fas fa-check-circle stat-icon"></i>
        </div>
        <div>
          <div class="stat-val">{{ stats.unreadNotifs }}</div>
          <div class="stat-label">Unread Notifications</div>
        </div>
      </div>
    </div>

    <!-- RECENT ACTIVITY -->
    <div class="recent-card">
      <div class="recent-header">
        <h2>Recent Records</h2>
        <button class="btn-ghost" @click="$router.push('/records')">View All</button>
      </div>
      <div class="recent-body">
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i> Loading...
        </div>
        <div v-else-if="recentRecords.length === 0" class="empty-state">
          No recent records found.
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Record ID</th>
              <th>Name</th>
              <th>Company</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in recentRecords" :key="r.public_id" class="data-row">
              <td><span class="badge-id">{{ r.public_id }}</span></td>
              <td class="bold">{{ r.name }}</td>
              <td>{{ r.source_company }}</td>
              <td class="muted">{{ formatDate(r.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ROLE CHANGE MODAL -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showRoleModal" @click.self="showRoleModal = false">
        <div class="modal modal-sm">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-user-shield"></i></div>
              <h2>Request Role Change</h2>
            </div>
            <button class="modal-close" @click="showRoleModal = false"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div class="info-banner">
              <i class="fas fa-info-circle"></i>
              <p>Your current role is <strong>{{ user.role === 'ADMIN' ? 'Admin' : (user.role === 'COLLABORATOR' ? 'Collaborator' : 'Viewer') }}</strong>. Select the role you wish to request below. This will be sent to the administrator for approval.</p>
            </div>
            <div class="form-group mt-4">
              <label>Desired Role</label>
              <div class="role-toggle">
                <label class="toggle-option">
                  <input type="radio" v-model="requestedRole" value="VIEWER" />
                  <span class="toggle-label">
                    <i class="fas fa-eye"></i> Viewer
                  </span>
                </label>
                <label class="toggle-option">
                  <input type="radio" v-model="requestedRole" value="COLLABORATOR" />
                  <span class="toggle-label">
                    <i class="fas fa-edit"></i> Collaborator
                  </span>
                </label>
              </div>
              <p v-if="requestedRole === (user.role ? user.role.toUpperCase() : 'VIEWER')" class="error-text">
              
              </p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showRoleModal = false">Cancel</button>
            <button class="btn-primary" @click="submitRoleRequest" :disabled="requestingRole || requestedRole === (user.role ? user.role.toUpperCase() : 'VIEWER')">
              <i class="fas fa-spinner fa-spin" v-if="requestingRole"></i>
              {{ requestingRole ? 'Submitting...' : 'Submit Request' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const userName = computed(() => user.name?.split(' ')[0] || 'User')
const currentDate = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })

const { unreadCount, notify } = useNotifications()

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

    // Calculate added this week (mock implementation based on visible data, in real app backend provides this)
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
.page { display: flex; flex-direction: column; gap: 20px; animation: fadeInUp 0.4s ease both; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes subtlePulse {
  0%, 100% { box-shadow: 0 4px 10px rgba(234, 88, 12, 0.15); }
  50%      { box-shadow: 0 4px 18px rgba(234, 88, 12, 0.28); }
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title  { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0; }
.page-sub    { font-size: 13px; color: #64748b; margin: 4px 0 0; }

.top-row {
  display: flex; justify-content: space-between; align-items: flex-start;
}
.top-actions { display: flex; flex-direction: column; align-items: flex-end; gap: 12px; }

.date-chip {
  background: linear-gradient(135deg, #f0f4fa, #e6ecf5);
  border: 1.5px solid rgba(61, 90, 128, 0.15); border-radius: 999px;
  padding: 8px 16px; font-size: 13px; font-weight: 600; color: #3d5a80;
  display: inline-flex; align-items: center; gap: 8px;
  box-shadow: 0 2px 8px rgba(61, 90, 128, 0.05);
}

/* ─── User Card ─────────────────────────────────────────────── */
.user-card {
  display: flex; align-items: center; gap: 24px;
  background: linear-gradient(135deg, #edf2f9 0%, #e4ecf7 100%);
  border: 1.5px solid rgba(61, 90, 128, 0.18); border-radius: 24px; padding: 24px 30px;
  box-shadow: 0 4px 20px rgba(61, 90, 128, 0.06), inset 0 1px 0 rgba(255,255,255,0.7);
  flex: 1; max-width: 450px;
  animation: fadeInUp 0.4s ease 0.05s both;
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease;
}
.user-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(61, 90, 128, 0.12), inset 0 1px 0 rgba(255,255,255,0.7);
}
.user-avatar {
  width: 80px; height: 80px; border-radius: 50%;
  background: #ffedd5; color: #ea580c;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; border: 4px solid #fff;
  animation: subtlePulse 3s ease-in-out infinite;
}
.user-info { display: flex; flex-direction: column; gap: 4px; }
.user-name { font-size: 20px; font-weight: 800; color: #1e293b; margin: 0; }
.user-email { font-size: 13px; color: #64748b; margin: 0; font-weight: 500; }
.user-id-badge {
  margin-top: 6px; display: inline-flex; align-items: center; gap: 6px;
  background: rgba(61, 90, 128, 0.08); color: #3d5a80; padding: 4px 12px;
  border-radius: 999px; font-size: 11px; font-weight: 700; font-family: monospace;
  border: 1px solid rgba(61, 90, 128, 0.12);
}

/* ─── Stats ─────────────────────────────────────────────────── */
.stats-row { display: flex; gap: 14px; }
.stat-card {
  flex: 1; display: flex; align-items: center; gap: 14px;
  background: linear-gradient(135deg, #f6f9fd 0%, #edf2f9 100%);
  border: 1.5px solid rgba(61, 90, 128, 0.12);
  border-radius: 16px; padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(61, 90, 128, 0.04);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease;
  position: relative; overflow: hidden;
}
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
}
.stat-card:nth-child(1) { animation: fadeInUp 0.4s ease 0.05s both; }
.stat-card:nth-child(2) { animation: fadeInUp 0.4s ease 0.12s both; }
.stat-card:nth-child(3) { animation: fadeInUp 0.4s ease 0.19s both; }
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(61, 90, 128, 0.1);
}
.stat-icon-wrap {
  width: 48px; height: 48px; border-radius: 14px; display: flex;
  align-items: center; justify-content: center; font-size: 20px;
  transition: transform 0.2s ease;
}
.stat-card:hover .stat-icon-wrap { transform: scale(1.1); }
.stat-icon-wrap.blue { background: #e0f2fe; color: #0284c7; }
.stat-icon-wrap.orange { background: #ffedd5; color: #ea580c; }
.stat-icon-wrap.green { background: #dcfce7; color: #16a34a; }

.stat-val   { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #64748b; font-weight: 500; }

/* ─── Recent Activity ───────────────────────────────────────── */
.recent-card {
  background: #fff; border-radius: 20px;
  border: 1.5px solid rgba(61, 90, 128, 0.12); overflow: hidden;
  box-shadow: 0 4px 12px rgba(61, 90, 128, 0.04);
  animation: fadeInUp 0.4s ease 0.22s both;
}
.recent-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px; border-bottom: 1px solid rgba(61, 90, 128, 0.08);
  background: linear-gradient(135deg, #f6f9fd, #eef3fa);
}
.recent-header h2 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0; }

.btn-ghost {
  background: rgba(61, 90, 128, 0.08); color: #3d5a80; border: none;
  padding: 8px 16px; border-radius: 999px; font-size: 12px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-ghost:hover { background: rgba(61, 90, 128, 0.15); color: #293241; }

.loading-state, .empty-state { text-align: center; padding: 40px; color: #94a3b8; font-size: 14px; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  padding: 13px 24px; text-align: left;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; color: #64748b; border-bottom: 1px solid rgba(61, 90, 128, 0.1);
}
.data-row {
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s ease, transform 0.2s ease;
}
.data-row:last-child { border-bottom: none; }
.data-row:hover { background: rgba(61, 90, 128, 0.03); }
.data-table td { padding: 14px 24px; font-size: 13px; color: #334155; }
.bold { font-weight: 600; color: #1e293b !important; }
.muted { color: #64748b; font-size: 12px; }

.badge-id {
  background: rgba(61, 90, 128, 0.08); color: #3d5a80; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
  border: 1px solid rgba(61, 90, 128, 0.1);
}

/* ─── Modal ──────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.modal {
  background: white; border-radius: 22px; width: 680px; max-width: 95vw;
  max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.18), 0 0 0 1px rgba(61,90,128,0.08);
  animation: slideUp 0.25s ease;
}
.modal-sm { width: 400px; }
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24px 30px 20px; border-bottom: 1px solid #f1f5f9;
}
.modal-title-group { display: flex; align-items: center; gap: 14px; }
.modal-icon-wrap {
  width: 40px; height: 40px; border-radius: 12px;
  background: #e0f2fe; color: #0284c7;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
}
.modal-header h2 { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close {
  width: 32px; height: 32px; border-radius: 50%; background: #f1f5f9;
  border: none; cursor: pointer; font-size: 13px; color: #64748b;
  transition: all 0.2s;
}
.modal-close:hover { background: #e2e8f0; color: #1e293b; transform: rotate(90deg); }
.modal-body { padding: 10px 30px 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 30px 24px; border-top: 1px solid #f1f5f9;
}

.info-banner {
  display: flex; gap: 12px; background: rgba(61, 90, 128, 0.04); border: 1px solid rgba(61, 90, 128, 0.1);
  padding: 16px; border-radius: 14px; align-items: flex-start;
  color: #475569; font-size: 13px; line-height: 1.5;
}
.info-banner i { color: #3b82f6; font-size: 16px; margin-top: 2px; }
.info-banner p { margin: 0; }
.info-banner strong { color: #1e293b; font-weight: 700; }
.mt-4 { margin-top: 24px; }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; font-weight: 600; color: #64748b; }
.form-group select {
  padding: 10px 14px; border-radius: 10px;
  border: 1.5px solid #e2e8f0; font-size: 13px; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s; color: #334155;
}
.form-group select:focus { border-color: #3d5a80; box-shadow: 0 0 0 3px rgba(61, 90, 128, 0.1); }

/* Custom Role Toggle */
.role-toggle {
  display: flex;
  background: #f1f5f9;
  border-radius: 12px;
  padding: 4px;
  gap: 4px;
  margin-top: 4px;
}
.toggle-option {
  flex: 1;
  cursor: pointer;
  position: relative;
}
.toggle-option input[type="radio"] {
  display: none;
}
.toggle-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 0;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  border-radius: 8px;
  transition: all 0.3s ease;
}
.toggle-option input[type="radio"]:checked + .toggle-label {
  background: #3d5a80;
  color: white;
  box-shadow: 0 4px 12px rgba(61, 90, 128, 0.3);
}
.toggle-option input[type="radio"]:hover:not(:checked) + .toggle-label {
  color: #475569;
}

.error-text { font-size: 12px; color: #ef4444; margin: 6px 0 0 4px; font-weight: 500; }

.btn-primary {
  background: #3d5a80; color: white; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.btn-primary:hover:not(:disabled) { background: #293241; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(61, 90, 128, 0.25); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
