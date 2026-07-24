<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Records Vault</h1>
        <p class="page-sub">Access and manage confidential disclosure records</p>
      </div>
      <button v-if="isCollaborator" class="btn-primary" @click="showCreate = true">
        <i class="fas fa-plus"></i> New Record
      </button>
    </div>

    <!-- STATS ROW (Neomorphism) -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon-wrap blue">
          <i class="fas fa-database"></i>
        </div>
        <div>
          <div class="stat-val">{{ total }}</div>
          <div class="stat-label">Accessible Records</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap orange">
          <i class="fas fa-calendar-day"></i>
        </div>
        <div>
          <div class="stat-val">{{ todayCount }}</div>
          <div class="stat-label">Added Today</div>
        </div>
      </div>
    </div>

    <!-- SEARCH TOOLBAR & STATUS FILTER TOGGLE -->
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

      <div class="filter-toggle-group" v-if="isCollaborator">
        <button
          type="button"
          class="filter-toggle-btn"
          :class="{ active: statusFilter === 'APPROVED' }"
          @click="setStatusFilter('APPROVED')"
        >
          <i class="fas fa-circle-check"></i>
          <span>Confirmed Records</span>
        </button>
        <button
          type="button"
          class="filter-toggle-btn"
          :class="{ active: statusFilter === 'PENDING' }"
          @click="setStatusFilter('PENDING')"
        >
          <i class="fas fa-clock"></i>
          <span>Pending Approval</span>
          <span class="badge-count" v-if="pendingCount > 0">{{ pendingCount }}</span>
        </button>
      </div>
    </div>

    <!-- TILE GRID -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading records…
    </div>

    <div v-else-if="records.length === 0" class="empty-state">
      <i class="fas fa-inbox"></i>
      <p v-if="statusFilter === 'PENDING'">No pending record creation requests.</p>
      <p v-else>No confirmed records found.</p>
    </div>

    <div v-else class="tile-grid">
      <div v-for="record in records" :key="record.public_id" class="record-tile">
        <div class="tile-header">
          <div class="tile-icon"><i class="fas fa-file-alt"></i></div>
          <div class="tile-name-wrap">
            <div class="tile-name">
              {{ record.name }}
              <span v-if="record.status === 'PENDING_CREATION'" class="tile-pending-tag"><i class="fas fa-clock"></i> Pending Confirmation</span>
            </div>
            <div class="tile-subname" v-if="record.designation">{{ record.designation }}</div>
          </div>
        </div>
        <div class="tile-details">
          <div class="tile-row">
            <i class="fas fa-id-card"></i>
            <span class="tile-label">PAN:</span>
            <span class="tile-pan">{{ record.pan }}</span>
          </div>
          <div class="tile-row">
            <i class="fas fa-building"></i>
            <span class="tile-label">Company:</span>
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
            <button v-if="record.access_type === 'EDIT'" class="icon-action edit" title="Edit Record" @click="openEdit(record)">
              <i class="fas fa-pen"></i>
            </button>
            <button v-if="record.access_type === 'VIEW'" class="icon-action upgrade" title="Request Edit Access" @click="requestEdit(record)">
              <i class="fas fa-lock"></i>
            </button>
            <button v-if="record.access_type === 'EDIT'" class="icon-action delete" title="Request Deletion" @click="deleteRecord(record)">
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

    <!-- ─── CREATE RECORD MODAL (Glassmorphism) ──────────────── -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showCreate" @click.self="showCreate = false">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-file-circle-plus"></i></div>
              <h2>Create Disclosure Record</h2>
            </div>
            <button class="modal-close" @click="showCreate = false" aria-label="Close"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group">
                <label>Full Name *</label>
                <input v-model="form.name" maxlength="255" @input="form.name = form.name.replace(/[^a-zA-Z\s\.\-']/g, '')" />
              </div>
              <div class="form-group">
                <label>Designation *</label>
                <input v-model="form.designation" maxlength="255" />
              </div>
              <div class="form-group">
                <label>Employee Code *</label>
                <input v-model="form.employee_code" maxlength="50" @input="form.employee_code = form.employee_code.replace(/[^a-zA-Z0-9\-\/]/g, '')" />
              </div>
              <div class="form-group">
                <label>PAN Card Number *</label>
                <input v-model="form.pan" maxlength="10" @input="form.pan = form.pan.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10)" />
              </div>
              <div class="form-group">
                <label>Disclosure Company *</label>
                <input v-model="form.source_company" maxlength="255" />
              </div>
              <div class="form-group">
                <label>Date Received *</label>
                <CustomDatePicker v-model="form.info_received_date" :max="todayDate" placeholder="" />
              </div>
              <div class="form-group">
                <label>Disclosure Name *</label>
                <input v-model="form.disclosure_name" maxlength="255" @input="form.disclosure_name = form.disclosure_name.replace(/[^a-zA-Z\s\.\-']/g, '')" />
              </div>
              <div class="form-group">
                <label>Disclosure Designation (Optional)</label>
                <input v-model="form.disclosure_designation" maxlength="255" />
              </div>
              <div class="form-group">
                <label>Disclosure Department (Optional)</label>
                <input v-model="form.disclosure_department" maxlength="255" />
              </div>
              <div class="form-group full-width">
                <label>Information Details *</label>
                <textarea v-model="form.info_details" rows="3"></textarea>
              </div>
            </div>
            <p class="error-msg" v-if="createError">{{ createError }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showCreate = false">Cancel</button>
            <button class="btn-primary" @click="createRecord" :disabled="creating">
              <i class="fas fa-spinner fa-spin" v-if="creating"></i>
              <span>{{ creating ? 'Creating…' : 'Create Record' }}</span>
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
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-pen-to-square"></i></div>
              <h2>Propose Edits — {{ editRecord?.public_id }}</h2>
            </div>
            <button class="modal-close" @click="showEdit = false" aria-label="Close"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div v-if="editing && !editForm.name" class="loading-state">
              <i class="fas fa-spinner fa-spin"></i> Loading record details…
            </div>
            <div class="form-grid" v-else>
              <div class="form-group">
                <label>Full Name *</label>
                <input v-model="editForm.name" maxlength="255" @input="editForm.name = editForm.name.replace(/[^a-zA-Z\s\.\-']/g, '')" />
              </div>
              <div class="form-group">
                <label>Designation *</label>
                <input v-model="editForm.designation" maxlength="255" />
              </div>
              <div class="form-group">
                <label>Employee Code *</label>
                <input v-model="editForm.employee_code" maxlength="50" @input="editForm.employee_code = editForm.employee_code.replace(/[^a-zA-Z0-9\-\/]/g, '')" />
              </div>
              <div class="form-group">
                <label>PAN Card Number *</label>
                <input v-model="editForm.pan" maxlength="10" placeholder="ABCDE1234F" @input="editForm.pan = editForm.pan.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10)" />
              </div>
              <div class="form-group">
                <label>Disclosure Company *</label>
                <input v-model="editForm.source_company" maxlength="255" />
              </div>
              <div class="form-group">
                <label>Date Received *</label>
                <CustomDatePicker v-model="editForm.info_received_date" :max="todayDate" />
              </div>
              <div class="form-group">
                <label>Disclosure Name *</label>
                <input v-model="editForm.disclosure_name" maxlength="255" @input="editForm.disclosure_name = editForm.disclosure_name.replace(/[^a-zA-Z\s\.\-']/g, '')" />
              </div>
              <div class="form-group">
                <label>Disclosure Designation (Optional)</label>
                <input v-model="editForm.disclosure_designation" maxlength="255" />
              </div>
              <div class="form-group">
                <label>Disclosure Department (Optional)</label>
                <input v-model="editForm.disclosure_department" maxlength="255" />
              </div>
              <div class="form-group full-width">
                <label>Information Details *</label>
                <textarea v-model="editForm.info_details" rows="3" placeholder="Enter disclosure details..."></textarea>
              </div>
            </div>
            <p class="error-msg" v-if="editError">{{ editError }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showEdit = false">Cancel</button>
            <button class="btn-primary" @click="saveEdit" :disabled="editing">
              <i class="fas fa-spinner fa-spin" v-if="editing"></i>
              <span>{{ editing ? 'Saving…' : 'Propose Changes' }}</span>
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
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-circle-question"></i></div>
              <h2>{{ confirmDialog.title }}</h2>
            </div>
            <button class="modal-close" @click="closeConfirm" aria-label="Close"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <p>{{ confirmDialog.message }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="closeConfirm">Cancel</button>
            <button class="btn-primary" @click="confirmAction">
              Confirm Request
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
import CustomDatePicker from '../../components/CustomDatePicker.vue'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isCollaborator = computed(() => user?.role === 'COLLABORATOR')
const { notify } = useNotifications()

const records = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const search = ref('')
const loading = ref(false)
const statusFilter = ref<'APPROVED' | 'PENDING'>('APPROVED')
const pendingCount = ref(0)

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const todayCount = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return records.value.filter(r => r.created_at?.startsWith(today)).length
})

async function fetchPendingCount() {
  if (!isCollaborator.value) return
  try {
    const res = await api.get('records/', { params: { status: 'PENDING', page_size: 1 } })
    pendingCount.value = res.data.count || 0
  } catch (e) {
    console.error(e)
  }
}

function setStatusFilter(filter: 'APPROVED' | 'PENDING') {
  statusFilter.value = filter
  page.value = 1
  fetchRecords()
}

async function fetchRecords() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize, status: statusFilter.value }
    if (search.value) params.search = search.value
    const res = await api.get('records/', { params })
    records.value = res.data.results
    total.value = res.data.count
    fetchPendingCount()
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

const todayDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

function formatApiError(err: any): string {
  const data = err?.response?.data
  if (data && typeof data === 'object') {
    if (data.error) return data.error
    if (data.detail) return data.detail
    return Object.entries(data)
      .map(([key, val]: [string, any]) => {
        const field = key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ')
        const error = Array.isArray(val) ? val[0] : val
        return `${field}: ${error}`
      })
      .join(', ')
  }
  return ''
}

function validateRecord(recordData: any): string | null {
  if (!recordData.name || recordData.name.trim().length < 2) {
    return "Full Name must be at least 2 characters long."
  }
  if (!/^[a-zA-Z\s\.\-']+$/.test(recordData.name)) {
    return "Full Name must contain only letters, spaces, dots, hyphens, and single quotes."
  }
  if (!recordData.designation || recordData.designation.trim().length < 2) {
    return "Designation must be at least 2 characters long."
  }
  if (!recordData.employee_code || recordData.employee_code.trim().length < 2) {
    return "Employee Code must be at least 2 characters long."
  }
  if (!/^[a-zA-Z0-9\-\/]+$/.test(recordData.employee_code)) {
    return "Employee Code must contain only alphanumeric characters, hyphens, and slashes."
  }
  if (!recordData.pan || !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(recordData.pan.toUpperCase())) {
    return "PAN must be in standard Indian format (e.g. ABCDE1234F)."
  }
  if (!recordData.source_company || recordData.source_company.trim().length < 2) {
    return "Disclosure Company must be at least 2 characters long."
  }
  if (!recordData.info_received_date) {
    return "Date Received is required."
  }
  if (recordData.info_received_date > todayDate.value) {
    return "Date Received cannot be in the future."
  }
  if (!recordData.disclosure_name || recordData.disclosure_name.trim().length < 2) {
    return "Disclosure Name must be at least 2 characters long."
  }
  if (!/^[a-zA-Z\s\.\-']+$/.test(recordData.disclosure_name)) {
    return "Disclosure Name must contain only letters, spaces, dots, hyphens, and single quotes."
  }
  if (!recordData.info_details || recordData.info_details.trim().length < 2) {
    return "Information Details must be at least 2 characters long."
  }
  return null
}

// ─── Create ────────────────────────────────────────────────────
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const form = ref({
  name: '', designation: '', employee_code: '', pan: '',
  source_company: '', info_details: '', info_received_date: '',
  disclosure_name: '', disclosure_designation: '', disclosure_department: ''
})

async function createRecord() {
  const validationError = validateRecord(form.value)
  if (validationError) {
    createError.value = validationError
    notify('Validation Error', validationError, 'WARNING')
    return
  }
  creating.value = true
  createError.value = ''
  try {
    await api.post('records/create/', form.value)
    notify('Record Created', `Submitted creation request for ${form.value.name}.`, 'SUCCESS')
    showCreate.value = false
    Object.keys(form.value).forEach(k => (form.value as any)[k] = '')
    fetchRecords()
  } catch (e: any) {
    createError.value = formatApiError(e) || 'Error creating record'
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
  editing.value = true
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
  const validationError = validateRecord(editForm.value)
  if (validationError) {
    editError.value = validationError
    notify('Validation Error', validationError, 'WARNING')
    return
  }
  editing.value = true
  editError.value = ''
  try {
    await api.put(`records/${editRecord.value.public_id}/update/`, editForm.value)
    notify('Edit Request Sent', `Proposed changes for ${editForm.value.name} submitted.`, 'SUCCESS')
    showEdit.value = false
    fetchRecords()
  } catch (e: any) {
    editError.value = formatApiError(e) || 'Failed to update record'
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
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; }
.page-title { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

.stats-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.stat-card {
  display: flex; align-items: center; gap: 16px;
  background: var(--bg-base);
  box-shadow: var(--neu-card);
  border-radius: var(--radius-xl);
  padding: 18px 24px;
  transition: transform var(--duration-base) var(--ease-out);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--neu-card-hover); }

.stat-icon-wrap {
  width: 46px; height: 46px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-xl); background: var(--bg-base);
  box-shadow: var(--neu-inset); flex-shrink: 0;
}
.stat-icon-wrap.blue   { color: var(--info-600); }
.stat-icon-wrap.orange { color: var(--orange-accent); }

.stat-val { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); line-height: 1.1; }
.stat-label { font-size: var(--text-xs); color: var(--text-secondary); font-weight: var(--weight-semibold); margin-top: 2px; }

/* Toolbar */
.toolbar { display: flex; gap: 16px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; min-width: 280px; max-width: 440px; }
.search-icon {
  position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
  color: var(--neutral-700); font-size: var(--text-sm); pointer-events: none;
}
.search-input {
  width: 100%; padding: 12px 20px 12px 44px; border-radius: var(--radius-pill);
  border: none; background: var(--bg-base);
  box-shadow: var(--shadow-sm); font-size: var(--text-sm); color: var(--text-primary);
  outline: none; transition: all var(--duration-fast);
}
.search-input:focus {
  background: var(--bg-base);
  box-shadow: var(--shadow-md), 0 0 0 3px var(--orange-glow);
}

.filter-toggle-group {
  display: flex;
  background: var(--bg-base);
  padding: 4px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(166, 169, 173, 0.35);
  box-shadow: var(--shadow-xs);
  gap: 4px;
}
.filter-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.filter-toggle-btn:hover {
  color: var(--text-primary);
}
.filter-toggle-btn.active {
  background: var(--orange-gradient);
  color: white;
  box-shadow: var(--sku-btn-primary-shadow);
}
.badge-count {
  background: #ef4444;
  color: white;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 10px;
  line-height: 1;
}
.filter-toggle-btn.active .badge-count {
  background: white;
  color: var(--orange-accent);
}
.tile-pending-tag {
  font-size: 9px;
  font-weight: 800;
  color: #d97706;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 6px;
  vertical-align: middle;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.tile-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 20px;
}

.record-tile {
  background: var(--bg-base);
  border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card);
  display: flex; flex-direction: column;
  transition: transform var(--duration-base) var(--ease-out), box-shadow var(--duration-base);
  overflow: hidden;
}
.record-tile:hover {
  transform: translateY(-4px);
  box-shadow: var(--neu-card-hover);
}

.tile-header {
  display: flex; align-items: center; gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--card-divider);
}
.tile-icon {
  width: 42px; height: 42px; border-radius: var(--radius-lg);
  background: var(--orange-bg-subtle);
  box-shadow: var(--neu-inset);
  color: var(--orange-accent);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-lg); flex-shrink: 0;
}
.tile-name-wrap { overflow: hidden; }
.tile-name {
  font-size: 17px;
  font-weight: 800;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25;
}
.tile-subname { font-size: var(--text-xs); color: var(--neutral-700); font-weight: var(--weight-medium); margin-top: 1px; }

