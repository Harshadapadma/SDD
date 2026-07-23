<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">User Management</h1>
        <p class="page-sub">Provision accounts, manage permissions, and track profile status</p>
      </div>
      <button class="btn-primary" v-if="currentUser?.role === 'ADMIN'" @click="showCreate = true">
        <i class="fas fa-user-plus"></i> Add User
      </button>
    </div>

    <!-- STATS ROW (Neomorphism) -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div :class="['stat-icon-wrap', s.color]">
          <i :class="['fas', s.icon]"></i>
        </div>
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
        <input v-model="search" @input="fetchUsers" class="search-input" placeholder="Search by name, email, public ID…" />
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
                <div class="menu-title">{{ total }} total users</div>
              </div>
            </div>
            
            <div class="menu-divider"></div>
            
            <div class="menu-item" :class="{ active: roleFilter === '' }" @click="setRoleFilter('')">
              <i class="fas fa-users"></i>
              <span>All Roles</span>
            </div>
            
            <div class="menu-divider"></div>
            
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
      <i class="fas fa-spinner fa-spin"></i> Loading user accounts…
    </div>
    
    <div v-else-if="users.length === 0" class="empty-state">
      <i class="fas fa-users-slash"></i>
      <p>No user accounts found.</p>
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
            <div class="status-wrap ms-auto">
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
            <button class="icon-action view" title="View Profile Details" @click="viewProfile(u)">
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
          <span v-else class="muted font-mono">System Owner</span>
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

    <!-- ─── CONFIRMATION MODAL (Glassmorphism) ────────────────── -->
    <teleport to="body">
    <div class="modal-overlay" v-if="confirmAction" @click.self="confirmAction = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon-wrap"><i class="fas fa-circle-question"></i></div>
            <h2>Confirm Action</h2>
          </div>
          <button class="modal-close" @click="confirmAction = null" aria-label="Close"><i class="fas fa-times"></i></button>
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
    </teleport>

    <!-- ─── USER DETAIL MODAL (Glassmorphism) ────────────────── -->
    <teleport to="body">
    <div class="modal-overlay" v-if="selectedUser" @click.self="selectedUser = null">
      <div class="modal modal-md">
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon-wrap"><i class="fas fa-id-card"></i></div>
            <h2>User Profile Details</h2>
          </div>
          <button class="modal-close" @click="selectedUser = null" aria-label="Close"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body profile-modal-body">
          <div class="profile-header-wrap">
            <div class="avatar-circle">{{ selectedUser.name.charAt(0).toUpperCase() }}</div>
            <div class="header-info">
              <h3>{{ selectedUser.name }}</h3>
              <p>{{ selectedUser.email }}</p>
              <span :class="['profile-status-badge', selectedUser.is_profile_complete ? 'complete' : 'incomplete']">
                {{ selectedUser.is_profile_complete ? 'Profile Complete' : 'Profile Incomplete' }}
              </span>
            </div>
          </div>

          <div class="details-grid-modal">
            <div class="detail-item">
              <label>Public ID</label>
              <span class="mono">{{ selectedUser.public_id }}</span>
            </div>
            <div class="detail-item">
              <label>System Role</label>
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

          <!-- ASSIGNED RECORDS & ACCESS PRIVILEGES SECTION -->
          <div class="user-records-access-section">
            <div class="section-title">
              <i class="fas fa-database"></i>
              <span>Assigned Records &amp; Access Privileges</span>
              <span class="count-pill" v-if="selectedUser.records_access">{{ selectedUser.records_access.length }}</span>
            </div>
            
            <div class="user-records-list" v-if="selectedUser.records_access && selectedUser.records_access.length > 0">
              <div class="user-record-card" v-for="rec in selectedUser.records_access" :key="rec.record_id">
                <div class="rec-main">
                  <div class="rec-name">{{ rec.record_name }}</div>
                  <div class="rec-meta">
                    <span class="rec-id">{{ rec.record_id }}</span> &bull; 
                    <span>PAN: <strong>{{ rec.pan || '—' }}</strong></span> &bull; 
                    <span>{{ rec.source_company || '—' }}</span>
                  </div>
                </div>
                <div class="rec-access-badge">
                  <span :class="['access-pill', rec.access_type.toLowerCase()]">
                    {{ rec.access_type === 'EDIT' ? 'Full Edit' : 'View Only' }}
                  </span>
                </div>
              </div>
            </div>
            <div class="user-records-empty" v-else>
              <i class="fas fa-folder-open"></i>
              <p>No records assigned to this user yet.</p>
            </div>
          </div>

          <div class="ping-section" v-if="!selectedUser.is_profile_complete">
            <div class="ping-info">
              <i class="fas fa-circle-info"></i>
              <span>Profile is missing mandatory details.</span>
            </div>
            <button class="btn-ping" @click="pingUser(selectedUser)" :disabled="pinging">
              <i class="fas fa-paper-plane" v-if="!pinging"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              <span>{{ pinging ? 'Sending...' : 'Remind User to Complete' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    </teleport>

    <!-- ─── CREATE USER MODAL (Glassmorphism) ────────────────── -->
    <teleport to="body">
    <div class="modal-overlay" v-if="showCreate" @click.self="showCreate = false">
      <div class="modal modal-sm">
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon-wrap"><i class="fas fa-user-plus"></i></div>
            <h2>Add New User</h2>
          </div>
          <button class="modal-close" @click="showCreate = false" aria-label="Close"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Full Name *</label>
            <input v-model="form.name" placeholder="e.g. Rahul Sharma" maxlength="255" @input="form.name = form.name.replace(/[^a-zA-Z\s\.\-']/g, '')" />
          </div>
          <div class="form-group">
            <label>Email Address *</label>
            <input v-model="form.email" type="email" placeholder="rahul@company.com" maxlength="255" />
          </div>
          <div class="form-group">
            <label>System Role *</label>
            <div class="role-selector">
              <button 
                type="button" 
                :class="['role-btn-option', { active: form.role === 'VIEWER' }]"
                @click="form.role = 'VIEWER'"
              >
                <i class="fas fa-eye"></i>
                <div class="role-btn-label">Viewer</div>
              </button>
              <button 
                type="button" 
                :class="['role-btn-option', { active: form.role === 'COLLABORATOR' }]"
                @click="form.role = 'COLLABORATOR'"
              >
                <i class="fas fa-user-edit"></i>
                <div class="role-btn-label">Collaborator</div>
              </button>
            </div>
          </div>
          <div class="alert-box error" v-if="createError">
            <i class="fas fa-circle-exclamation"></i>
            <span>{{ createError }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="closeCreate">Cancel</button>
          <button class="btn-primary" @click="createUser" :disabled="creating">
            <i class="fas fa-spinner fa-spin" v-if="creating"></i>
            <span>{{ creating ? 'Creating…' : 'Create User' }}</span>
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
const currentUser = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
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
  fetchUsers()
  window.addEventListener('click', () => { showRoleMenu.value = false })
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const userStats = ref({
  total_users: 0,
  active_users: 0,
  inactive_users: 0,
  blacklisted_users: 0
})

async function fetchUserStats() {
  try {
    const res = await api.get('auth/users/stats/')
    userStats.value = res.data
  } catch (e) {
    console.error('Failed to load user stats:', e)
  }
}

const stats = computed(() => [
  { icon: 'fa-users', color: 'green', val: userStats.value.total_users, label: 'Total Users' },
  { icon: 'fa-user-check', color: 'blue', val: userStats.value.active_users, label: 'Active' },
  { icon: 'fa-user-clock', color: 'red', val: userStats.value.inactive_users, label: 'Inactive' },
  { icon: 'fa-user-slash', color: 'orange', val: userStats.value.blacklisted_users, label: 'Blacklisted' },
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
    await fetchUserStats()
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
      fetchUserStats()
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
      fetchUserStats()
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
  if (!form.value.name || form.value.name.trim().length < 2) {
    createError.value = 'Full name must be at least 2 characters long.'
    notify('Validation Error', createError.value, 'WARNING')
    return
  }
  if (!/^[a-zA-Z\s\.\-']+$/.test(form.value.name)) {
    createError.value = 'Name must contain only letters, spaces, dots, hyphens, and single quotes.'
    notify('Validation Error', createError.value, 'WARNING')
    return
  }
  const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
  if (!form.value.email || !emailRegex.test(form.value.email)) {
    createError.value = 'Please enter a valid email address.'
    notify('Validation Error', createError.value, 'WARNING')
    return
  }
  creating.value = true
  createError.value = ''
  try {
    await api.post('auth/create-user/', form.value)
    notify('User Created', `Successfully added ${form.value.name}. Activation link sent.`, 'SUCCESS')
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
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; }
.page-title { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

/* Stats (Neomorphism) */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.stat-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--bg-base); box-shadow: var(--neu-card);
  border-radius: var(--radius-xl); padding: 18px 20px;
  transition: transform var(--duration-base) var(--ease-out);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--neu-card-hover); }

.stat-icon-wrap {
  width: 44px; height: 44px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-lg); background: var(--bg-base);
  box-shadow: var(--neu-inset); flex-shrink: 0;
}
.stat-icon-wrap.green  { color: var(--success-600); }
.stat-icon-wrap.blue   { color: var(--info-600); }
.stat-icon-wrap.red    { color: var(--error-600); }
.stat-icon-wrap.orange { color: var(--warning-600); }

.stat-val { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); line-height: 1.1; }
.stat-label { font-size: var(--text-xs); color: var(--text-secondary); font-weight: var(--weight-semibold); margin-top: 2px; }

/* Toolbar */
.toolbar { display: flex; gap: 12px; }
.search-wrap { position: relative; flex: 1; max-width: 440px; }
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

.filter-dropdown-wrap { position: relative; }
.filter-btn {
  background: var(--bg-base); border: none; padding: 10px 18px; border-radius: var(--radius-pill);
  font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-secondary);
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  box-shadow: var(--sku-btn-secondary-shadow); transition: all var(--duration-fast);
}
.filter-btn:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }

.filter-menu {
  position: absolute; top: calc(100% + 8px); right: 0; width: 220px;
  background: var(--bg-base); border-radius: var(--radius-xl); border: none;
  box-shadow: var(--neu-card-hover); z-index: var(--z-dropdown); padding: 8px;
}
.menu-header { display: flex; gap: 10px; align-items: center; padding: 8px; }
.menu-icon-bg { width: 32px; height: 32px; border-radius: var(--radius-md); background: var(--orange-bg-subtle); color: var(--orange-accent); display: flex; align-items: center; justify-content: center; font-size: var(--text-sm); }
.menu-title { font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-primary); }
.menu-sub { font-size: 10px; color: var(--text-muted); }
.menu-divider { height: 1px; background: var(--card-divider); margin: 6px 0; }
.menu-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: var(--radius-md); font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--text-secondary); cursor: pointer; transition: all var(--duration-fast); }
.menu-item:hover { background: var(--bg-app); color: var(--orange-accent); box-shadow: var(--neu-inset); }
.menu-item.active { background: var(--bg-app); box-shadow: var(--neu-inset); color: var(--orange-accent); font-weight: var(--weight-bold); }

/* Tile Grid */
.tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.user-tile {
  background: var(--bg-base); border-radius: var(--radius-2xl); box-shadow: var(--neu-card);
  display: flex; flex-direction: column; overflow: hidden;
  transition: transform var(--duration-base) var(--ease-out), box-shadow var(--duration-base);
}
.user-tile:hover { transform: translateY(-4px); box-shadow: var(--neu-card-hover); }

