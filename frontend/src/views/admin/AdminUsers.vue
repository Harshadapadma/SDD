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
      <div class="filter-dropdown-wrap">
        <button class="filter-btn" @click.stop="showRoleMenu = !showRoleMenu">
          <i class="fas fa-filter"></i>
          <span>{{ roleFilterLabel || 'All Roles' }}</span>
          <i class="fas fa-chevron-down ms-auto"></i>
        </button>

        <transition name="menu-fade">
          <div class="filter-menu" v-if="showRoleMenu" @click.stop>
            <div class="menu-header">
              <div class="menu-icon-bg"><i class="fas fa-users-cog"></i></div>
              <div class="menu-info">
                <div class="menu-title">Filter by Role</div>
                <div class="menu-sub">{{ total }} total users</div>
              </div>
            </div>
            
            <div class="menu-divider"></div>
            
            <div class="menu-item" :class="{ active: roleFilter === '' }" @click="setRoleFilter('')">
              <i class="fas fa-users"></i>
              <span>All Roles</span>
            </div>
            
            <div class="menu-divider"></div>
            
            <div class="menu-item" :class="{ active: roleFilter === 'ADMIN' }" @click="setRoleFilter('ADMIN')">
              <i class="fas fa-user-shield"></i>
              <span>Admin</span>
            </div>
            <div class="menu-item" :class="{ active: roleFilter === 'COLLABORATOR' }" @click="setRoleFilter('COLLABORATOR')">
              <i class="fas fa-user-friends"></i>
              <span>Collaborator</span>
            </div>
            <div class="menu-item" :class="{ active: roleFilter === 'VIEWER' }" @click="setRoleFilter('VIEWER')">
              <i class="fas fa-eye"></i>
              <span>Viewer</span>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- TILE GRID -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading users…
    </div>
    
    <div v-else-if="users.length === 0" class="empty-state">
      <i class="fas fa-users-slash"></i>
      <p>No users found.</p>
    </div>

    <div v-else class="tile-grid">
      <div v-for="u in users" :key="u.public_id" class="user-tile">
        <div class="tile-header">
          <div class="user-avatar-small">{{ u.name.charAt(0).toUpperCase() }}</div>
          <div class="user-info-main">
            <div class="user-name">{{ u.name }}</div>
            <div class="user-email">{{ u.email }}</div>
          </div>
          <span :class="['role-badge', u.role.toLowerCase()]">{{ u.role }}</span>
        </div>
        
        <div class="tile-details">
          <div class="tile-row">
            <span class="badge-id">{{ u.public_id }}</span>
          </div>
          <div class="tile-row">
            <div class="status-wrap">
              <span :class="['status-dot', u.is_active ? 'active' : 'inactive']">
                {{ u.is_active ? 'Active' : 'Inactive' }}
              </span>
              <i 
                :class="['fas fa-id-card profile-indicator', u.is_profile_complete ? 'complete' : 'incomplete']"
                :title="u.is_profile_complete ? 'Profile Complete' : 'Profile Incomplete'"
              ></i>
            </div>
          </div>
        </div>

        <div class="tile-footer">
          <div class="tile-meta">
            <span class="tile-date"><i class="fas fa-calendar-alt"></i> {{ formatDate(u.created_at) }}</span>
          </div>
        </div>

        <div class="tile-actions">
          <template v-if="u.role !== 'ADMIN'">
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
          </template>
          <span v-else class="muted">—</span>
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
const showRoleMenu = ref(false)

const roleFilterLabel = computed(() => {
  if (!roleFilter.value) return 'All Roles'
  return roleFilter.value.charAt(0) + roleFilter.value.slice(1).toLowerCase()
})

function setRoleFilter(role: string) {
  roleFilter.value = role
  showRoleMenu.value = false
  fetchUsers()
}

