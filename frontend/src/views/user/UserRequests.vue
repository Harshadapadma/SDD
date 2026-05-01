<template>
  <div class="page">
    
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">My Requests</h1>
        <p class="page-sub">Track the status of your system and record requests</p>
      </div>
    </div>

    <!-- TABS -->
    <div class="tabs">
      <button 
        v-for="t in tabs" 
        :key="t.id" 
        :class="['tab-btn', { active: activeTab === t.id }]"
        @click="activeTab = t.id"
      >
        <i :class="['fas', t.icon]"></i>
        {{ t.label }}
        <span class="tab-count">{{ getCount(t.id) }}</span>
      </button>
    </div>

    <!-- CONTENT -->
    <div class="table-card">
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading requests...
      </div>
      
      <div v-else>
        <table class="data-table" v-if="currentRequests.length > 0">
          <thead>
            <tr>
              <th>ID</th>
              <th v-if="activeTab !== 'role'">Target</th>
              <th v-if="activeTab === 'role'">Requested Role</th>
              <th v-if="activeTab === 'access'">Access Type</th>
              <th>Status</th>
              <th>Requested On</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in currentRequests" :key="req.id" class="data-row">
              <td><span class="badge-id">#{{ req.id }}</span></td>
              
              <!-- TARGET (Record) -->
              <td v-if="activeTab !== 'role'" class="bold">
                {{ req.record_id }}
              </td>

              <!-- ROLE -->
              <td v-if="activeTab === 'role'">
                <span class="role-pill">{{ req.requested_role }}</span>
              </td>

              <!-- ACCESS TYPE -->
              <td v-if="activeTab === 'access'">
                <span class="access-pill">{{ req.requested_access }}</span>
              </td>

              <!-- STATUS -->
              <td>
                <span :class="['status-pill', req.status.toLowerCase()]">
                  {{ req.status }}
                </span>
              </td>

              <!-- DATE -->
              <td class="muted">{{ formatDate(req.created_at) }}</td>
            </tr>
          </tbody>
        </table>
        
        <div v-else class="empty-state">
          <i class="fas fa-inbox"></i>
          <p>No {{ activeTab }} requests found.</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../../api/client'

const loading = ref(true)
const activeTab = ref('access')
const data = ref<any>({
  delete_requests: [],
  role_requests: [],
  access_requests: []
})

const tabs = [
  { id: 'access', label: 'Access Upgrades', icon: 'fa-key' },
  { id: 'role', label: 'Role Changes', icon: 'fa-user-tag' },
  { id: 'delete', label: 'Deletions', icon: 'fa-trash-alt' },
]

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

const currentRequests = computed(() => {
  if (activeTab.value === 'access') return data.value.access_requests
  if (activeTab.value === 'role') return data.value.role_requests
  if (activeTab.value === 'delete') return data.value.delete_requests
  return []
})

function getCount(id: string) {
  if (id === 'access') return data.value.access_requests.length
  if (id === 'role') return data.value.role_requests.length
  if (id === 'delete') return data.value.delete_requests.length
  return 0
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchRequests)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; animation: fadeIn 0.4s ease both; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 24px; font-weight: 800; color: #1e293b; margin: 0; }
.page-sub { font-size: 14px; color: #64748b; margin-top: 4px; }

/* ─── Tabs ──────────────────────────────────────────────────── */
.tabs { display: flex; gap: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
.tab-btn {
  background: none; border: none; padding: 10px 16px; font-size: 14px;
  font-weight: 600; color: #64748b; cursor: pointer; display: flex;
  align-items: center; gap: 8px; position: relative; transition: all 0.2s;
}
.tab-btn:hover { color: #1e293b; }
.tab-btn.active { color: #3d5a80; }
.tab-btn.active::after {
  content: ''; position: absolute; bottom: -5px; left: 0; right: 0;
  height: 3px; background: #3d5a80; border-radius: 999px;
}

.tab-count {
  background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 999px;
  font-size: 11px; font-weight: 700;
}
.tab-btn.active .tab-count { background: #3d5a80; color: white; }

/* ─── Table Card ────────────────────────────────────────────── */
.table-card {
  background: white; border-radius: 20px; border: 1px solid #e2e8f0;
  overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.02);
}

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  padding: 14px 24px; text-align: left; font-size: 11px; font-weight: 700;
  text-transform: uppercase; color: #64748b; border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}
.data-table td { padding: 16px 24px; font-size: 14px; color: #1e293b; border-bottom: 1px solid #f1f5f9; }
.data-row:hover { background: #f8fafc; }

.bold { font-weight: 700; }
.muted { font-size: 12px; color: #94a3b8; }

.badge-id { font-family: monospace; color: #94a3b8; font-weight: 700; }

/* ─── Status Pills ───────────────────────────────────────────── */
.status-pill {
  padding: 4px 12px; border-radius: 999px; font-size: 11px; font-weight: 700;
}
.status-pill.pending { background: #fef3c7; color: #b45309; }
.status-pill.approved { background: #dcfce7; color: #15803d; }
.status-pill.rejected { background: #fee2e2; color: #b91c1c; }

.role-pill, .access-pill {
  background: #f1f5f9; color: #334155; padding: 3px 10px; border-radius: 6px;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
}

/* ─── Loading / Empty ────────────────────────────────────────── */
.loading-state, .empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 20px; color: #94a3b8; gap: 16px;
}
.empty-state i { font-size: 40px; color: #e2e8f0; }
.loading-state i { font-size: 32px; color: #3d5a80; }
</style>
