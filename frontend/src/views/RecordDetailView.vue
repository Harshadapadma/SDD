<template>
  <div class="page" v-if="record">
    
    <!-- HEADER -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.push('/records')">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div>
          <h1 class="page-title">Record Details</h1>
          <p class="page-sub">{{ record.public_id }} • {{ record.name }}</p>
        </div>
      </div>
      <div class="header-actions">
        <span :class="['role-badge', record.access_type?.toLowerCase()]">
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
            <i class="fas fa-user-circle"></i>
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
              <label>Source Company</label>
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
            <i class="fas fa-file-signature"></i>
            <h3>Disclosure Details</h3>
          </div>
          <div class="card-body grid-2">
            <div class="info-group">
              <label>Disclosure Name</label>
              <div class="info-val">{{ record.disclosure_name || '—' }}</div>
            </div>
            <div class="info-group">
              <label>Disclosure Designation</label>
              <div class="info-val">{{ record.disclosure_designation || '—' }}</div>
            </div>
          </div>
        </div>

        <!-- CARD: INFO DETAILS (Large Text) -->
        <div class="detail-card">
          <div class="card-header">
            <i class="fas fa-info-circle"></i>
            <h3>Detailed Information</h3>
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
            <i class="fas fa-cog"></i>
            <h3>Metadata</h3>
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

        <!-- CARD: ACCESS LIST (ADMIN ONLY) -->
        <div class="detail-card" v-if="isAdmin && record.access_list">
          <div class="card-header">
            <i class="fas fa-users-shield"></i>
            <h3>Users with Access</h3>
          </div>
          <div class="card-body no-padding">
            <table class="access-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Access</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="acc in record.access_list" :key="acc.user_id">
                  <td>
                    <div class="acc-user">{{ acc.user_name }}</div>
                    <div class="acc-id">{{ acc.user_id }}</div>
                  </td>
                  <td>
                    <span :class="['access-pill', acc.access_type.toLowerCase()]">
                      {{ acc.access_type }}
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
    <i class="fas fa-exclamation-triangle"></i>
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

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isAdmin = computed(() => user.role === 'ADMIN')

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
  display: flex; flex-direction: column; gap: 24px; 
  animation: fadeIn 0.4s ease both;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ─── Header ─────────────────────────────────────────────────── */
.page-header { 
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 12px; border-bottom: 1px solid #eee;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.back-btn {
  width: 40px; height: 40px; border-radius: 50%; border: 1px solid #ddd;
  background: white; cursor: pointer; color: #666; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.back-btn:hover { background: #f5f5f5; border-color: #999; color: #111; }

.page-title { font-size: 24px; font-weight: 800; color: #111; margin: 0; }
.page-sub { font-size: 14px; color: #777; margin: 4px 0 0; font-family: monospace; }

.role-badge {
  padding: 6px 14px; border-radius: 999px; font-size: 12px; font-weight: 700;
  background: #f1f5f9; color: #475569;
}
.role-badge.edit { background: #dcfce7; color: #15803d; }

/* ─── Layout Grid ───────────────────────────────────────────── */
.details-grid {
  display: grid; grid-template-columns: 1fr 340px; gap: 24px;
}

@media (max-width: 1000px) {
  .details-grid { grid-template-columns: 1fr; }
}

.details-main, .details-side { display: flex; flex-direction: column; gap: 24px; }

/* ─── Card Styles ───────────────────────────────────────────── */
.detail-card {
  background: white; border-radius: 20px; border: 1px solid #e5e7eb;
  overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.03);
}
.card-header {
  padding: 16px 20px; background: #f9fafb; border-bottom: 1px solid #eee;
  display: flex; align-items: center; gap: 12px;
}
.card-header i { color: #3d5a80; font-size: 18px; }
.card-header h3 { font-size: 15px; font-weight: 700; color: #333; margin: 0; }

.card-body { padding: 20px; }
.card-body.no-padding { padding: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px 30px; }

/* ─── Info Groups ───────────────────────────────────────────── */
.info-group { display: flex; flex-direction: column; gap: 4px; }
.info-group label { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
.info-val { font-size: 14px; font-weight: 600; color: #1e293b; }
.info-val.mono { font-family: monospace; color: #334155; }

.info-text-box {
  background: #f8fafc; border-radius: 12px; padding: 16px;
  font-size: 14px; line-height: 1.6; color: #334155; border: 1px solid #f1f5f9;
  min-height: 100px; white-space: pre-wrap;
}

/* ─── Sidebar Meta ──────────────────────────────────────────── */
.meta-item {
  display: flex; justify-content: space-between; padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}
.meta-item:last-child { border-bottom: none; }
.meta-item label { font-size: 12px; color: #64748b; font-weight: 500; }
.meta-item span { font-size: 12px; color: #1e293b; font-weight: 600; text-align: right; }

/* ─── Access Table ──────────────────────────────────────────── */
.access-table { width: 100%; border-collapse: collapse; }
.access-table th {
  padding: 10px 20px; text-align: left; font-size: 10px; font-weight: 700;
  color: #94a3b8; text-transform: uppercase; border-bottom: 1px solid #eee;
}
.access-table td { padding: 12px 20px; border-bottom: 1px solid #f8fafc; }
.acc-user { font-size: 13px; font-weight: 700; color: #1e293b; }
.acc-id { font-size: 10px; color: #94a3b8; font-family: monospace; }

.access-pill {
  padding: 3px 10px; border-radius: 999px; font-size: 10px; font-weight: 800;
}
.access-pill.view { background: #e0f2fe; color: #0369a1; }
.access-pill.edit { background: #dcfce7; color: #15803d; }

/* ─── Loading / Error ────────────────────────────────────────── */
.loading-full, .error-full {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 20px; text-align: center;
}
.loading-full i { font-size: 40px; color: #3d5a80; margin-bottom: 20px; }
.loading-full p { color: #64748b; font-weight: 500; }

.error-full i { font-size: 48px; color: #ef4444; margin-bottom: 20px; }
.error-full h2 { font-size: 24px; font-weight: 800; margin-bottom: 8px; }
.error-full p { color: #64748b; margin-bottom: 24px; }

.btn-primary {
  background: #3d5a80; color: white; border: none; padding: 12px 24px;
  border-radius: 999px; font-weight: 600; cursor: pointer; transition: 0.2s;
}
.btn-primary:hover { background: #293241; transform: translateY(-1px); }
</style>
