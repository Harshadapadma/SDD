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

    <!-- TABLE -->
    <div class="table-card">
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading records…
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Record ID</th>
            <th>Name</th>
            <th>PAN</th>
            <th>Company</th>
            <th>Date Received</th>
            <th>Created By</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="records.length === 0">
            <td colspan="7" class="empty-row">No records found.</td>
          </tr>
          <tr v-for="record in records" :key="record.public_id" class="data-row">
            <td><span class="badge-id">{{ record.public_id }}</span></td>
            <td class="bold">{{ record.name }}</td>
            <td class="mono">{{ record.pan }}</td>
            <td>{{ record.source_company }}</td>
            <td>{{ formatDate(record.info_received_date) }}</td>
            <td><span class="user-chip">{{ record.created_by }}</span></td>
            <td>
              <div class="action-btns">
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
            </td>
          </tr>
        </tbody>
      </table>

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
            <div class="form-grid">
              <div class="form-group">
                <label>Full Name</label>
                <input v-model="editForm.name" />
              </div>
              <div class="form-group">
                <label>Designation</label>
                <input v-model="editForm.designation" />
              </div>
              <div class="form-group">
                <label>PAN</label>
                <input v-model="editForm.pan" />
              </div>
              <div class="form-group">
                <label>Source Company</label>
                <input v-model="editForm.source_company" />
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

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isCollaborator = computed(() => user?.role === 'COLLABORATOR')

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

function openEdit(record: any) {
  editRecord.value = record
  editForm.value = { ...record }
  showEdit.value = true
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

async function deleteRecord(record: any) {
  if (!confirm(`Are you sure you want to request deletion of record ${record.public_id}?`)) return
  try {
    await api.delete(`workflows/request/${record.public_id}/`)
    alert("Delete request sent to admin for approval.")
  } catch (e) {
    console.error(e)
    alert("Failed to submit delete request.")
  }
}

async function requestEdit(record: any) {
  if (!confirm(`Do you want to request EDIT access for record ${record.public_id}?`)) return
  try {
    await api.post(`workflows/access-upgrade/request/${record.public_id}/`)
    alert("Access upgrade request sent to admin for approval.")
  } catch (e: any) {
    console.error(e)
    alert(e?.response?.data?.error || "Failed to submit access request.")
  }
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
  background: #ffffff; border: 1.5px solid #e2e8f0;
  border-radius: 16px; padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  animation: fadeInUp 0.4s ease 0.05s both;
}
.stat-icon { font-size: 22px; }
.stat-icon.blue { color: #3b82f6; }
.stat-icon.orange { color: #f59e0b; }
.stat-val   { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #64748b; }

/* ─── Toolbar ────────────────────────────────────────────────── */
.toolbar { display: flex; gap: 12px; }
.search-wrap { position: relative; flex: 1; max-width: 420px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #94a3b8; font-size: 13px; }
.search-input {
  width: 100%; padding: 10px 14px 10px 38px;
  border-radius: 999px; border: 1.5px solid #e2e8f0;
  background: #f8fafc; font-size: 13px; outline: none;
  transition: border-color 0.2s, width 0.3s;
  color: #334155;
  box-sizing: border-box;
}
.search-input:focus { border-color: #3d5a80; background: #fff; }

/* ─── Buttons ────────────────────────────────────────────────── */
.btn-primary {
  background: #3d5a80; color: white; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: background 0.2s, transform 0.15s;
}
.btn-primary:hover { background: #293241; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-ghost {
  background: #f1f5f9; color: #475569; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-ghost:hover { background: #e2e8f0; color: #1e293b; }

/* ─── Table ─────────────────────────────────────────────────── */
.table-card {
  background: #fff; border-radius: 20px;
  border: 1.5px solid #e2e8f0; overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  animation: fadeInUp 0.4s ease 0.1s both;
}
.loading-state { text-align: center; padding: 40px; color: #94a3b8; font-size: 14px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table thead tr { background: #f8fafc; }
.data-table th {
  padding: 13px 16px; text-align: left;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; color: #64748b; border-bottom: 1.5px solid #e2e8f0;
}
.data-row { border-bottom: 1px solid #f1f5f9; transition: background 0.15s; }
.data-row:hover { background: #f8fafc; }
.data-table td { padding: 13px 16px; font-size: 13px; color: #334155; }
.empty-row { text-align: center; color: #94a3b8; padding: 40px; }
.bold { font-weight: 600; color: #1e293b !important; }
.mono { font-family: monospace; font-size: 12px; color: #475569; }

.badge-id {
  background: #f1f5f9; color: #3d5a80; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
}
.user-chip {
  background: #f1f5f9; color: #475569; border-radius: 6px;
  padding: 3px 8px; font-size: 11px; font-family: monospace;
}

/* ─── Action buttons ─────────────────────────────────────────── */
.action-btns { display: flex; gap: 6px; }
.icon-action {
  width: 30px; height: 30px; border-radius: 8px; border: none;
  cursor: pointer; font-size: 12px; display: flex; align-items: center;
  justify-content: center; transition: background 0.2s, transform 0.15s;
}
.icon-action:hover { transform: scale(1.1); }
.icon-action.view { background: #f1f5f9; color: #3d5a80; }
.icon-action.view:hover { background: #3d5a80; color: white; }
.icon-action.edit { background: #f1f5f9; color: #3d5a80; }
.icon-action.edit:hover { background: #3d5a80; color: white; }
.icon-action.upgrade { background: #fef3e2; color: #d97706; }
.icon-action.upgrade:hover { background: #d97706; color: white; }
.icon-action.delete { background: #fee2e2; color: #dc2626; }
.icon-action.delete:hover { background: #dc2626; color: white; }

/* ─── Pagination ─────────────────────────────────────────────── */
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 14px; }
.page-btn {
  width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid #e2e8f0;
  background: white; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; color: #475569;
}
.page-btn:hover:not(:disabled) { border-color: #3d5a80; color: #3d5a80; }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-size: 13px; color: #64748b; }

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
  transition: border-color 0.2s; resize: vertical; color: #334155;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus { border-color: #3d5a80; }

.error-msg { color: #dc2626; font-size: 12px; margin-top: 8px; }
</style>