.tile-details { padding: 14px 20px; display: flex; flex-direction: column; gap: 8px; }
.tile-row { display: flex; align-items: center; gap: 8px; font-size: var(--text-xs); color: var(--text-primary); }
.tile-row i { color: var(--orange-accent); font-size: var(--text-xs); width: 14px; text-align: center; }
.tile-label { color: var(--neutral-700); font-weight: var(--weight-bold); }
.tile-pan { font-family: monospace; font-weight: var(--weight-bold); color: var(--text-primary); }

.tile-footer {
  padding: 12px 20px; border-top: 1px solid var(--card-divider);
  background: var(--bg-base); display: flex; flex-direction: column; gap: 4px;
}
.tile-meta { display: flex; justify-content: space-between; align-items: center; }
.tile-badge {
  background: var(--neutral-100); border: 1px solid var(--neutral-200);
  color: var(--neutral-700); border-radius: var(--radius-xs);
  padding: 2px 8px; font-size: 11px; font-weight: var(--weight-bold); font-family: monospace;
}
.tile-date { font-size: 11px; color: var(--neutral-700); font-weight: var(--weight-semibold); }
.tile-creator { font-size: 11px; color: var(--neutral-700); font-weight: var(--weight-semibold); display: flex; align-items: center; gap: 6px; }
.tile-creator i { color: var(--orange-accent); }

