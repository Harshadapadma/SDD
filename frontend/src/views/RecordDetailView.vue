<template>
  <div class="page" v-if="record">
    
    <!-- HEADER -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.push('/records')" title="Back to Records">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div>
          <h1 class="page-title">Record Details</h1>
          <p class="page-sub"><span class="id-code">{{ record.public_id }}</span> • {{ record.name }}</p>
        </div>
      </div>
      <div class="header-actions">
        <span :class="['role-badge', record.access_type === 'EDIT' ? 'edit-access' : 'view-access']">
          <i :class="['fas', record.access_type === 'EDIT' ? 'fa-pen-to-square' : 'fa-eye']"></i>
          {{ record.access_type === 'EDIT' ? 'Full Access' : 'View Only' }}
        </span>
      </div>
    </div>

    <div class="details-grid">
      
      <!-- LEFT: MAIN INFO -->
      <div class="details-main">
        
        <!-- CARD: SUBJECT INFO -->
        <div class="detail-card">
          <div class="card-header">
            <div class="header-icon"><i class="fas fa-user-circle"></i></div>
            <h3>Subject Information</h3>
          </div>
          <div class="card-body grid-2">
            <div class="info-group">
              <label>Full Name</label>
              <div class="info-val">{{ record.name }}</div>
            </div>
            <div class="info-group">
              <label>Designation</label>
              <div class="info-val">{{ record.designation || '—' }}</div>
            </div>
            <div class="info-group">
              <label>PAN Number</label>
              <div class="info-val mono">{{ record.pan }}</div>
            </div>
            <div class="info-group">
              <label>Employee Code</label>
              <div class="info-val mono">{{ record.employee_code || '—' }}</div>
            </div>
            <div class="info-group">
              <label>Disclosure Company</label>
              <div class="info-val">{{ record.source_company }}</div>
            </div>
            <div class="info-group">
              <label>Date Received</label>
              <div class="info-val">{{ formatDate(record.info_received_date) }}</div>
            </div>
          </div>
        </div>

        <!-- CARD: DISCLOSURE INFO -->
        <div class="detail-card">
          <div class="card-header">
            <div class="header-icon"><i class="fas fa-file-signature"></i></div>
            <h3>Disclosure Officer Details</h3>
          </div>
          <div class="card-body grid-2">
            <div class="info-group">
              <label>Disclosure Officer Name</label>
              <div class="info-val">{{ record.disclosure_name || '—' }}</div>
            </div>
            <div class="info-group">
              <label>Disclosure Officer Designation</label>
              <div class="info-val">{{ record.disclosure_designation || '—' }}</div>
            </div>
            <div class="info-group">
              <label>Disclosure Officer Department</label>
              <div class="info-val">{{ record.disclosure_department || '—' }}</div>
            </div>
          </div>
        </div>

        <!-- CARD: INFO DETAILS (Large Text) -->
        <div class="detail-card">
          <div class="card-header">
            <div class="header-icon"><i class="fas fa-circle-info"></i></div>
            <h3>Detailed Disclosure Information</h3>
          </div>
          <div class="card-body">
            <div class="info-text-box">
              {{ record.info_details || 'No additional details provided.' }}
            </div>
          </div>
        </div>

      </div>

      <!-- RIGHT: METADATA & ACCESS (ADMIN ONLY) -->
      <div class="details-side">
        
        <!-- CARD: SYSTEM METADATA -->
        <div class="detail-card compact">
          <div class="card-header">
            <div class="header-icon"><i class="fas fa-sliders"></i></div>
            <h3>System Metadata</h3>
          </div>
          <div class="card-body">
            <div class="meta-item">
              <label>Created By</label>
              <span>{{ record.created_by_name }}</span>
            </div>
            <div class="meta-item">
              <label>Created At</label>
              <span>{{ formatDateTime(record.created_at) }}</span>
            </div>
            <div class="meta-item" v-if="record.updated_by_name">
              <label>Last Updated By</label>
              <span>{{ record.updated_by_name }}</span>
            </div>
            <div class="meta-item" v-if="record.updated_at">
              <label>Last Updated</label>
              <span>{{ formatDateTime(record.updated_at) }}</span>
            </div>
          </div>
        </div>

        <!-- CARD: ACCESS LIST (TOGGLEABLE FOR COMPLIANCE OFFICER / ADMIN) -->
        <div class="detail-card" v-if="canManageAccess && record.access_list && record.access_list.length > 0">
          <div class="card-header clickable-header" @click="showAccessList = !showAccessList">
            <div class="header-left-title">
              <div class="header-icon"><i class="fas fa-user-shield"></i></div>
              <h3>Users with Access ({{ record.access_list.length }})</h3>
            </div>
            <button class="btn-toggle-expand" type="button" aria-label="Toggle Users with Access">
              <span>{{ showAccessList ? 'Hide Access List' : 'View Access List' }}</span>
              <i :class="['fas', showAccessList ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
            </button>
          </div>
          <div class="card-body no-padding" v-if="showAccessList">
            <table class="access-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Permission</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="acc in record.access_list" :key="acc.user_id">
                  <td>
                    <div class="acc-user">{{ acc.user_name }}</div>
                    <div class="acc-id">{{ acc.user_id }}</div>
                  </td>
                  <td>
                    <span class="user-role-chip">{{ acc.user_role || 'COLLABORATOR' }}</span>
                  </td>
                  <td>
                    <span :class="['access-pill', (acc.access_type || 'VIEW').toLowerCase()]">
                      {{ acc.access_type === 'EDIT' ? 'Full Edit' : 'View Only' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>

  </div>

  <!-- LOADING STATE -->
  <div class="loading-full" v-else-if="loading">
    <i class="fas fa-spinner fa-spin"></i>
    <p>Fetching secure record data...</p>
  </div>

  <!-- ERROR STATE -->
  <div class="error-full" v-else>
    <i class="fas fa-triangle-exclamation"></i>
    <h2>Access Denied</h2>
    <p>{{ error || 'You do not have permission to view this record.' }}</p>
    <button class="btn-primary" @click="$router.push('/records')">Back to Records</button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/client'

const route = useRoute()
const record = ref<any>(null)
const loading = ref(true)
const error = ref('')
const showAccessList = ref(false)

const user = JSON.parse(localStorage.getItem('user') || '{}')
const canManageAccess = computed(() => ['ADMIN', 'COMPLIANCE_OFFICER'].includes(user.role?.toUpperCase()))

async function fetchRecord() {
  loading.value = true
  try {
    const res = await api.get(`records/${route.params.id}/`)
    record.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Failed to load record.'
  } finally {
    loading.value = false
  }
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatDateTime(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleString('en-GB', { 
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

onMounted(fetchRecord)
</script>

<style scoped>
.page { 
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.page-header { 
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left { display: flex; align-items: center; gap: 16px; }

.back-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--duration-base) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
}
.back-btn:hover {
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
  transform: translateY(-1px);
}
.back-btn:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
}

.page-title { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); margin: 0; }
.page-sub { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 2px; }
.id-code { font-family: monospace; font-weight: var(--weight-bold); color: var(--orange-accent); }

.role-badge {
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.role-badge.edit-access {
  background: var(--success-bg);
  color: var(--success-700);
  border: 1px solid var(--success-border);
}
.role-badge.view-access {
  background: var(--info-bg);
  color: var(--info-700);
  border: 1px solid var(--info-border);
}

/* Grid Layout */
.details-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
}

.details-main, .details-side { display: flex; flex-direction: column; gap: 20px; }

/* Cards (Neorphism) */
.detail-card {
  background: var(--bg-base);
  border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card);
  overflow: hidden;
  transition: transform var(--duration-base) var(--ease-out);
}
.detail-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--neu-card-hover);
}

.card-header {
  padding: 16px 20px;
  background: var(--bg-base);
  border-bottom: 1px solid var(--card-divider);
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--orange-bg-subtle);
  color: var(--orange-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
}
.card-header h3 { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }

.card-body { padding: 20px; }
.card-body.no-padding { padding: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 24px; }

.info-group { display: flex; flex-direction: column; gap: 4px; }
.info-group label { font-size: 11px; font-weight: var(--weight-bold); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.info-val { font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--text-primary); }
.info-val.mono { font-family: monospace; color: var(--orange-accent); font-weight: var(--weight-bold); }

.info-text-box {
  background: var(--bg-input);
  border-radius: var(--radius-md);
  padding: 16px;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-primary);
  box-shadow: var(--neu-inset);
  min-height: 110px;
  white-space: pre-wrap;
}