.tile-header { display: flex; align-items: center; gap: 12px; padding: 18px 20px 14px; border-bottom: 1px solid var(--card-divider); }
.user-avatar-small {
  width: 42px; height: 42px; border-radius: 50%; background: var(--orange-gradient);
  color: white; display: flex; align-items: center; justify-content: center; font-weight: var(--weight-bold);
  font-size: var(--text-base); box-shadow: var(--sku-btn-primary-shadow); flex-shrink: 0;
}
.user-info-main { overflow: hidden; flex: 1; }
.user-name { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-email { font-size: var(--text-xs); color: var(--neutral-700); font-weight: var(--weight-medium); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.role-badge { padding: 3px 10px; border-radius: var(--radius-pill); font-size: 10px; font-weight: var(--weight-bold); }
.role-badge.admin { background: var(--orange-bg-subtle); color: var(--orange-accent); border: 1px solid var(--orange-border); }
.role-badge.collaborator { background: var(--info-bg); color: var(--info-700); border: 1px solid var(--info-border); }
.role-badge.viewer { background: var(--neutral-100); color: var(--neutral-700); border: 1px solid var(--neutral-200); }

.tile-details { padding: 14px 20px; }
.tile-row { display: flex; align-items: center; gap: 8px; }
.badge-id { background: var(--neutral-100); color: var(--neutral-700); border: 1px solid var(--neutral-200); border-radius: var(--radius-xs); padding: 2px 8px; font-size: 11px; font-weight: var(--weight-bold); font-family: monospace; }
.status-wrap { display: flex; align-items: center; gap: 8px; }
.status-dot { font-size: 11px; font-weight: var(--weight-semibold); display: flex; align-items: center; gap: 4px; }
.status-dot.active { color: var(--success-600); }
.status-dot.inactive { color: var(--error-600); }
.profile-indicator { font-size: 14px; }
.profile-indicator.complete { color: var(--success-600); }
.profile-indicator.incomplete { color: var(--warning-600); }

.tile-footer { padding: 10px 20px; border-top: 1px solid var(--card-divider); background: var(--bg-base); font-size: 11px; color: var(--neutral-700); font-weight: var(--weight-semibold); }

.tile-actions {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 20px; background: var(--bg-app); border-top: 1px solid var(--card-divider);
}

.icon-action {
  width: 36px; height: 36px; border-radius: var(--radius-lg); border: none;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow);
  color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all var(--duration-fast);
}
.icon-action:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }
.icon-action.blacklist:hover { color: var(--error-600); }
.icon-action.unblacklist:hover { color: var(--success-600); }