.tile-actions {
  display: flex; gap: 8px; padding: 10px 20px; border-top: 1px solid var(--card-divider);
  background: var(--bg-base);
}

.icon-action {
  width: 32px; height: 32px; border-radius: var(--radius-md); border: none;
  cursor: pointer; font-size: var(--text-xs); display: flex; align-items: center;
  justify-content: center; transition: all var(--duration-fast);
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow);
  color: var(--text-secondary);
}
.icon-action:hover {
  transform: translateY(-1px);
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}

.loading-state, .empty-state {
  text-align: center; padding: 48px 24px; color: var(--text-muted);
  font-size: var(--text-sm); display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.empty-state i { font-size: 32px; color: var(--neutral-400); }

.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 12px; }
.page-btn {
  width: 34px; height: 34px; border-radius: 50%; border: none;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow);
  cursor: pointer; font-size: var(--text-xs); display: flex; align-items: center;
  justify-content: center; transition: all var(--duration-fast); color: var(--text-secondary);
}
.page-btn:hover:not(:disabled) { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: var(--text-xs); color: var(--text-secondary); font-weight: var(--weight-semibold); }

.modal-overlay {
  position: fixed; inset: 0; background: var(--overlay-bg);
  backdrop-filter: var(--glass-blur-sm); display: flex; align-items: center;
  justify-content: center; z-index: var(--z-modal); padding: 20px;
}
.modal {
  background: var(--bg-base); border-radius: var(--radius-2xl);
  width: 100%; max-width: 640px; max-height: 90vh; display: flex;
  flex-direction: column; box-shadow: var(--neu-card-hover);
  border: none; overflow: hidden;
  animation: modalIn 0.3s var(--ease-spring);
}
.confirm-modal { max-width: 400px; }

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px; border-bottom: 1px solid var(--card-divider);
}
.modal-title-group { display: flex; align-items: center; gap: 10px; }
.modal-icon-wrap {
  width: 36px; height: 36px; border-radius: var(--radius-md);
  background: var(--orange-bg-subtle); color: var(--orange-accent);
  display: flex; align-items: center; justify-content: center; font-size: var(--text-base);
}
.modal-header h2 { font-size: var(--text-lg); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }

.modal-close {
  width: 32px; height: 32px; border-radius: 50%; background: transparent;
  border: none; cursor: pointer; font-size: var(--text-xs); color: var(--text-muted);
  transition: all var(--duration-fast); display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: var(--bg-app); color: var(--text-primary); }

.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px; border-top: 1px solid var(--card-divider); background: var(--bg-app);
}

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--text-primary); }

.form-group input, .form-group select, .form-group textarea {
  padding: 10px 14px; border-radius: var(--radius-md);
  border: 1px solid rgba(166, 169, 173, 0.55); background: var(--bg-input);
  box-shadow: var(--neu-inset); font-size: var(--text-xs); font-weight: var(--weight-semibold); outline: none;
  transition: all var(--duration-fast); color: var(--text-primary);
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {
  border-color: var(--orange-accent);
  box-shadow: inset 0 2px 4px rgba(35, 28, 20, 0.08), 0 0 0 3px var(--orange-glow), 0 1px 0 rgba(255, 255, 255, 0.8);
  background: var(--bg-input-focus);
}

.error-msg { color: var(--error-600); font-size: var(--text-xs); margin-top: 8px; font-weight: var(--weight-semibold); }

.btn-primary {
  background: var(--orange-gradient); color: white; border: none;
  padding: 10px 18px; border-radius: var(--radius-pill); font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; display: inline-flex;
  align-items: center; gap: 6px; transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--sku-btn-primary-shadow);
}
.btn-primary:hover:not(:disabled) { box-shadow: var(--sku-btn-primary-shadow-hover); transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  background: var(--bg-base); color: var(--text-secondary); border: none;
  padding: 8px 16px; border-radius: var(--radius-pill); font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--sku-btn-secondary-shadow);
}
.btn-ghost:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }

@keyframes modalIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
@media (max-width: 640px) { .form-grid { grid-template-columns: 1fr; } .stats-row { grid-template-columns: 1fr; } }
</style>