/* Sidebar Metadata */
.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--card-divider);
}
.meta-item:last-child { border-bottom: none; }
.meta-item label { font-size: var(--text-xs); color: var(--neutral-700); font-weight: var(--weight-bold); }
.meta-item span { font-size: var(--text-xs); color: var(--text-primary); font-weight: var(--weight-bold); }

/* Access Table */
.access-table { width: 100%; border-collapse: collapse; }
.access-table th {
  padding: 10px 20px;
  text-align: left;
  font-size: 11px;
  font-weight: var(--weight-bold);
  color: var(--neutral-700);
  text-transform: uppercase;
  border-bottom: 1px solid var(--card-divider);
  background: var(--bg-content);
}
.card-header.clickable-header {
  cursor: pointer;
  user-select: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background var(--duration-fast);
}
.card-header.clickable-header:hover {
  background: var(--bg-content);
}
.header-left-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.btn-toggle-expand {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-app);
  border: 1px solid rgba(166, 169, 173, 0.4);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  transition: all var(--duration-fast);
  cursor: pointer;
}
.clickable-header:hover .btn-toggle-expand {
  background: var(--orange-bg-subtle);
  color: var(--orange-accent);
  border-color: var(--orange-border);
}

.access-table td { padding: 12px 20px; border-bottom: 1px solid var(--card-divider); }
.acc-user { font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-primary); }
.acc-id { font-size: 10px; color: var(--neutral-700); font-weight: var(--weight-medium); font-family: monospace; }

.user-role-chip {
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 9.5px;
  font-weight: 800;
  text-transform: uppercase;
  background: rgba(35, 28, 20, 0.07);
  color: var(--neutral-800);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.access-pill {
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: var(--weight-bold);
}
.access-pill.edit { background: var(--success-bg); color: var(--success-700); border: 1px solid var(--success-border); }
.access-pill.view { background: var(--info-bg); color: var(--info-700); border: 1px solid var(--info-border); }

/* Loading & Error States */
.loading-full, .error-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}
.loading-full i { font-size: 36px; color: var(--orange-accent); margin-bottom: 16px; }
.loading-full p { color: var(--text-secondary); font-weight: var(--weight-medium); }

.error-full i { font-size: 48px; color: var(--error-500); margin-bottom: 16px; }
.error-full h2 { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); margin-bottom: 8px; color: var(--text-primary); }
.error-full p { color: var(--text-secondary); margin-bottom: 20px; }

.btn-primary {
  background: var(--orange-gradient); color: white; border: none; padding: 10px 20px;
  border-radius: var(--radius-pill); font-weight: var(--weight-bold); font-size: var(--text-xs);
  cursor: pointer; transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--sku-btn-primary-shadow);
}
.btn-primary:hover {
  box-shadow: var(--sku-btn-primary-shadow-hover);
  transform: translateY(-1px);
}

@media (max-width: 900px) {
  .details-grid { grid-template-columns: 1fr; }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