.role-toggle { display: flex; background: var(--bg-base); border-radius: var(--radius-lg); padding: 3px; box-shadow: var(--neu-inset); flex: 1; }
.role-toggle label {
  flex: 1; text-align: center; padding: 6px; border-radius: var(--radius-md);
  font-size: 11px; font-weight: var(--weight-bold); color: var(--text-secondary);
  cursor: pointer; transition: all var(--duration-fast);
}
.role-toggle label.active { background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow); color: var(--orange-accent); }
.role-toggle input { display: none; }

.ms-auto { margin-left: auto; }
.loading-state, .empty-state { text-align: center; padding: 48px 24px; color: var(--text-muted); font-size: var(--text-sm); display: flex; flex-direction: column; align-items: center; gap: 8px; }

.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; padding-top: 10px; }
.page-btn {
  width: 38px; height: 38px; border-radius: var(--radius-lg); border: none;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow); color: var(--text-primary);
  cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all var(--duration-fast);
}
.page-btn:hover:not(:disabled) { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; box-shadow: none; }
.page-info { font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-secondary); }

/* Modals */
.modal-overlay { position: fixed; inset: 0; background: var(--overlay-bg); backdrop-filter: var(--glass-blur-sm); display: flex; align-items: center; justify-content: center; z-index: var(--z-modal); padding: 20px; }
.modal { background: var(--bg-base); border-radius: var(--radius-2xl); width: 100%; max-width: 480px; box-shadow: var(--neu-card-hover); border: none; display: flex; flex-direction: column; overflow: hidden; }
.modal-sm { max-width: 400px; }
.modal-md { max-width: 520px; }

