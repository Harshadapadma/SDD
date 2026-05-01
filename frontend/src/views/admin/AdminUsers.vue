<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Users</h1>
        <p class="page-sub">Manage system users and their roles</p>
      </div>
      <button class="btn-primary" @click="showCreate = true">
        <i class="fas fa-user-plus"></i> Add User
      </button>
    </div>

    <!-- STATS ROW -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <i :class="['fas', s.icon, 'stat-icon', s.color]"></i>
        <div>
          <div class="stat-val">{{ s.val }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- TOOLBAR -->
    <div class="toolbar">
      <div class="search-wrap">
        <i class="fas fa-search search-icon"></i>
        <input v-model="search" @input="fetchUsers" class="search-input" placeholder="Search by name, email, ID…" />
      </div>
      <select v-model="roleFilter" @change="fetchUsers" class="filter-select">
        <option value="">All Roles</option>
        <option value="ADMIN">Admin</option>
        <option value="COLLABORATOR">Collaborator</option>
        <option value="VIEWER">Viewer</option>
      </select>
    </div>

    <!-- TABLE -->
    <div class="table-card">
      <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading users…</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>User ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="users.length === 0">
            <td colspan="6" class="empty-row">No users found.</td>
          </tr>
          <tr v-for="u in users" :key="u.public_id" class="data-row">
            <td><span class="badge-id">{{ u.public_id }}</span></td>
            <td class="bold">{{ u.name }}</td>
            <td class="muted">{{ u.email }}</td>
            <td><span :class="['role-badge', u.role.toLowerCase()]">{{ u.role }}</span></td>
            <td>
              <div class="status-wrap">
                <span :class="['status-dot', u.is_active ? 'active' : 'inactive']">
                  {{ u.is_active ? 'Active' : 'Inactive' }}
                </span>
                <i 
                  :class="['fas fa-id-card profile-indicator', u.is_profile_complete ? 'complete' : 'incomplete']"
                  :title="u.is_profile_complete ? 'Profile Complete' : 'Profile Incomplete'"
                ></i>
              </div>
            </td>
            <td class="muted">{{ formatDate(u.created_at) }}</td>
            <td>
              <div class="action-btns" v-if="u.role !== 'ADMIN'">
                <button class="icon-action view" title="View Profile" @click="viewProfile(u)">
                  <i class="fas fa-eye"></i>
                </button>
                <div class="role-toggle">
                  <label :class="{ active: u.role === 'COLLABORATOR' }">
                    <input type="radio" :name="'role-'+u.public_id" value="COLLABORATOR" :checked="u.role === 'COLLABORATOR'" @click.prevent="promptRoleChange(u, 'COLLABORATOR')" />
                    Coll.
                  </label>
                  <label :class="{ active: u.role === 'VIEWER' }">
                    <input type="radio" :name="'role-'+u.public_id" value="VIEWER" :checked="u.role === 'VIEWER'" @click.prevent="promptRoleChange(u, 'VIEWER')" />
                    View.
                  </label>
                </div>
                <button 
                  :class="['icon-action', u.is_blacklisted ? 'unblacklist' : 'blacklist']" 
                  :title="u.is_blacklisted ? 'Unblacklist User' : 'Blacklist User'" 
                  @click="promptBlacklist(u)"
                >
                  <i :class="['fas', u.is_blacklisted ? 'fa-user-check' : 'fa-user-slash']"></i>
                </button>
              </div>
              <span v-else class="muted">—</span>
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

    <!-- ─── CONFIRMATION MODAL ────────────────────────────────── -->
    <teleport to="body">
    <div class="modal-overlay" v-if="confirmAction" @click.self="confirmAction = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>Confirm Action</h2>
          <button class="modal-close" @click="confirmAction = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <p v-if="confirmAction.type === 'ROLE'">
            Are you sure you want to change <strong>{{ confirmAction.user.name }}</strong>'s role to <strong>{{ confirmAction.targetRole }}</strong>?
          </p>
          <p v-else>
            Are you sure you want to <strong>{{ confirmAction.user.is_blacklisted ? 'unblacklist' : 'blacklist' }}</strong> <strong>{{ confirmAction.user.name }}</strong>?
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="confirmAction = null">Cancel</button>
          <button 
            :class="['btn-primary', { 'btn-danger': confirmAction.type === 'BLACKLIST' && !confirmAction.user.is_blacklisted }]" 
            @click="executeConfirm"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>

    <!-- ─── USER DETAIL MODAL ────────────────────────────────── -->
    <div class="modal-overlay" v-if="selectedUser" @click.self="selectedUser = null">
      <div class="modal modal-md">
        <div class="modal-header">
          <h2>User Profile Details</h2>
          <button class="modal-close" @click="selectedUser = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body profile-modal-body">
          <div class="profile-header-wrap">
            <div class="avatar-circle">{{ selectedUser.name.charAt(0) }}</div>
            <div class="header-info">
              <h3>{{ selectedUser.name }}</h3>
              <p>{{ selectedUser.email }}</p>
              <span :class="['profile-status-badge', selectedUser.is_profile_complete ? 'complete' : 'incomplete']">
                {{ selectedUser.is_profile_complete ? 'Complete' : 'Incomplete' }}
              </span>
            </div>
          </div>

          <div class="details-grid-modal">
            <div class="detail-item">
              <label>Public ID</label>
              <span class="mono">{{ selectedUser.public_id }}</span>
            </div>
            <div class="detail-item">
              <label>Role</label>
              <span class="role-pill-sm">{{ selectedUser.role }}</span>
            </div>
            <div class="detail-item">
              <label>Designation</label>
              <span class="bold-val">{{ selectedUser.designation || '—' }}</span>
            </div>
            <div class="detail-item">
              <label>Company</label>
              <span class="bold-val">{{ selectedUser.company_name || '—' }}</span>
            </div>
            <div class="detail-item">
              <label>Mobile Number</label>
              <span class="bold-val">{{ selectedUser.mobile_number || '—' }}</span>
            </div>
          </div>

          <div class="ping-section" v-if="!selectedUser.is_profile_complete">
            <div class="ping-info">
              <i class="fas fa-info-circle"></i>
              <span>Profile is missing mandatory details.</span>
            </div>
            <button class="btn-ping" @click="pingUser(selectedUser)" :disabled="pinging">
              <i class="fas fa-paper-plane" v-if="!pinging"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              {{ pinging ? 'Pinging...' : 'Remind User to Complete' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    </teleport>

    <!-- ─── CREATE USER MODAL ────────────────────────────────── -->
    <teleport to="body">
    <div class="modal-overlay" v-if="showCreate" @click.self="showCreate = false">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>Add New User</h2>
          <button class="modal-close" @click="showCreate = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Full Name</label>
            <input v-model="form.name" placeholder="Jane Smith" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="form.email" type="email" placeholder="jane@negen.com" />
          </div>
          <div class="form-group">
            <label>Role</label>
            <div class="radio-group">
              <label>
                <input type="radio" value="VIEWER" v-model="form.role" />
                Viewer
              </label>
              <label>
                <input type="radio" value="COLLABORATOR" v-model="form.role" />
                Collaborator
              </label>
            </div>
          </div>
          <div class="alert-box error" v-if="createError">
            <i class="fas fa-exclamation-circle"></i>
            <span>{{ createError }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="closeCreate">Cancel</button>
          <button class="btn-primary" @click="createUser" :disabled="creating">
            <i class="fas fa-spinner fa-spin" v-if="creating"></i>
            {{ creating ? 'Creating…' : 'Create User' }}
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
const users = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const search = ref('')
const roleFilter = ref('')
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const stats = computed(() => [
  { icon: 'fa-users', color: 'green', val: total.value, label: 'Total Users' },
  { icon: 'fa-user-check', color: 'blue', val: users.value.filter(u => u.is_active).length, label: 'Active' },
  { icon: 'fa-user-shield', color: 'orange', val: users.value.filter(u => u.role === 'ADMIN').length, label: 'Admins' },
  { icon: 'fa-user-clock', color: 'red', val: users.value.filter(u => !u.is_active).length, label: 'Inactive' },
])

async function fetchUsers() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (search.value) params.search = search.value
    if (roleFilter.value) params.role = roleFilter.value
    const res = await api.get('auth/users/', { params })
    users.value = res.data.results
    total.value = res.data.count
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function changePage(p: number) { page.value = p; fetchUsers() }

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Actions ───────────────────────────────────────────────────
const confirmAction = ref<any>(null)
const selectedUser = ref<any>(null)
const pinging = ref(false)

function viewProfile(user: any) {
  selectedUser.value = user
}

async function pingUser(user: any) {
  pinging.value = true
  try {
    await api.post(`auth/users/${user.public_id}/ping/`)
    notify('User Pinged', `Notification sent to ${user.name}.`, 'SUCCESS')
    selectedUser.value = null
  } catch (err) {
    console.error(err)
    notify('Ping Failed', 'Failed to send notification.', 'ERROR')
  } finally {
    pinging.value = false
  }
}

function promptRoleChange(user: any, targetRole: string) {
  if (user.role === targetRole) return
  confirmAction.value = { type: 'ROLE', user, targetRole }
}

function promptBlacklist(user: any) {
  confirmAction.value = { type: 'BLACKLIST', user }
}

async function executeConfirm() {
  if (!confirmAction.value) return
  const { type, user, targetRole } = confirmAction.value
  confirmAction.value = null

  if (type === 'ROLE') {
    try {
      await api.put(`auth/users/${user.public_id}/change-role/`, { role: targetRole })
      user.role = targetRole
      notify('Role Updated', `User ${user.name} is now a ${targetRole}.`, 'SUCCESS')
    } catch (e) {
      console.error(e)
      notify('Update Failed', 'Failed to change user role.', 'ERROR')
      fetchUsers()
    }
  } else {
    try {
      await api.put(`auth/users/${user.public_id}/blacklist/`)
      user.is_blacklisted = !user.is_blacklisted
      notify(
        user.is_blacklisted ? 'User Blacklisted' : 'User Whitelisted',
        `${user.name} has been ${user.is_blacklisted ? 'blacklisted' : 'unblacklisted'}.`,
        user.is_blacklisted ? 'WARNING' : 'SUCCESS'
      )
    } catch (e) {
      console.error(e)
      notify('Update Failed', 'Failed to update user status.', 'ERROR')
    }
  }
}

// ─── Create User ───────────────────────────────────────────────
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const form = ref({ name: '', email: '', role: 'VIEWER' })

async function createUser() {
  creating.value = true
  createError.value = ''
  try {
    await api.post('auth/create-user/', form.value)
    notify('User Created', `Successfully added ${form.value.name}. An activation email has been sent.`, 'SUCCESS')
    showCreate.value = false
    form.value = { name: '', email: '', role: 'VIEWER' }
    fetchUsers()
  } catch (e: any) {
    const data = e?.response?.data
    if (data && typeof data === 'object') {
      const msgs = Object.entries(data).map(([key, val]: [string, any]) => {
        const field = key.charAt(0).toUpperCase() + key.slice(1)
        const error = Array.isArray(val) ? val[0] : val
        return `${field}: ${error}`
      })
      createError.value = msgs.join(', ')
    } else {
      createError.value = 'Failed to create new user.'
    }
    notify('Creation Failed', createError.value, 'ERROR')
  } finally {
    creating.value = false
  }
}


function closeCreate() {
  showCreate.value = false
  createError.value = ''
  form.value = { name: '', email: '', role: 'VIEWER' }
}

onMounted(fetchUsers)
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

/* ─── Stats ─────────────────────────────────────────────────── */
.stats-row { display: flex; gap: 14px; }
.stat-card {
  flex: 1; display: flex; align-items: center; gap: 14px;
  background: #f5fbf7; border: 1.5px solid #e0f0e8;
  border-radius: 16px; padding: 16px 20px;
  animation: fadeInUp 0.4s ease 0.05s both;
}
.stat-icon { font-size: 20px; }
.stat-icon.green  { color: #2f7d65; }
.stat-icon.blue   { color: #3b82f6; }
.stat-icon.orange { color: #f59e0b; }
.stat-icon.red    { color: #ef4444; }
.stat-val   { font-size: 22px; font-weight: 700; color: #1a2e1a; }
.stat-label { font-size: 12px; color: #7a9a7a; }

/* ─── Toolbar ────────────────────────────────────────────────── */
.toolbar { display: flex; gap: 12px; align-items: center; }
.search-wrap { position: relative; flex: 1; max-width: 380px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #aaa; font-size: 13px; }
.search-input {
  width: 100%; padding: 10px 14px 10px 38px;
  border-radius: 999px; border: 1.5px solid #e0e0e0;
  background: #f7f7f7; font-size: 13px; outline: none;
  transition: border-color 0.2s; box-sizing: border-box;
}
.search-input:focus { border-color: #2f7d65; background: #fff; }
.filter-select {
  padding: 10px 16px; border-radius: 999px; border: 1.5px solid #e0e0e0;
  font-size: 13px; outline: none; background: #f7f7f7; cursor: pointer;
}
.filter-select:focus { border-color: #2f7d65; }

/* ─── Buttons ────────────────────────────────────────────────── */
.btn-primary {
  background: #2f7d65; color: white; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: background 0.2s, transform 0.15s;
}
.btn-primary:hover { background: #256554; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-ghost {
  background: #f3f3f3; color: #444; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background 0.2s;
}
.btn-ghost:hover { background: #e8e8e8; }

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
  padding: 13px 16px; text-align: left;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; color: #5a8a6a; border-bottom: 1.5px solid #e0f0e8;
}
.data-row { border-bottom: 1px solid #f0f5f1; transition: background 0.15s; }
.data-row:hover { background: #f9fdfb; }
.data-table td { padding: 13px 16px; font-size: 13px; color: #2a3a2a; }
.empty-row { text-align: center; color: #aaa; padding: 40px; }
.bold { font-weight: 600; }
.muted { color: #666; font-size: 12px; }

.badge-id {
  background: #edf7f2; color: #2f7d65; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
}

.role-badge {
  padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600;
}
.role-badge.admin        { background: #fef3cd; color: #b45309; }
.role-badge.collaborator { background: #dbeafe; color: #1d4ed8; }
.role-badge.viewer       { background: #f3f4f6; color: #4b5563; }

.status-dot {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 500;
}
.status-dot::before { content: '●'; font-size: 8px; }
.status-dot.active   { color: #15803d; }
.status-dot.active::before { color: #22c55e; }
.status-dot.inactive { color: #9ca3af; }

/* ─── Action buttons ─────────────────────────────────────────── */
.action-btns { display: flex; gap: 6px; align-items: center; }
.role-toggle {
  display: flex; background: #f0f0f0; border-radius: 8px; padding: 2px; gap: 2px;
}
.role-toggle label {
  padding: 4px 10px; font-size: 10px; font-weight: 700; border-radius: 6px;
  cursor: pointer; transition: all 0.2s; color: #777;
}
.role-toggle label:hover { color: #333; }
.role-toggle label.active { background: white; color: #2f7d65; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.role-toggle input { display: none; }

.radio-group { display: flex; gap: 16px; margin-top: 4px; }
.radio-group label {
  display: flex; align-items: center; gap: 6px; font-size: 13px;
  cursor: pointer; color: #444; font-weight: 500;
}
.radio-group input { cursor: pointer; accent-color: #2f7d65; }

.icon-action {
  width: 28px; height: 28px; border-radius: 8px; border: none;
  cursor: pointer; font-size: 12px; display: flex; align-items: center;
  justify-content: center; transition: background 0.2s, transform 0.15s;
}
.icon-action:hover { transform: scale(1.1); }
.icon-action.blacklist { background: #fee2e2; color: #dc2626; }
.icon-action.blacklist:hover { background: #dc2626; color: white; }

.status-wrap { display: flex; align-items: center; gap: 8px; }
.profile-indicator { font-size: 14px; }
.profile-indicator.complete { color: #22c55e; }
.profile-indicator.incomplete { color: #f59e0b; opacity: 0.6; }

.icon-action.view { background: #f1f5f9; color: #3d5a80; }
.icon-action.view:hover { background: #3d5a80; color: white; }

/* ─── Profile Modal ────────────────────────────────────────── */
.profile-header-wrap { display: flex; align-items: center; gap: 20px; margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #f1f5f9; }
.avatar-circle { width: 64px; height: 64px; border-radius: 50%; background: #e0f2fe; color: #0369a1; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; }
.header-info h3 { font-size: 18px; font-weight: 800; color: #1e293b; margin: 0; }
.header-info p { font-size: 14px; color: #64748b; margin: 2px 0 8px; }

.profile-status-badge { padding: 4px 12px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.profile-status-badge.complete { background: #dcfce7; color: #15803d; }
.profile-status-badge.incomplete { background: #fef3c7; color: #b45309; }

.details-grid-modal { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item label { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.detail-item span { font-size: 14px; color: #1e293b; }
.detail-item span.mono { font-family: monospace; font-weight: 700; color: #3d5a80; }
.detail-item span.bold-val { font-weight: 700; color: #334155; }
.role-pill-sm { background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }

.ping-section { margin-top: 32px; padding: 20px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 16px; display: flex; flex-direction: column; gap: 16px; align-items: center; text-align: center; }
.ping-info { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #92400e; font-weight: 600; }
.btn-ping { width: 100%; padding: 12px; background: #f59e0b; color: white; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s; }
.btn-ping:hover:not(:disabled) { background: #d97706; transform: translateY(-1px); }

.alert-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  margin-top: 16px;
}
.alert-box.error {
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fee2e2;
}
.alert-box i { font-size: 16px; }

.icon-action.unblacklist { background: #dcfce7; color: #16a34a; }
.icon-action.unblacklist:hover { background: #16a34a; color: white; }

.btn-danger { background: #dc2626; color: white; border: none; }
.btn-danger:hover { background: #b91c1c; }

/* ─── Pagination ─────────────────────────────────────────────── */
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 14px; }
.page-btn {
  width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid #ddd;
  background: white; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.page-btn:hover:not(:disabled) { border-color: #2f7d65; color: #2f7d65; }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-size: 13px; color: #666; }

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
.modal-sm { width: 440px; }
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
.modal-close:hover { background: #e2e8f0; color: #1e293b; }
.modal-close:hover { background: #ddd; }
.modal-body { padding: 20px 26px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 14px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 26px 22px; border-top: 1px solid #eee;
}

/* ─── Form ───────────────────────────────────────────────────── */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; font-weight: 600; color: #5a8a6a; }
.form-group input,
.form-group select {
  padding: 10px 14px; border-radius: 10px;
  border: 1.5px solid #e0e0e0; font-size: 13px; outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus,
.form-group select:focus { border-color: #2f7d65; }

.info-box {
  display: flex; gap: 12px; padding: 14px 16px;
  background: #edf7f2; border-radius: 12px; border: 1px solid #b7e4ca;
  font-size: 13px; color: #1a5c3a; align-items: flex-start;
}
.link-text { font-family: monospace; font-size: 11px; margin: 4px 0 0; word-break: break-all; color: #2f7d65; }
.error-msg { color: #dc2626; font-size: 12px; }
</style>
