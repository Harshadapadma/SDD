<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Workflow Requests</h1>
        <p class="page-sub">Review and approve role and deletion requests</p>
      </div>
      <div class="header-badges">
        <span class="count-badge pending">{{ pendingRequests.length }} Pending</span>
      </div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading requests…</div>

    <!-- KANBAN BOARD -->
    <div v-else class="kanban-board">

      <!-- PENDING COLUMN -->
      <div class="kanban-col">
        <div class="col-header pending">
          <div class="col-title"><i class="fas fa-clock"></i><span>Pending</span></div>
          <span class="col-count">{{ pendingRequests.length }}</span>
        </div>
        <div class="col-body">
          <div v-if="pendingRequests.length === 0" class="col-empty">
            <i class="fas fa-check-circle"></i><span>All caught up!</span>
          </div>
          <div v-for="req in pendingRequests" :key="req.type + req.id" class="kanban-card">
            <div class="card-top">
              <span :class="['type-chip', req.type.toLowerCase()]">
                {{ req.type === 'DELETE' ? 'Deletion' : (req.type === 'ACCESS' ? 'Access' : 'Role') }}
              </span>
              <span class="card-id">#{{ req.id }}</span>
            </div>
            <div class="card-target">
              <i :class="['fas', req.type === 'ROLE' ? 'fa-user-tag' : 'fa-file-alt']"></i>
              {{ req.type === 'ROLE' ? 'To ' + req.requested_role : 'Record ' + req.record_id }}
            </div>
            <div class="card-user">
              <i class="fas fa-user"></i>
              {{ (req.type === 'DELETE' || req.type === 'ACCESS') ? (req.user_name || req.requested_by) : req.user_name }}
            </div>
            <div class="card-date">
              <i class="fas fa-calendar-alt"></i> {{ formatDate(req.created_at) }}
            </div>
            <div class="card-actions">
              <button class="action-pill approve" @click="review(req, 'APPROVE')" :disabled="reviewing === req.type + req.id">
                <i class="fas fa-check"></i> Approve
              </button>
              <button class="action-pill reject" @click="review(req, 'REJECT')" :disabled="reviewing === req.type + req.id">
                <i class="fas fa-times"></i> Reject
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- APPROVED COLUMN -->
      <div class="kanban-col">
        <div class="col-header approved">
          <div class="col-title"><i class="fas fa-check-circle"></i><span>Approved</span></div>
          <span class="col-count">{{ approvedRequests.length }}</span>
        </div>
        <div class="col-body">
          <div v-if="approvedRequests.length === 0" class="col-empty">
            <i class="fas fa-inbox"></i><span>No approved requests</span>
          </div>
          <div v-for="req in approvedRequests" :key="req.type + req.id" class="kanban-card approved">
            <div class="card-top">
              <span :class="['type-chip', req.type.toLowerCase()]">
                {{ req.type === 'DELETE' ? 'Deletion' : (req.type === 'ACCESS' ? 'Access' : 'Role') }}
              </span>
              <span class="card-id">#{{ req.id }}</span>
            </div>
            <div class="card-target">
              <i :class="['fas', req.type === 'ROLE' ? 'fa-user-tag' : 'fa-file-alt']"></i>
              {{ req.type === 'ROLE' ? 'To ' + req.requested_role : 'Record ' + req.record_id }}
            </div>
            <div class="card-user">
              <i class="fas fa-user"></i>
              {{ (req.type === 'DELETE' || req.type === 'ACCESS') ? (req.user_name || req.requested_by) : req.user_name }}
            </div>
            <div class="card-date">
              <i class="fas fa-calendar-alt"></i> {{ formatDate(req.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- REJECTED COLUMN -->
      <div class="kanban-col">
        <div class="col-header rejected">
          <div class="col-title"><i class="fas fa-times-circle"></i><span>Rejected</span></div>
          <span class="col-count">{{ rejectedRequests.length }}</span>
        </div>
        <div class="col-body">
          <div v-if="rejectedRequests.length === 0" class="col-empty">
            <i class="fas fa-inbox"></i><span>No rejected requests</span>
          </div>
          <div v-for="req in rejectedRequests" :key="req.type + req.id" class="kanban-card rejected">
            <div class="card-top">
              <span :class="['type-chip', req.type.toLowerCase()]">
                {{ req.type === 'DELETE' ? 'Deletion' : (req.type === 'ACCESS' ? 'Access' : 'Role') }}
              </span>
              <span class="card-id">#{{ req.id }}</span>
            </div>
            <div class="card-target">
              <i :class="['fas', req.type === 'ROLE' ? 'fa-user-tag' : 'fa-file-alt']"></i>
              {{ req.type === 'ROLE' ? 'To ' + req.requested_role : 'Record ' + req.record_id }}
            </div>
            <div class="card-user">
              <i class="fas fa-user"></i>
              {{ (req.type === 'DELETE' || req.type === 'ACCESS') ? (req.user_name || req.requested_by) : req.user_name }}
            </div>
            <div class="card-date">
              <i class="fas fa-calendar-alt"></i> {{ formatDate(req.created_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CONFIRM MODAL -->
    <teleport to="body">
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
            :class="confirmModal.action === 'APPROVE' ? 'btn-primary' : 'btn-danger'"
            @click="doReview"
            :disabled="reviewing !== null"
          >
            {{ reviewing !== null ? 'Processing…' : confirmModal.action === 'APPROVE' ? (confirmModal.req.type === 'DELETE' ? 'Yes, Delete' : 'Approve') : 'Reject' }}
          </button>
        </div>
      </div>
    </div>
    </teleport>

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

const pendingRequests = computed(() => requests.value.filter(r => r.status === 'PENDING'))
const approvedRequests = computed(() => requests.value.filter(r => r.status === 'APPROVED'))
const rejectedRequests = computed(() => requests.value.filter(r => r.status === 'REJECTED'))

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

.count-badge { padding: 5px 14px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.count-badge.pending { background: #fef3cd; color: #b45309; }

.loading-state { text-align: center; padding: 60px; color: #5a8a6a; font-size: 15px; }

/* ─── Kanban Board ───────────────────────────────────────────── */
.kanban-board {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
  min-height: 400px; animation: fadeInUp 0.4s ease 0.1s both;
}

.kanban-col {
  background: rgba(47, 125, 101, 0.03); border-radius: 20px;
  border: 1px solid rgba(47, 125, 101, 0.08);
  display: flex; flex-direction: column; min-height: 300px;
  overflow: hidden;
}

.col-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid rgba(47, 125, 101, 0.08);
}
.col-header.pending { background: linear-gradient(135deg, #fffbeb, #fef3c7); }
.col-header.approved { background: linear-gradient(135deg, #f0fdf4, #dcfce7); }
.col-header.rejected { background: linear-gradient(135deg, #fef2f2, #fee2e2); }

.col-title { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 700; }
.col-header.pending .col-title { color: #92400e; }
.col-header.approved .col-title { color: #166534; }
.col-header.rejected .col-title { color: #991b1b; }

.col-count { padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.col-header.pending .col-count { background: rgba(180, 83, 9, 0.15); color: #92400e; }
.col-header.approved .col-count { background: rgba(22, 101, 52, 0.15); color: #166534; }
.col-header.rejected .col-count { background: rgba(153, 27, 27, 0.15); color: #991b1b; }

.col-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; flex: 1; overflow-y: auto; }

.col-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1; color: #94a3b8; gap: 10px; font-size: 13px; font-weight: 500; min-height: 150px;
}
.col-empty i { font-size: 28px; opacity: 0.4; }

/* ─── Kanban Cards ───────────────────────────────────────────── */
.kanban-card {
  background: white; border-radius: 14px; padding: 16px;
  border: 1px solid rgba(47, 125, 101, 0.1);
  box-shadow: 0 2px 8px rgba(47, 125, 101, 0.04);
  display: flex; flex-direction: column; gap: 10px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  animation: fadeInUp 0.3s ease both;
}
.kanban-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(47, 125, 101, 0.08); }
.kanban-card.approved { border-left: 3px solid #22c55e; }
.kanban-card.rejected { border-left: 3px solid #ef4444; }

.card-top { display: flex; justify-content: space-between; align-items: center; }
.card-id { font-family: monospace; font-size: 12px; font-weight: 700; color: #94a3b8; }

.type-chip { padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; text-transform: uppercase; }
.type-chip.delete { background: #fee2e2; color: #b91c1c; }
.type-chip.role { background: #dbeafe; color: #1d4ed8; }
.type-chip.access { background: #fef3c7; color: #92400e; }

.card-target, .card-user {
  display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #334155;
}
.card-target i, .card-user i { color: #94a3b8; font-size: 12px; width: 14px; }

.card-date {
  display: flex; align-items: center; gap: 8px; font-size: 11px; color: #94a3b8; font-weight: 500;
  padding-top: 6px; border-top: 1px solid #f1f5f9;
}

.card-actions {
  display: flex; gap: 8px; padding-top: 8px; border-top: 1px solid #f1f5f9;
}
.action-pill {
  flex: 1; padding: 7px 0; border-radius: 8px; border: none;
  font-size: 12px; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: all 0.2s;
}
.action-pill:disabled { opacity: 0.5; cursor: not-allowed; }
.action-pill.approve { background: #dcfce7; color: #15803d; }
.action-pill.approve:hover:not(:disabled) { background: #16a34a; color: white; }
.action-pill.reject  { background: #fee2e2; color: #b91c1c; }
.action-pill.reject:hover:not(:disabled) { background: #dc2626; color: white; }

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
  box-shadow: 0 20px 60px rgba(0,0,0,0.18), 0 0 0 1px rgba(47,125,101,0.08);
  animation: slideUp 0.25s ease;
}
.modal-sm { width: 420px; }
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 22px 26px 18px; border-bottom: 1px solid #f1f5f9;
}
.modal-header h2 { font-size: 17px; font-weight: 700; color: #1a2e1a; margin: 0; }
.modal-close {
  width: 32px; height: 32px; border-radius: 50%; background: #f1f5f9;
  border: none; cursor: pointer; font-size: 13px; color: #64748b; transition: all 0.2s;
}
.modal-close:hover { background: #e2e8f0; color: #1e293b; transform: rotate(90deg); }
.modal-body { padding: 22px 26px; }
.confirm-text { font-size: 14px; color: #444; line-height: 1.6; margin: 0; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 26px 22px; border-top: 1px solid #f1f5f9;
}

.btn-primary {
  background: #2f7d65; color: white; border: none;
  padding: 10px 22px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.btn-primary:hover { background: #256554; box-shadow: 0 4px 14px rgba(47, 125, 101, 0.25); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-danger {
  background: #dc2626; color: white; border: none;
  padding: 10px 22px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-danger:hover { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost {
  background: rgba(47, 125, 101, 0.06); color: #2f7d65; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-ghost:hover { background: rgba(47, 125, 101, 0.12); color: #1a5c3a; }

@media (max-width: 900px) {
  .kanban-board { grid-template-columns: 1fr; }
}
</style>