.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px; border-bottom: 1px solid var(--card-divider); }
.modal-title-group { display: flex; align-items: center; gap: 10px; }
.modal-icon-wrap { width: 36px; height: 36px; border-radius: var(--radius-md); background: var(--orange-bg-subtle); color: var(--orange-accent); display: flex; align-items: center; justify-content: center; font-size: var(--text-base); }
.modal-header h2 { font-size: var(--text-lg); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.modal-close { width: 32px; height: 32px; border-radius: 50%; background: transparent; border: none; cursor: pointer; font-size: var(--text-xs); color: var(--text-muted); display: flex; align-items: center; justify-content: center; }
.modal-close:hover { background: var(--bg-app); color: var(--text-primary); }

.modal-body { padding: 20px 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 24px; border-top: 1px solid var(--card-divider); background: var(--bg-app); }

.profile-modal-body { display: flex; flex-direction: column; gap: 20px; }
.profile-header-wrap { display: flex; align-items: center; gap: 16px; background: var(--bg-app); padding: 16px; border-radius: var(--radius-xl); border: none; box-shadow: var(--neu-inset); }
.avatar-circle { width: 52px; height: 52px; border-radius: 50%; background: var(--orange-gradient); color: white; display: flex; align-items: center; justify-content: center; font-size: var(--text-xl); font-weight: var(--weight-bold); box-shadow: var(--sku-btn-primary-shadow); }
.header-info h3 { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.header-info p { font-size: var(--text-xs); color: var(--text-secondary); margin: 2px 0 6px; }

.profile-status-badge { padding: 2px 8px; border-radius: var(--radius-pill); font-size: 10px; font-weight: var(--weight-bold); }
.profile-status-badge.complete { background: var(--success-bg); color: var(--success-700); border: 1px solid var(--success-border); }
.profile-status-badge.incomplete { background: var(--warning-bg); color: var(--warning-700); border: 1px solid var(--warning-border); }

.details-grid-modal { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item label { font-size: 11px; font-weight: var(--weight-bold); color: var(--text-muted); text-transform: uppercase; }
.detail-item .mono { font-family: monospace; font-size: var(--text-xs); color: var(--orange-accent); font-weight: var(--weight-bold); }
.detail-item .bold-val { font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--text-primary); }
.role-pill-sm { font-size: 11px; font-weight: var(--weight-bold); color: var(--text-primary); }

/* User Records Access Section */
.user-records-access-section {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(166, 169, 173, 0.25);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  font-weight: 800;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.count-pill {
  background: var(--orange-accent);
  color: white;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: 800;
}

.user-records-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 190px;
  overflow-y: auto;
  padding-right: 4px;
}

.user-record-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid rgba(166, 169, 173, 0.3);
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  transition: all var(--duration-fast);
}

.user-record-card:hover {
  border-color: var(--orange-border);
  box-shadow: var(--shadow-sm);
}

.rec-main { display: flex; flex-direction: column; gap: 2px; }
.rec-name { font-size: 11.5px; font-weight: 800; color: var(--text-primary); }
.rec-meta { font-size: 10px; color: var(--text-muted); }
.rec-id { font-family: monospace; font-weight: 700; color: var(--orange-accent); }

.access-pill {
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 9.5px;
  font-weight: 800;
  text-transform: uppercase;
}
.access-pill.edit { background: var(--success-bg); color: var(--success-700); border: 1px solid var(--success-border); }
.access-pill.view { background: var(--info-bg); color: var(--info-700); border: 1px solid var(--info-border); }

.user-records-empty {
  text-align: center;
  padding: 16px;
  background: var(--bg-app);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: 11px;
}

.ping-section { display: flex; justify-content: space-between; align-items: center; background: var(--warning-bg); border: 1px solid var(--warning-border); padding: 12px 16px; border-radius: var(--radius-lg); }
.ping-info { font-size: var(--text-xs); color: var(--warning-700); display: flex; align-items: center; gap: 8px; font-weight: var(--weight-semibold); }
.btn-ping { background: var(--warning-500); color: white; border: none; padding: 8px 14px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold); cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: var(--sku-btn-primary-shadow); }
.btn-ping:hover:not(:disabled) { background: var(--warning-600); }

.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.form-group label { font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--text-primary); }
.form-group input { padding: 10px 14px; border-radius: var(--radius-md); border: 1px solid rgba(166, 169, 173, 0.55); background: var(--bg-input); box-shadow: var(--neu-inset); font-size: var(--text-xs); font-weight: var(--weight-semibold); outline: none; transition: all var(--duration-fast); color: var(--text-primary); }
.form-group input:focus { border-color: var(--orange-accent); background: var(--bg-input-focus); box-shadow: inset 0 2px 4px rgba(35, 28, 20, 0.08), 0 0 0 3px var(--orange-glow), 0 1px 0 rgba(255, 255, 255, 0.8); }

.role-selector { display: flex; gap: 10px; }
.role-btn-option { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px; border-radius: var(--radius-lg); border: 1px solid rgba(166, 169, 173, 0.4); background: var(--bg-input); box-shadow: var(--neu-btn); cursor: pointer; transition: all var(--duration-fast); color: var(--text-secondary); }
.role-btn-option.active { border-color: var(--orange-accent); background: var(--orange-bg-subtle); color: var(--orange-accent); box-shadow: var(--neu-pressed); }
.role-btn-label { font-size: var(--text-xs); font-weight: var(--weight-bold); }

.alert-box { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: var(--radius-md); font-size: var(--text-xs); font-weight: var(--weight-semibold); }
.alert-box.error { background: var(--error-bg); border: 1px solid var(--error-border); color: var(--error-700); }

.btn-primary { background: var(--orange-gradient); color: white; border: none; padding: 10px 18px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold); cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all var(--duration-base); box-shadow: var(--sku-btn-primary-shadow); }
.btn-primary:hover:not(:disabled) { box-shadow: var(--sku-btn-primary-shadow-hover); transform: translateY(-1px); }

.btn-ghost { background: var(--bg-base); color: var(--text-secondary); border: none; padding: 8px 16px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold); cursor: pointer; transition: all var(--duration-base); box-shadow: var(--sku-btn-secondary-shadow); }
.btn-ghost:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }

.btn-danger { background: var(--error-600); color: white; border: none; padding: 10px 18px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold); cursor: pointer; }
.btn-danger:hover { background: var(--error-700); }

@media (max-width: 900px) { .stats-row { grid-template-columns: repeat(2, 1fr); } }
</style>
