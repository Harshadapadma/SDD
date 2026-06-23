<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">My Requests</h1>
        <p class="page-sub">Track the status of your system and record requests</p>
      </div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading requests...
    </div>

    <!-- KANBAN BOARD -->
    <div v-else class="kanban-board">

      <!-- PENDING COLUMN -->
      <div class="kanban-col">
        <div class="col-header pending">
          <div class="col-title">
            <i class="fas fa-clock"></i>
            <span>Pending</span>
          </div>
          <span class="col-count">{{ pendingRequests.length }}</span>
        </div>
        <div class="col-body">
          <div v-if="pendingRequests.length === 0" class="col-empty">
            <i class="fas fa-check-circle"></i>
            <span>No pending requests</span>
          </div>
          <div v-for="req in pendingRequests" :key="req._key" class="kanban-card">
            <div class="card-top">
              <span :class="['type-chip', req._type]">{{ req._typeLabel }}</span>
              <span class="card-id">#{{ req.id }}</span>
            </div>
            <div class="card-target" v-if="req._type !== 'role'">
              <i class="fas fa-file-alt"></i> Record {{ req.record_id }}
            </div>
            <div class="card-target" v-else>
              <i class="fas fa-user-tag"></i> {{ req.requested_role }}
            </div>
            <div class="card-target" v-if="req._type === 'access'">
              <i class="fas fa-key"></i> {{ req.requested_access }}
            </div>
            <div class="card-date">
              <i class="fas fa-calendar-alt"></i> {{ formatDate(req.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- APPROVED COLUMN -->
      <div class="kanban-col">
        <div class="col-header approved">
          <div class="col-title">
            <i class="fas fa-check-circle"></i>
            <span>Approved</span>
          </div>
          <span class="col-count">{{ approvedRequests.length }}</span>
        </div>
        <div class="col-body">
          <div v-if="approvedRequests.length === 0" class="col-empty">
            <i class="fas fa-inbox"></i>
            <span>No approved requests</span>
          </div>
          <div v-for="req in approvedRequests" :key="req._key" class="kanban-card approved">
            <div class="card-top">
              <span :class="['type-chip', req._type]">{{ req._typeLabel }}</span>
              <span class="card-id">#{{ req.id }}</span>
            </div>
            <div class="card-target" v-if="req._type !== 'role'">
              <i class="fas fa-file-alt"></i> Record {{ req.record_id }}
            </div>
            <div class="card-target" v-else>
              <i class="fas fa-user-tag"></i> {{ req.requested_role }}
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
          <div class="col-title">
            <i class="fas fa-times-circle"></i>
            <span>Rejected</span>
          </div>
          <span class="col-count">{{ rejectedRequests.length }}</span>
        </div>
        <div class="col-body">
          <div v-if="rejectedRequests.length === 0" class="col-empty">
            <i class="fas fa-inbox"></i>
            <span>No rejected requests</span>
          </div>
          <div v-for="req in rejectedRequests" :key="req._key" class="kanban-card rejected">
            <div class="card-top">
              <span :class="['type-chip', req._type]">{{ req._typeLabel }}</span>
              <span class="card-id">#{{ req.id }}</span>
            </div>
            <div class="card-target" v-if="req._type !== 'role'">
              <i class="fas fa-file-alt"></i> Record {{ req.record_id }}
            </div>
            <div class="card-target" v-else>
              <i class="fas fa-user-tag"></i> {{ req.requested_role }}
            </div>
            <div class="card-date">
              <i class="fas fa-calendar-alt"></i> {{ formatDate(req.created_at) }}
            </div>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../../api/client'

const loading = ref(true)
const data = ref<any>({
  delete_requests: [],
  role_requests: [],
  access_requests: []
})

async function fetchRequests() {
  loading.value = true
  try {
    const res = await api.get('workflows/my-requests/')
    data.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const allRequests = computed(() => {
  const del = (data.value.delete_requests || []).map((r: any) => ({ ...r, _type: 'delete', _typeLabel: 'Deletion', _key: 'del-' + r.id }))
  const role = (data.value.role_requests || []).map((r: any) => ({ ...r, _type: 'role', _typeLabel: 'Role Change', _key: 'role-' + r.id }))
  const acc = (data.value.access_requests || []).map((r: any) => ({ ...r, _type: 'access', _typeLabel: 'Access', _key: 'acc-' + r.id }))
  return [...del, ...role, ...acc].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const pendingRequests = computed(() => allRequests.value.filter(r => r.status === 'PENDING'))
const approvedRequests = computed(() => allRequests.value.filter(r => r.status === 'APPROVED'))
const rejectedRequests = computed(() => allRequests.value.filter(r => r.status === 'REJECTED'))

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchRequests)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; animation: fadeIn 0.4s ease both; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 24px; font-weight: 800; color: #1e293b; margin: 0; }
.page-sub { font-size: 14px; color: #64748b; margin-top: 4px; }

/* ─── Loading ────────────────────────────────────────────────── */
.loading-state {
  display: flex; align-items: center; justify-content: center;
  padding: 80px 20px; color: #3d5a80; gap: 12px; font-size: 15px;
}

/* ─── Kanban Board ───────────────────────────────────────────── */
.kanban-board {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
  min-height: 400px; animation: fadeInUp 0.4s ease 0.1s both;
}

.kanban-col {
  background: rgba(61, 90, 128, 0.03); border-radius: 20px;
  border: 1px solid rgba(61, 90, 128, 0.08);
  display: flex; flex-direction: column; min-height: 300px;
  overflow: hidden;
}

/* Column Headers */
.col-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid rgba(61, 90, 128, 0.08);
}
.col-header.pending { background: linear-gradient(135deg, #fffbeb, #fef3c7); }
.col-header.approved { background: linear-gradient(135deg, #f0fdf4, #dcfce7); }
.col-header.rejected { background: linear-gradient(135deg, #fef2f2, #fee2e2); }

.col-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 14px; font-weight: 700;
}
.col-header.pending .col-title { color: #92400e; }
.col-header.approved .col-title { color: #166534; }
.col-header.rejected .col-title { color: #991b1b; }

.col-count {
  background: rgba(0,0,0,0.08); padding: 2px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 800;
}
.col-header.pending .col-count { background: rgba(180, 83, 9, 0.15); color: #92400e; }
.col-header.approved .col-count { background: rgba(22, 101, 52, 0.15); color: #166534; }
.col-header.rejected .col-count { background: rgba(153, 27, 27, 0.15); color: #991b1b; }

/* Column Body */
.col-body {
  padding: 16px; display: flex; flex-direction: column; gap: 12px;
  flex: 1; overflow-y: auto;
}

.col-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1; color: #94a3b8; gap: 10px; font-size: 13px; font-weight: 500;
  min-height: 150px;
}
.col-empty i { font-size: 28px; opacity: 0.4; }

/* ─── Kanban Cards ───────────────────────────────────────────── */
.kanban-card {
  background: white; border-radius: 14px; padding: 16px;
  border: 1px solid rgba(61, 90, 128, 0.1);
  box-shadow: 0 2px 8px rgba(61, 90, 128, 0.04);
  display: flex; flex-direction: column; gap: 10px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  animation: fadeInUp 0.3s ease both;
}
.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(61, 90, 128, 0.08);
}
.kanban-card.approved { border-left: 3px solid #22c55e; }
.kanban-card.rejected { border-left: 3px solid #ef4444; }

.card-top {
  display: flex; justify-content: space-between; align-items: center;
}
.card-id {
  font-family: monospace; font-size: 12px; font-weight: 700; color: #94a3b8;
}

.type-chip {
  padding: 3px 10px; border-radius: 6px; font-size: 10px;
  font-weight: 800; text-transform: uppercase; letter-spacing: 0.3px;
}
.type-chip.delete { background: #fee2e2; color: #b91c1c; }
.type-chip.role { background: #dbeafe; color: #1d4ed8; }
.type-chip.access { background: #fef3c7; color: #92400e; }

.card-target {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: #334155;
}
.card-target i { color: #94a3b8; font-size: 12px; width: 14px; }

.card-date {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; color: #94a3b8; font-weight: 500;
  padding-top: 6px; border-top: 1px solid #f1f5f9;
}
.card-date i { font-size: 11px; }

@media (max-width: 900px) {
  .kanban-board { grid-template-columns: 1fr; }
}
</style>