onMounted(() => {
  window.addEventListener('click', () => { showRoleMenu.value = false })
})

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
  background: linear-gradient(135deg, #f5fbf7 0%, #ecf5ef 100%);
  border: 1.5px solid rgba(47, 125, 101, 0.12);
  border-radius: 16px; padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(47, 125, 101, 0.04);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease;
  position: relative; overflow: hidden;
}
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
}
.stat-card:nth-child(1) { animation: fadeInUp 0.4s ease 0.05s both; }
.stat-card:nth-child(2) { animation: fadeInUp 0.4s ease 0.10s both; }
.stat-card:nth-child(3) { animation: fadeInUp 0.4s ease 0.15s both; }
.stat-card:nth-child(4) { animation: fadeInUp 0.4s ease 0.20s both; }
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(47, 125, 101, 0.1);
}
.stat-icon { font-size: 20px; transition: transform 0.2s ease; }
.stat-card:hover .stat-icon { transform: scale(1.15); }
.stat-icon.green  { color: #2f7d65; }
.stat-icon.blue   { color: #3b82f6; }
.stat-icon.orange { color: #f59e0b; }
.stat-icon.red    { color: #ef4444; }
.stat-val   { font-size: 22px; font-weight: 700; color: #1a2e1a; }
.stat-label { font-size: 12px; color: #7a9a7a; }

/* ─── Toolbar ────────────────────────────────────────────────── */
.toolbar { display: flex; gap: 12px; align-items: center; }
.search-wrap { position: relative; flex: 1; max-width: 380px; }
.search-icon {
  position: absolute; left: 18px; top: 50%; transform: translateY(-50%);
  color: #5a8a6a; font-size: 15px; z-index: 1;
}
.search-input {
  width: 100%; padding: 13px 16px 13px 48px; border-radius: 999px;
  border: 1.5px solid rgba(47, 125, 101, 0.15); 
  background: rgba(255, 255, 255, 0.7); 
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  font-size: 14px; font-weight: 500; color: #1a2e1a; outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  box-sizing: border-box;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
}
.search-input::placeholder { color: #94a3b8; font-weight: 400; }
.search-input:hover { background: rgba(255, 255, 255, 0.9); border-color: rgba(47, 125, 101, 0.3); }
.search-input:focus { 
  border-color: #2f7d65; background: #fff; 
  box-shadow: 0 8px 20px rgba(47, 125, 101, 0.12), 0 0 0 4px rgba(47, 125, 101, 0.06);
  transform: translateY(-1px);
}

/* ─── Premium Toolbar Dropdown ────────────────────────────── */
.filter-dropdown-wrap { position: relative; }
.filter-btn {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 18px; border-radius: 999px;
  border: 1.5px solid #e2e8f0; background: white;
  color: #475569; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.25s;
  min-width: 160px;
}
.filter-btn:hover { background: #f8fafc; border-color: #cbd5e1; transform: translateY(-1px); }
.filter-btn .ms-auto { margin-left: auto; font-size: 11px; opacity: 0.6; }

.filter-menu {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 220px; background: rgba(248, 253, 250, 0.96); border-radius: 20px;
  box-shadow: 0 15px 35px rgba(47, 125, 101, 0.12), 0 5px 15px rgba(0,0,0,0.05);
  padding: 8px; z-index: 100;
  border: 1px solid rgba(47, 125, 101, 0.15);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transform-origin: top right;
  animation: menuIn 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.menu-header { display: flex; align-items: center; gap: 12px; padding: 12px 14px 10px; }
.menu-icon-bg {
  width: 38px; height: 38px; border-radius: 12px;
  background: #f1f5f9; color: #475569;
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.menu-info { display: flex; flex-direction: column; }
.menu-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.menu-sub { font-size: 11px; color: #94a3b8; font-weight: 500; }

.menu-divider { height: 1px; background: #f1f5f9; margin: 8px 0; }

.menu-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 12px;
  cursor: pointer; transition: all 0.2s;
  color: #475569;
}
.menu-item i { width: 16px; font-size: 14px; color: #94a3b8; transition: color 0.2s; }
.menu-item span { font-size: 13px; font-weight: 600; flex: 1; }
.menu-shortcut { font-size: 10px; color: #cbd5e1; font-weight: 700; opacity: 0.8; }

.menu-item:hover { background: #ecfdf5; color: #059669; }
.menu-item:hover i { color: #059669; }
.menu-item.active { background: #f0fdf4; color: #15803d; }
.menu-item.active i { color: #15803d; }

@keyframes menuIn {
  from { opacity: 0; transform: scale(0.95) translateY(-10px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.menu-fade-enter-active, .menu-fade-leave-active { transition: all 0.2s ease; }
.menu-fade-enter-from, .menu-fade-leave-to { opacity: 0; transform: translateY(-8px); }
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
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.btn-primary:hover { background: #256554; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(47, 125, 101, 0.25); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-ghost {
  background: rgba(47, 125, 101, 0.06); color: #2f7d65; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-ghost:hover { background: rgba(47, 125, 101, 0.12); color: #1a5c3a; }

/* ─── Tile Grid ──────────────────────────────────────────────── */
.tile-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px; animation: fadeInUp 0.4s ease 0.1s both;
}

.user-tile {
  background: linear-gradient(135deg, #f9fdfa 0%, #f0f7f3 100%);
  border-radius: 18px; padding: 0;
  border: 1.5px solid rgba(47, 125, 101, 0.12);
  box-shadow: 0 4px 12px rgba(47, 125, 101, 0.04);
  display: flex; flex-direction: column;
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease;
  overflow: hidden; animation: fadeInUp 0.4s ease both;
  position: relative;
}
.user-tile::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1.5px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent);
  z-index: 1;
}
.user-tile:nth-child(1) { animation-delay: 0.05s; }
.user-tile:nth-child(2) { animation-delay: 0.10s; }
.user-tile:nth-child(3) { animation-delay: 0.15s; }
.user-tile:nth-child(4) { animation-delay: 0.20s; }
.user-tile:nth-child(n+5) { animation-delay: 0.25s; }

.user-tile:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(47, 125, 101, 0.12);
}

.tile-header {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 20px 14px;
  background: rgba(47, 125, 101, 0.03);
  border-bottom: 1px solid rgba(47, 125, 101, 0.06);
}
.user-avatar-small {
  width: 40px; height: 40px; border-radius: 12px;
  background: rgba(47, 125, 101, 0.1); color: #2f7d65;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 700; flex-shrink: 0;
}
.user-info-main { flex: 1; overflow: hidden; }
.user-name {
  font-size: 15px; font-weight: 700; color: #1a2e1a;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.user-email { font-size: 12px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.tile-details { padding: 14px 20px; display: flex; flex-direction: column; gap: 8px; }
.tile-row { display: flex; align-items: center; justify-content: space-between; }
.badge-id {
  background: rgba(47, 125, 101, 0.08); color: #2f7d65; border-radius: 8px;
  padding: 3px 9px; font-size: 11px; font-weight: 700; font-family: monospace;
  border: 1px solid rgba(47, 125, 101, 0.1);
}

.tile-footer {
  padding: 12px 20px; border-top: 1px solid #f0f5f1;
  display: flex; flex-direction: column; gap: 6px;
}
.tile-meta { display: flex; justify-content: space-between; align-items: center; }
.tile-date { font-size: 11px; color: #94a3b8; font-weight: 500; }

.tile-actions {
  display: flex; gap: 6px; padding: 12px 20px; border-top: 1px solid #f0f5f1; align-items: center; justify-content: flex-start;
}

.loading-state {
  display: flex; align-items: center; justify-content: center;
  padding: 60px 20px; color: #2f7d65; gap: 12px; font-size: 15px;
}
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 20px; color: #94a3b8; gap: 16px;
}
.empty-state i { font-size: 40px; opacity: 0.4; }

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
  justify-content: center; transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
.icon-action:hover { transform: scale(1.12); }
.icon-action.blacklist { background: #fee2e2; color: #dc2626; }
.icon-action.blacklist:hover { background: #dc2626; color: white; box-shadow: 0 4px 10px rgba(220, 38, 38, 0.2); }

.status-wrap { display: flex; align-items: center; gap: 8px; }
.profile-indicator { font-size: 14px; }
.profile-indicator.complete { color: #22c55e; }
.profile-indicator.incomplete { color: #f59e0b; opacity: 0.6; }

.icon-action.view { background: rgba(61, 90, 128, 0.08); color: #3d5a80; }
.icon-action.view:hover { background: #3d5a80; color: white; box-shadow: 0 4px 10px rgba(61, 90, 128, 0.2); }

/* ─── Profile Modal ────────────────────────────────────────── */
.profile-header-wrap { display: flex; align-items: center; gap: 20px; margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #f1f5f9; }
.avatar-circle { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #e6f5ee, #d6ede3); color: #2f7d65; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; box-shadow: 0 4px 12px rgba(47, 125, 101, 0.12); }
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
.icon-action.unblacklist:hover { background: #16a34a; color: white; box-shadow: 0 4px 10px rgba(22, 163, 106, 0.2); }

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
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal {
  background: white; border-radius: 22px; width: 680px; max-width: 95vw;
  max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.18), 0 0 0 1px rgba(47,125,101,0.08); animation: slideUp 0.25s ease;
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
  width: 32px; height: 32px; border-radius: 50%; background: #f1f5f9;
  border: none; cursor: pointer; font-size: 13px; color: #64748b; transition: all 0.2s;
}
.modal-close:hover { background: #e2e8f0; color: #1e293b; transform: rotate(90deg); }
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
