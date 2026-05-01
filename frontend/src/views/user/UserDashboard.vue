<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Welcome back, {{ userName }}!</h1>
        <p class="page-sub">Here is a quick overview of your vault</p>
      </div>
      <button class="btn-primary" @click="showRoleModal = true">
        <i class="fas fa-user-shield"></i> Request Role Change
      </button>
    </div>

    <!-- USER PROFILE CARD -->
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
            <h2>Request Role Change</h2>
            <button class="modal-close" @click="showRoleModal = false"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <p class="subtext">Select the role you wish to request. This will be sent to the administrator for approval.</p>
            <div class="form-group mt-3">
              <label>Desired Role</label>
              <select v-model="requestedRole">
                <option value="VIEWER">Viewer</option>
                <option value="COLLABORATOR">Collaborator</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showRoleModal = false">Cancel</button>
            <button class="btn-primary" @click="submitRoleRequest" :disabled="requestingRole">
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

const { unreadCount, notify } = useNotifications()

const stats = ref({
  totalRecords: 0,
  recentAdded: 0,
  unreadNotifs: unreadCount,
})

const recentRecords = ref<any[]>([])
const loading = ref(true)

const showRoleModal = ref(false)
const requestedRole = ref('COLLABORATOR')
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

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title  { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0; }
.page-sub    { font-size: 13px; color: #64748b; margin: 4px 0 0; }

/* ─── User Card ─────────────────────────────────────────────── */
.user-card {
  display: flex; align-items: center; gap: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1.5px solid #e2e8f0; border-radius: 24px; padding: 24px 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  max-width: 450px;
  animation: fadeInUp 0.4s ease 0.05s both;
}
.user-avatar {
  width: 80px; height: 80px; border-radius: 50%;
  background: #ffedd5; color: #ea580c;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; border: 4px solid #fff;
  box-shadow: 0 4px 10px rgba(234, 88, 12, 0.15);
}
.user-info { display: flex; flex-direction: column; gap: 4px; }
.user-name { font-size: 20px; font-weight: 800; color: #1e293b; margin: 0; }
.user-email { font-size: 13px; color: #64748b; margin: 0; font-weight: 500; }
.user-id-badge {
  margin-top: 6px; display: inline-flex; align-items: center; gap: 6px;
  background: #f1f5f9; color: #3d5a80; padding: 4px 12px;
  border-radius: 999px; font-size: 11px; font-weight: 700; font-family: monospace;
}

/* ─── Stats ─────────────────────────────────────────────────── */
.stats-row { display: flex; gap: 14px; }
.stat-card {
  flex: 1; display: flex; align-items: center; gap: 14px;
  background: #ffffff; border: 1.5px solid #e2e8f0;
  border-radius: 16px; padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  animation: fadeInUp 0.4s ease 0.05s both;
}
.stat-icon-wrap {
  width: 48px; height: 48px; border-radius: 14px; display: flex;
  align-items: center; justify-content: center; font-size: 20px;
}
.stat-icon-wrap.blue { background: #e0f2fe; color: #0284c7; }
.stat-icon-wrap.orange { background: #ffedd5; color: #ea580c; }
.stat-icon-wrap.green { background: #dcfce7; color: #16a34a; }

.stat-val   { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #64748b; font-weight: 500; }

/* ─── Recent Activity ───────────────────────────────────────── */
.recent-card {
  background: #fff; border-radius: 20px;
  border: 1.5px solid #e2e8f0; overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  animation: fadeInUp 0.4s ease 0.1s both;
}
.recent-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px; border-bottom: 1px solid #f1f5f9; background: #f8fafc;
}
.recent-header h2 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0; }

.btn-ghost {
  background: #f1f5f9; color: #475569; border: none;
  padding: 8px 16px; border-radius: 999px; font-size: 12px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-ghost:hover { background: #e2e8f0; color: #1e293b; }

.loading-state, .empty-state { text-align: center; padding: 40px; color: #94a3b8; font-size: 14px; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  padding: 13px 24px; text-align: left;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; color: #64748b; border-bottom: 1px solid #e2e8f0;
}
.data-row { border-bottom: 1px solid #f1f5f9; transition: background 0.15s; }
.data-row:last-child { border-bottom: none; }
.data-row:hover { background: #f8fafc; }
.data-table td { padding: 14px 24px; font-size: 13px; color: #334155; }
.bold { font-weight: 600; color: #1e293b !important; }
.muted { color: #64748b; font-size: 12px; }

.badge-id {
  background: #f1f5f9; color: #3d5a80; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
}

/* ─── Modal ──────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.modal {
  background: white; border-radius: 22px; width: 680px; max-width: 95vw;
  max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  animation: slideUp 0.25s ease;
}
.modal-sm { width: 400px; }
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 22px 26px 18px; border-bottom: 1px solid #f1f5f9;
}
.modal-header h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close {
  width: 32px; height: 32px; border-radius: 50%; background: #f1f5f9;
  border: none; cursor: pointer; font-size: 13px; color: #64748b;
  transition: background 0.2s;
}
.modal-close:hover { background: #e2e8f0; color: #1e293b; }
.modal-body { padding: 20px 26px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 26px 22px; border-top: 1px solid #f1f5f9;
}

.subtext { font-size: 13px; color: #64748b; margin: 0 0 16px; line-height: 1.5; }
.mt-3 { margin-top: 12px; }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; font-weight: 600; color: #64748b; }
.form-group select {
  padding: 10px 14px; border-radius: 10px;
  border: 1.5px solid #e2e8f0; font-size: 13px; outline: none;
  transition: border-color 0.2s; color: #334155;
}
.form-group select:focus { border-color: #3d5a80; }

.btn-primary {
  background: #3d5a80; color: white; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: background 0.2s, transform 0.15s;
}
.btn-primary:hover:not(:disabled) { background: #293241; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
