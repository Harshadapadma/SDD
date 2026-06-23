<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Records</h1>
        <p class="page-sub">View and manage vault records</p>
      </div>
      <button v-if="isCollaborator" class="btn-primary" @click="showCreate = true">
        <i class="fas fa-plus"></i> New Record
      </button>
    </div>

    <!-- STATS ROW -->
    <div class="stats-row">
      <div class="stat-card">
        <i class="fas fa-database stat-icon blue"></i>
        <div>
          <div class="stat-val">{{ total }}</div>
          <div class="stat-label">Accessible Records</div>
        </div>
      </div>
      <div class="stat-card">
        <i class="fas fa-calendar-day stat-icon orange"></i>
        <div>
          <div class="stat-val">{{ todayCount }}</div>
          <div class="stat-label">Added Today</div>
        </div>
      </div>
    </div>

    <!-- SEARCH BAR -->
    <div class="toolbar">
      <div class="search-wrap">
        <i class="fas fa-search search-icon"></i>
        <input
          v-model="search"
          @input="fetchRecords"
          class="search-input"
          placeholder="Search by name, PAN, record ID…"
        />
      </div>
    </div>

    <!-- TILE GRID -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading records…
    </div>

    <div v-else-if="records.length === 0" class="empty-state">
      <i class="fas fa-inbox"></i>
      <p>No records found.</p>
    </div>

    <div v-else class="tile-grid">
      <div v-for="record in records" :key="record.public_id" class="record-tile">
        <div class="tile-header">
          <div class="tile-icon"><i class="fas fa-file-alt"></i></div>
          <div class="tile-name">{{ record.name }}</div>
        </div>
        <div class="tile-details">
          <div class="tile-row">
            <i class="fas fa-id-card"></i>
            <span class="tile-pan">{{ record.pan }}</span>
          </div>
          <div class="tile-row">
            <i class="fas fa-building"></i>
            <span>{{ record.source_company || '—' }}</span>
          </div>
        </div>
        <div class="tile-footer">
          <div class="tile-meta">
            <span class="tile-badge">{{ record.public_id }}</span>
            <span class="tile-date">{{ formatDate(record.info_received_date) }}</span>
          </div>
          <div class="tile-creator">
            <i class="fas fa-user-circle"></i> {{ record.created_by }}
          </div>
        </div>
        <div class="tile-actions">
          <button class="icon-action view" title="View Details" @click="$router.push(`/records/${record.public_id}`)">
            <i class="fas fa-eye"></i>
          </button>
          <template v-if="isCollaborator">
            <button v-if="record.access_type === 'EDIT'" class="icon-action edit" title="Edit" @click="openEdit(record)">
              <i class="fas fa-pen"></i>
            </button>
            <button v-if="record.access_type === 'VIEW'" class="icon-action upgrade" title="Request Edit Access" @click="requestEdit(record)">
              <i class="fas fa-lock"></i>
            </button>
            <button v-if="record.access_type === 'EDIT'" class="icon-action delete" title="Request Delete" @click="deleteRecord(record)">
              <i class="fas fa-trash"></i>
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- PAGINATION -->
    <div class="pagination" v-if="totalPages > 1">
      <button class="page-btn" :disabled="page === 1" @click="changePage(page - 1)">
        <i class="fas fa-chevron-left"></i>
      </button>
      <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
      <button class="page-btn" :disabled="page === totalPages" @click="changePage(page + 1)">
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <!-- ─── CREATE RECORD MODAL ──────────────────────────────── -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showCreate" @click.self="showCreate = false">
        <div class="modal">
          <div class="modal-header">
            <h2>New Record</h2>
            <button class="modal-close" @click="showCreate = false"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="form.name" />
              </div>
              <div class="form-group">
                <label>Designation</label>
                <input v-model="form.designation" />
              </div>
              <div class="form-group">
                <label>Employee Code</label>
                <input v-model="form.employee_code" />
              </div>
              <div class="form-group">
                <label>PAN</label>
                <input v-model="form.pan" />
              </div>
              <div class="form-group">
                <label>Source Company</label>
                <input v-model="form.source_company" />
              </div>
              <div class="form-group">
                <label>Date Received</label>
                <input type="date" v-model="form.info_received_date" />
              </div>
              <div class="form-group">
                <label>Disclosure Name</label>
                <input v-model="form.disclosure_name" />
              </div>
              <div class="form-group">
                <label>Disclosure Designation</label>
                <input v-model="form.disclosure_designation" />
              </div>
              <div class="form-group full-width">
                <label>Information Details</label>
                <textarea v-model="form.info_details" rows="3"></textarea>
              </div>
            </div>
            <p class="error-msg" v-if="createError">{{ createError }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showCreate = false">Cancel</button>
            <button class="btn-primary" @click="createRecord" :disabled="creating">
              <i class="fas fa-spinner fa-spin" v-if="creating"></i>
              {{ creating ? 'Creating…' : 'Create Record' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- ─── EDIT RECORD MODAL ────────────────────────────────── -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showEdit" @click.self="showEdit = false">
        <div class="modal">
          <div class="modal-header">
            <h2>Edit — {{ editRecord?.public_id }}</h2>
            <button class="modal-close" @click="showEdit = false"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div v-if="editing && !editForm.name" class="loading-state">
              <i class="fas fa-spinner fa-spin"></i> Loading record details…
            </div>
            <div class="form-grid" v-else>
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="editForm.name" />
              </div>
              <div class="form-group">
                <label>Designation</label>
                <input v-model="editForm.designation" />
              </div>
              <div class="form-group">
                <label>Employee Code</label>
                <input v-model="editForm.employee_code" />
              </div>
              <div class="form-group">
                <label>PAN</label>
                <input v-model="editForm.pan" />
              </div>
              <div class="form-group">
                <label>Source Company</label>
                <input v-model="editForm.source_company" />
              </div>
              <div class="form-group">
                <label>Date Received</label>
                <input type="date" v-model="editForm.info_received_date" />
              </div>
              <div class="form-group">
                <label>Disclosure Name</label>
                <input v-model="editForm.disclosure_name" />
              </div>
              <div class="form-group">
                <label>Disclosure Designation</label>
                <input v-model="editForm.disclosure_designation" />
              </div>
              <div class="form-group full-width">
                <label>Information Details</label>
                <textarea v-model="editForm.info_details" rows="3"></textarea>
              </div>
            </div>
            <p class="error-msg" v-if="editError">{{ editError }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showEdit = false">Cancel</button>
            <button class="btn-primary" @click="saveEdit" :disabled="editing">
              {{ editing ? 'Saving…' : 'Save Changes' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- ─── CONFIRM MODAL ────────────────────────────────────── -->
    <teleport to="body">
      <div class="modal-overlay" v-if="confirmDialog.show" @click.self="closeConfirm">
        <div class="modal confirm-modal">
          <div class="modal-header">
            <h2>{{ confirmDialog.title }}</h2>
            <button class="modal-close" @click="closeConfirm"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <p>{{ confirmDialog.message }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="closeConfirm">Cancel</button>
            <button class="btn-primary confirm-btn" @click="confirmAction">
              Confirm
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

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isCollaborator = computed(() => user?.role === 'COLLABORATOR')
const { notify } = useNotifications()

const records = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const search = ref('')
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const todayCount = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return records.value.filter(r => r.created_at?.startsWith(today)).length
})

async function fetchRecords() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (search.value) params.search = search.value
    const res = await api.get('records/', { params })
    records.value = res.data.results
    total.value = res.data.count
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  fetchRecords()
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Create ────────────────────────────────────────────────────
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const form = ref({
  name: '', designation: '', employee_code: '', pan: '',
  source_company: '', info_details: '', info_received_date: '',
  disclosure_name: '', disclosure_designation: ''
})

async function createRecord() {
  creating.value = true
  createError.value = ''
  try {
    await api.post('records/create/', form.value)
    showCreate.value = false
    Object.keys(form.value).forEach(k => (form.value as any)[k] = '')
    fetchRecords()
  } catch (e: any) {
    createError.value = JSON.stringify(e?.response?.data || 'Error creating record')
  } finally {
    creating.value = false
  }
}

// ─── Edit ──────────────────────────────────────────────────────
const showEdit = ref(false)
const editing = ref(false)
const editError = ref('')
const editRecord = ref<any>(null)
const editForm = ref<any>({})

async function openEdit(record: any) {
  editRecord.value = record
  editForm.value = {}
  showEdit.value = true
  editing.value = true  // show loading state while fetching
  try {
    const res = await api.get(`records/${record.public_id}/`)
    editForm.value = { ...res.data }
  } catch (e) {
    notify('Error', 'Failed to load record details.', 'ERROR')
    showEdit.value = false
  } finally {
    editing.value = false
  }
}

async function saveEdit() {
  editing.value = true
  editError.value = ''
  try {
    await api.put(`records/${editRecord.value.public_id}/update/`, editForm.value)
    showEdit.value = false
    fetchRecords()
  } catch (e: any) {
    editError.value = e?.response?.data?.error || 'Failed to update record'
  } finally {
    editing.value = false
  }
}

// ─── Confirm Modal Logic ──────────────────────────────────────
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: null as (() => void) | null
})

function openConfirm(title: string, message: string, action: () => void) {
  confirmDialog.value = {
    show: true,
    title,
    message,
    onConfirm: action
  }
}

function closeConfirm() {
  confirmDialog.value.show = false
  confirmDialog.value.onConfirm = null
}

function confirmAction() {
  if (confirmDialog.value.onConfirm) {
    confirmDialog.value.onConfirm()
  }
  closeConfirm()
}

function deleteRecord(record: any) {
  openConfirm(
    "Confirm Deletion Request",
    `Are you sure you want to request deletion of record ${record.public_id}?`,
    async () => {
      try {
        await api.delete(`records/${record.public_id}/delete/`)
        notify("Delete Request", "Delete request sent to admin for approval.", "SUCCESS")
      } catch (e: any) {
        console.error(e)
        const errObj = e?.response?.data || {}
        const errMsg = errObj.error || errObj.detail || "Failed to submit delete request."
        notify("Delete Failed", errMsg, "ERROR")
      }
    }
  )
}

function requestEdit(record: any) {
  openConfirm(
    "Request Edit Access",
    `Do you want to request EDIT access for record ${record.public_id}?`,
    async () => {
      try {
        await api.post(`workflows/access-upgrade/request/${record.public_id}/`)
        notify("Access Request", "Access upgrade request sent to admin for approval.", "SUCCESS")
      } catch (e: any) {
        console.error(e)
        notify("Request Failed", e?.response?.data?.error || "Failed to submit access request.", "ERROR")
      }
    }
  )
}

onMounted(fetchRecords)
</script>

<style scoped>
/* ─── Page shell ─────────────────────────────────────────────── */
.page { display: flex; flex-direction: column; gap: 20px; animation: fadeInUp 0.4s ease both; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ─── Header ─────────────────────────────────────────────────── */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title  { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0; }
.page-sub    { font-size: 13px; color: #64748b; margin: 4px 0 0; }

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
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(61, 90, 128, 0.1);
}
.stat-icon { font-size: 22px; transition: transform 0.2s ease; }
.stat-card:hover .stat-icon { transform: scale(1.15); }
.stat-icon.blue { color: #3b82f6; }
.stat-icon.orange { color: #f59e0b; }
.stat-val   { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #64748b; }

/* ─── Toolbar ────────────────────────────────────────────────── */
.toolbar { display: flex; gap: 12px; }
.search-wrap { position: relative; flex: 1; max-width: 420px; }
.search-icon {
  position: absolute; left: 18px; top: 50%; transform: translateY(-50%);
  color: #3d5a80; font-size: 15px; z-index: 1;
}
.search-input {
  width: 100%; padding: 13px 16px 13px 48px; border-radius: 999px;
  border: 1.5px solid rgba(61, 90, 128, 0.15); 
  background: rgba(255, 255, 255, 0.7); 
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  font-size: 14px; font-weight: 500; color: #1e293b; outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  box-sizing: border-box;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
}
.search-input::placeholder { color: #94a3b8; font-weight: 400; }
.search-input:hover { background: rgba(255, 255, 255, 0.9); border-color: rgba(61, 90, 128, 0.3); }
.search-input:focus { 
  border-color: #3d5a80; background: #fff; 
  box-shadow: 0 8px 20px rgba(61, 90, 128, 0.12), 0 0 0 4px rgba(61, 90, 128, 0.08);
  transform: translateY(-1px);
}

/* ─── Buttons ────────────────────────────────────────────────── */
.btn-primary {
  background: #3d5a80; color: white; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.btn-primary:hover { background: #293241; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(61, 90, 128, 0.25); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-ghost {
  background: rgba(61, 90, 128, 0.08); color: #3d5a80; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-ghost:hover { background: rgba(61, 90, 128, 0.15); color: #293241; }

/* ─── Tile Grid ──────────────────────────────────────────────── */
.tile-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px; animation: fadeInUp 0.4s ease 0.1s both;
}

.record-tile {
  background: white; border-radius: 18px; padding: 0;
  border: 1.5px solid rgba(61, 90, 128, 0.1);
  box-shadow: 0 2px 10px rgba(61, 90, 128, 0.04);
  display: flex; flex-direction: column;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1), box-shadow 0.25s ease;
  overflow: hidden; animation: fadeInUp 0.3s ease both;
}
.record-tile:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(61, 90, 128, 0.1);
}

.tile-header {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 20px 14px;
  background: linear-gradient(135deg, #f6f9fd, #edf2f9);
  border-bottom: 1px solid rgba(61, 90, 128, 0.06);
}
.tile-icon {
  width: 40px; height: 40px; border-radius: 12px;
  background: rgba(61, 90, 128, 0.1); color: #3d5a80;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; flex-shrink: 0;
}
.tile-name {
  font-size: 15px; font-weight: 700; color: #1e293b;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.tile-details { padding: 14px 20px; display: flex; flex-direction: column; gap: 8px; }
.tile-row {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: #475569;
}
.tile-row i { color: #94a3b8; font-size: 12px; width: 14px; text-align: center; }
.tile-pan { font-family: monospace; font-weight: 600; color: #334155; }

.tile-footer {
  padding: 12px 20px; border-top: 1px solid #f1f5f9;
  display: flex; flex-direction: column; gap: 6px;
}
.tile-meta { display: flex; justify-content: space-between; align-items: center; }
.tile-badge {
  background: rgba(61, 90, 128, 0.08); color: #3d5a80; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
  border: 1px solid rgba(61, 90, 128, 0.1);
}
.tile-date { font-size: 11px; color: #94a3b8; font-weight: 500; }
.tile-creator {
  font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 6px;
}

.tile-actions {
  display: flex; gap: 6px; padding: 12px 20px; border-top: 1px solid #f1f5f9;
}

.loading-state {
  display: flex; align-items: center; justify-content: center;
  padding: 60px 20px; color: #3d5a80; gap: 12px; font-size: 15px;
}
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 20px; color: #94a3b8; gap: 16px;
}
.empty-state i { font-size: 40px; opacity: 0.4; }

/* ─── Action buttons ─────────────────────────────────────────── */
.icon-action {
  width: 30px; height: 30px; border-radius: 8px; border: none;
  cursor: pointer; font-size: 12px; display: flex; align-items: center;
  justify-content: center; transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
.icon-action:hover { transform: scale(1.12); }
.icon-action.view { background: rgba(61, 90, 128, 0.08); color: #3d5a80; }
.icon-action.view:hover { background: #3d5a80; color: white; box-shadow: 0 4px 10px rgba(61, 90, 128, 0.2); }
.icon-action.edit { background: rgba(61, 90, 128, 0.08); color: #3d5a80; }
.icon-action.edit:hover { background: #3d5a80; color: white; box-shadow: 0 4px 10px rgba(61, 90, 128, 0.2); }
.icon-action.upgrade { background: #fef3e2; color: #d97706; }
.icon-action.upgrade:hover { background: #d97706; color: white; box-shadow: 0 4px 10px rgba(217, 119, 6, 0.2); }
.icon-action.delete { background: #fee2e2; color: #dc2626; }
.icon-action.delete:hover { background: #dc2626; color: white; box-shadow: 0 4px 10px rgba(220, 38, 38, 0.2); }

/* ─── Pagination ─────────────────────────────────────────────── */
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 14px; }
.page-btn {
  width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid rgba(61, 90, 128, 0.15);
  background: white; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; color: #475569;
}
.page-btn:hover:not(:disabled) { border-color: #3d5a80; color: #3d5a80; background: rgba(61, 90, 128, 0.04); }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-size: 13px; color: #64748b; }

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
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.confirm-modal { width: 420px; }
.confirm-modal .modal-body { padding: 30px 26px; text-align: center; color: #475569; font-size: 14px; }
.confirm-btn { background: #3d5a80; }
.confirm-btn:hover { background: #293241; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 22px 26px 18px; border-bottom: 1px solid #f1f5f9;
}
.modal-header h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close {
  width: 32px; height: 32px; border-radius: 50%; background: #f1f5f9;
  border: none; cursor: pointer; font-size: 13px; color: #64748b;
  transition: all 0.2s;
}
.modal-close:hover { background: #e2e8f0; color: #1e293b; transform: rotate(90deg); }
.modal-body { padding: 20px 26px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 26px 22px; border-top: 1px solid #f1f5f9;
}

/* ─── Form ───────────────────────────────────────────────────── */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-size: 12px; font-weight: 600; color: #64748b; }
.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 14px; border-radius: 10px;
  border: 1.5px solid #e2e8f0; font-size: 13px; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s; resize: vertical; color: #334155;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus { border-color: #3d5a80; box-shadow: 0 0 0 3px rgba(61, 90, 128, 0.08); }

.error-msg { color: #dc2626; font-size: 12px; margin-top: 8px; }
</style>