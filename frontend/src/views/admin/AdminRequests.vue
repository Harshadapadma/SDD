<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Workflow Requests</h1>
        <p class="page-sub">Review and approve role and deletion requests</p>
      </div>
      <div class="header-badges">
        <span class="count-badge pending">{{ pendingCount }} Pending</span>
      </div>
    </div>

    <!-- FILTER TABS -->
    <div class="tab-bar">
      <button
        v-for="t in tabs" :key="t.val"
        :class="['tab-btn', { active: activeTab === t.val }]"
        @click="activeTab = t.val"
      >
        {{ t.label }}
        <span class="tab-count" v-if="countFor(t.val) > 0">{{ countFor(t.val) }}</span>
      </button>
    </div>

    <!-- TABLE -->
    <div class="table-card">
      <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading requests…</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Request ID</th>
            <th>Target / Record</th>
            <th>Requested By</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filtered.length === 0">
            <td colspan="6" class="empty-row">No requests in this category.</td>
          </tr>
          <tr v-for="req in filtered" :key="req.type + req.id" class="data-row">
            <td>
              <span :class="['type-badge', req.type.toLowerCase()]">
                {{ req.type === 'DELETE' ? 'Deletion' : (req.type === 'ACCESS' ? 'Access Upgrade' : 'Role Change') }}
              </span>
            </td>
            <td><span class="badge-id">#{{ req.id }}</span></td>
            <td>
              <span class="badge-id green" v-if="req.type === 'DELETE' || req.type === 'ACCESS'">{{ req.record_id }}</span>
              <span class="bold" v-else>To {{ req.requested_role }}</span>
            </td>
            <td class="bold">
              {{ (req.type === 'DELETE' || req.type === 'ACCESS') ? (req.user_name || req.requested_by) : (req.user_name + ' (' + req.user_id + ')') }}
            </td>
            <td>
              <span :class="['status-badge', req.status.toLowerCase()]">
                {{ req.status }}
              </span>
            </td>
            <td class="muted">{{ formatDate(req.created_at) }}</td>
            <td>
              <div class="action-btns" v-if="req.status === 'PENDING'">
                <button class="action-pill approve" @click="review(req, 'APPROVE')" :disabled="reviewing === req.type + req.id">
                  <i class="fas fa-check"></i> Approve
                </button>
                <button class="action-pill reject" @click="review(req, 'REJECT')" :disabled="reviewing === req.type + req.id">
                  <i class="fas fa-times"></i> Reject
                </button>
              </div>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- CONFIRM MODAL -->
    <div class="modal-overlay" v-if="confirmModal" @click.self="confirmModal = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>{{ confirmModal.action === 'APPROVE' ? '✅ Approve Request' : '❌ Reject Request' }}</h2>
          <button class="modal-close" @click="confirmModal = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <p class="confirm-text">
            <span v-if="confirmModal.action === 'APPROVE' && confirmModal.req.type === 'DELETE'">
              This will <strong>permanently delete</strong> the record. This action cannot be undone.
            </span>
            <span v-else-if="confirmModal.action === 'APPROVE' && confirmModal.req.type === 'ROLE'">
              This will upgrade the user's permissions to <strong>{{ confirmModal.req.requested_role }}</strong>.
            </span>
            <span v-else-if="confirmModal.action === 'APPROVE' && confirmModal.req.type === 'ACCESS'">
              This will grant the user <strong>EDIT</strong> access to record <strong>{{ confirmModal.req.record_id }}</strong>.
            </span>
            <span v-else>
              The request will be rejected and the user will be notified.
            </span>
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="confirmModal = null">Cancel</button>
          <button
            :class="confirmModal.action === 'APPROVE' ? 'btn-danger' : 'btn-primary'"
            @click="doReview"
            :disabled="reviewing !== null"
          >
            {{ reviewing !== null ? 'Processing…' : confirmModal.action === 'APPROVE' ? (confirmModal.req.type === 'DELETE' ? 'Yes, Delete' : 'Approve') : 'Reject' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const { notify } = useNotifications()
const requests = ref<any[]>([])
const loading  = ref(false)
const reviewing = ref<string | null>(null)
const activeTab = ref('ALL')

const tabs = [
  { val: 'ALL', label: 'All' },
  { val: 'PENDING', label: 'Pending' },
  { val: 'APPROVED', label: 'Approved' },
  { val: 'REJECTED', label: 'Rejected' },
]

const filtered = computed(() =>
  activeTab.value === 'ALL'
    ? requests.value
    : requests.value.filter(r => r.status === activeTab.value)
)

const pendingCount = computed(() => requests.value.filter(r => r.status === 'PENDING').length)

function countFor(tab: string) {
  if (tab === 'ALL') return 0
  return requests.value.filter(r => r.status === tab).length
}

async function fetchRequests() {
  loading.value = true
  try {
    const [delRes, roleRes, accRes] = await Promise.all([
      api.get('workflows/'),
      api.get('workflows/role-change/'),
      api.get('workflows/access-upgrade/')
    ])
    
    const delReqs = delRes.data.map((r: any) => ({ ...r, type: 'DELETE' }))
    const roleReqs = roleRes.data.map((r: any) => ({ ...r, type: 'ROLE' }))
    const accReqs = accRes.data.map((r: any) => ({ ...r, type: 'ACCESS' }))
    
    requests.value = [...delReqs, ...roleReqs, ...accReqs].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Review ────────────────────────────────────────────────────
const confirmModal = ref<{ req: any, action: string } | null>(null)

function review(req: any, action: string) {
  confirmModal.value = { req, action }
}

async function doReview() {
  if (!confirmModal.value) return
  const req = confirmModal.value.req
  const action = confirmModal.value.action
  reviewing.value = req.type + req.id
  
  const endpoint = req.type === 'DELETE' 
    ? `workflows/review/${req.id}/` 
    : (req.type === 'ROLE' ? `workflows/role-change/review/${req.id}/` : `workflows/access-upgrade/review/${req.id}/`)

  try {
    await api.post(endpoint, { action })
    notify(
      action === 'APPROVE' ? 'Request Approved' : 'Request Rejected',
      `Workflow request #${req.id} has been ${action.toLowerCase()}d.`,
      action === 'APPROVE' ? 'SUCCESS' : 'INFO'
    )
    confirmModal.value = null
    fetchRequests()
  } catch (e) {
    console.error(e)
    notify('Review Failed', 'Failed to process request.', 'ERROR')
  } finally {
    reviewing.value = null
  }
}


onMounted(fetchRequests)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 20px; animation: fadeInUp 0.4s ease both; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title  { font-size: 22px; font-weight: 700; color: #1a2e1a; margin: 0; }
.page-sub    { font-size: 13px; color: #7a9a7a; margin: 4px 0 0; }

.count-badge {
  padding: 5px 14px; border-radius: 999px; font-size: 12px; font-weight: 700;
}
.count-badge.pending { background: #fef3cd; color: #b45309; }

/* ─── Tabs ───────────────────────────────────────────────────── */
.tab-bar { display: flex; gap: 8px; }
.tab-btn {
  padding: 8px 18px; border-radius: 999px; border: 1.5px solid #e0e0e0;
  background: white; font-size: 13px; font-weight: 500; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.2s; color: #555;
}
.tab-btn.active { background: #2f7d65; color: white; border-color: #2f7d65; }
.tab-btn:hover:not(.active) { border-color: #2f7d65; color: #2f7d65; }
.tab-count {
  background: rgba(255,255,255,0.25); border-radius: 999px;
  padding: 1px 7px; font-size: 11px;
}
.tab-btn:not(.active) .tab-count { background: #f0f0f0; color: #555; }

/* ─── Table ─────────────────────────────────────────────────── */
.table-card {
  background: #fff; border-radius: 20px;
  border: 1.5px solid #e8f0ea; overflow: hidden;
  animation: fadeInUp 0.4s ease 0.1s both;
}
.loading-state { text-align: center; padding: 40px; color: #999; font-size: 14px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table thead tr { background: #f5fbf7; }
.data-table th {
  padding: 13px 16px; text-align: left; font-size: 11px;
  font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  color: #5a8a6a; border-bottom: 1.5px solid #e0f0e8;
}
.data-row { border-bottom: 1px solid #f0f5f1; transition: background 0.15s; }
.data-row:hover { background: #f9fdfb; }
.data-table td { padding: 13px 16px; font-size: 13px; color: #2a3a2a; }
.empty-row { text-align: center; color: #aaa; padding: 40px; }
.bold  { font-weight: 600; }
.muted { color: #888; font-size: 12px; }

.badge-id {
  background: #edf7f2; color: #2f7d65; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
}
.badge-id.green { background: #edf7f2; color: #256554; }

.status-badge {
  padding: 4px 12px; border-radius: 999px; font-size: 11px; font-weight: 700;
}
.status-badge.pending  { background: #fef3cd; color: #b45309; }
.status-badge.approved { background: #dcfce7; color: #15803d; }
.status-badge.rejected { background: #fee2e2; color: #b91c1c; }

.type-badge {
  padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 800; text-transform: uppercase;
}
.type-badge.delete { background: #fee2e2; color: #b91c1c; }
.type-badge.role { background: #dbeafe; color: #1d4ed8; }
.type-badge.access { background: #fef3e2; color: #d97706; }

/* ─── Action pills ───────────────────────────────────────────── */
.action-btns { display: flex; gap: 6px; }
.action-pill {
  padding: 5px 12px; border-radius: 999px; border: none;
  font-size: 12px; font-weight: 600; cursor: pointer;
  display: inline-flex; align-items: center; gap: 5px;
  transition: all 0.2s;
}
.action-pill:disabled { opacity: 0.5; cursor: not-allowed; }
.action-pill.approve { background: #dcfce7; color: #15803d; }
.action-pill.approve:hover:not(:disabled) { background: #16a34a; color: white; }
.action-pill.reject  { background: #fee2e2; color: #b91c1c; }
.action-pill.reject:hover:not(:disabled)  { background: #dc2626; color: white; }

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
  box-shadow: 0 20px 60px rgba(0,0,0,0.2); animation: slideUp 0.25s ease;
}
.modal-sm { width: 420px; }
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 22px 26px 18px; border-bottom: 1px solid #eee;
}
.modal-header h2 { font-size: 17px; font-weight: 700; color: #1a2e1a; margin: 0; }
.modal-close {
  width: 32px; height: 32px; border-radius: 50%; background: #f3f3f3;
  border: none; cursor: pointer; font-size: 13px; color: #666; transition: background 0.2s;
}
.modal-close:hover { background: #ddd; }
.modal-body { padding: 22px 26px; }
.confirm-text { font-size: 14px; color: #444; line-height: 1.6; margin: 0; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 26px 22px; border-top: 1px solid #eee;
}

.btn-primary {
  background: #2f7d65; color: white; border: none;
  padding: 10px 22px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-primary:hover { background: #256554; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-danger {
  background: #dc2626; color: white; border: none;
  padding: 10px 22px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-danger:hover { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost {
  background: #f3f3f3; color: #444; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-ghost:hover { background: #e8e8e8; }
</style>
