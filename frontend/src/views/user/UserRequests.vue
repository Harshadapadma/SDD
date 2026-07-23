<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">My Requests</h1>
        <p class="page-sub">Track real-time status of your submitted system and record requests</p>
      </div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Fetching your requests...
    </div>

    <template v-else>
      <!-- TAB TOGGLE -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-btn', { active: activeTab === tab.key }]"
          :data-tab="tab.key"
          @click="activeTab = tab.key"
        >
          <i :class="tab.icon"></i>
          <span>{{ tab.label }}</span>
          <span class="tab-count" :class="tab.key">{{ tab.count }}</span>
        </button>
      </div>

      <!-- REQUEST LIST -->
      <div class="request-list">
        <transition name="fade-slide" mode="out-in">

          <!-- EMPTY STATE -->
          <div class="empty-state" v-if="activeList.length === 0" :key="'empty-' + activeTab">
            <div class="empty-icon-wrap" :class="activeTab">
              <i :class="['fas', activeTab === 'pending' ? 'fa-hourglass-half' : activeTab === 'approved' ? 'fa-circle-check' : 'fa-circle-xmark']"></i>
            </div>
            <p class="empty-title">No {{ activeTab }} requests</p>
            <p class="empty-sub">You don't have any {{ activeTab }} requests at the moment.</p>
          </div>

          <!-- LIST ROWS (Neomorphism) -->
          <div class="list-container" v-else :key="'list-' + activeTab">
            <div
              v-for="(req, i) in activeList"
              :key="req._key"
              class="list-row"
              :style="{ animationDelay: i * 50 + 'ms' }"
            >
              <!-- Type Icon -->
              <div class="row-icon" :class="req._type">
                <i :class="typeIcon(req._type)"></i>
              </div>

              <!-- Main Info -->
              <div class="row-info">
                <div class="row-main">
                  <span class="row-label">
                    <template v-if="req._type !== 'role'">
                      {{ req.record_id || req.record_name || '—' }}
                    </template>
                    <template v-else>
                      Requested to change role to {{ req.requested_role ? req.requested_role.toLowerCase() : 'viewer' }}
                    </template>
                  </span>
                  <span class="row-sub" v-if="req._type === 'access'">
                    Requesting <strong>{{ req.requested_access }}</strong> access
                  </span>
                  <span class="row-sub" v-else-if="req._type === 'role'">
                    System role modification request
                  </span>
                  <span class="row-sub" v-else>
                    {{ req._typeLabel }} request
                  </span>
                </div>
              </div>

              <!-- Type Chip -->
              <span :class="['type-chip', req._type]">
                {{ req._typeLabel }}
              </span>

              <!-- Date -->
              <div class="row-date">
                <i class="fas fa-clock"></i>
                <span>{{ formatDate(req.created_at) }}</span>
              </div>

              <!-- ID -->
              <span class="row-id">#{{ req.id }}</span>
            </div>
          </div>

        </transition>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../../api/client'

const loading = ref(true)
const activeTab = ref<'pending' | 'approved' | 'rejected'>('pending')

const data = ref<any>({
  delete_requests: [],
  role_requests: [],
  access_requests: [],
  creation_requests: [],
  edit_requests: []
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
  const del      = (data.value.delete_requests   || []).map((r: any) => ({ ...r, _type: 'delete',   _typeLabel: 'Deletion',    _key: 'del-'    + r.id }))
  const role     = (data.value.role_requests     || []).map((r: any) => ({ ...r, _type: 'role',     _typeLabel: 'Role Change', _key: 'role-'   + r.id }))
  const acc      = (data.value.access_requests   || []).map((r: any) => ({ ...r, _type: 'access',   _typeLabel: 'Access',      _key: 'acc-'    + r.id }))
  const creation = (data.value.creation_requests || []).map((r: any) => ({ ...r, _type: 'creation', _typeLabel: 'Creation',    _key: 'create-' + r.id }))
  const edit     = (data.value.edit_requests     || []).map((r: any) => ({ ...r, _type: 'edit',     _typeLabel: 'Edit',        _key: 'edit-'   + r.id }))
  return [...del, ...role, ...acc, ...creation, ...edit]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const pendingRequests  = computed(() => allRequests.value.filter(r => r.status === 'PENDING'))
const approvedRequests = computed(() => allRequests.value.filter(r => r.status === 'APPROVED'))
const rejectedRequests = computed(() => allRequests.value.filter(r => r.status === 'REJECTED'))

const activeList = computed(() => {
  if (activeTab.value === 'pending')  return pendingRequests.value
  if (activeTab.value === 'approved') return approvedRequests.value
  return rejectedRequests.value
})

const tabs = computed<{ key: 'pending' | 'approved' | 'rejected', label: string, icon: string, count: number }[]>(() => [
  { key: 'pending',  label: 'Pending',  icon: 'fas fa-hourglass-half', count: pendingRequests.value.length  },
  { key: 'approved', label: 'Approved', icon: 'fas fa-circle-check',   count: approvedRequests.value.length },
  { key: 'rejected', label: 'Rejected', icon: 'fas fa-circle-xmark',   count: rejectedRequests.value.length },
])

function typeIcon(type: string) {
  const map: Record<string, string> = {
    creation: 'fas fa-plus-circle',
    delete:   'fas fa-trash-alt',
    edit:     'fas fa-pen-to-square',
    access:   'fas fa-key',
    role:     'fas fa-user-shield',
  }
  return map[type] || 'fas fa-circle'
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchRequests)
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title  { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub    { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

.loading-state {
  display: flex; align-items: center; justify-content: center;
  padding: 48px 24px; color: var(--orange-accent); gap: 10px;
  font-size: var(--text-sm); font-weight: var(--weight-bold);
}

/* Tab Bar */
.tab-bar {
  display: flex; gap: 6px;
  background: var(--bg-app); border-radius: var(--radius-xl);
  padding: 4px; width: fit-content; box-shadow: var(--neu-inset);
}

.tab-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; border: none; border-radius: var(--radius-lg);
  font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-secondary);
  background: transparent; cursor: pointer; transition: all var(--duration-fast);
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow); color: var(--text-primary); }
.tab-btn.active[data-tab="pending"]  { color: var(--warning-700); }
.tab-btn.active[data-tab="approved"] { color: var(--success-700); }
.tab-btn.active[data-tab="rejected"] { color: var(--error-700); }

.tab-count {
  min-width: 20px; height: 20px; border-radius: var(--radius-pill); font-size: 10px; font-weight: var(--weight-bold);
  display: inline-flex; align-items: center; justify-content: center; padding: 0 6px;
}
.tab-count.pending  { background: var(--warning-bg); color: var(--warning-700); }
.tab-count.approved { background: var(--success-bg); color: var(--success-700); }
.tab-count.rejected { background: var(--error-bg);   color: var(--error-700); }

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px 24px; gap: 10px; text-align: center;
}
.empty-icon-wrap {
  width: 56px; height: 56px; border-radius: var(--radius-xl);
  display: flex; align-items: center; justify-content: center; font-size: 24px;
}
.empty-icon-wrap.pending  { background: var(--warning-bg); color: var(--warning-600); }
.empty-icon-wrap.approved { background: var(--success-bg); color: var(--success-600); }
.empty-icon-wrap.rejected { background: var(--error-bg);   color: var(--error-600); }

.empty-title { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.empty-sub   { font-size: var(--text-xs); color: var(--text-secondary); margin: 0; max-width: 280px; }

/* List Container (Neomorphism) */
.list-container {
  background: var(--bg-base);
  border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card);
  overflow: hidden;
}

.list-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--card-divider);
  transition: background var(--duration-fast);
}
.list-row:last-child { border-bottom: none; }
.list-row:hover { background: rgba(234, 108, 0, 0.06); }

.row-icon {
  width: 40px; height: 40px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-base); flex-shrink: 0;
}
.row-icon.creation { background: var(--info-bg);    color: var(--info-600); }
.row-icon.delete   { background: var(--error-bg);   color: var(--error-600); }
.row-icon.edit     { background: var(--warning-bg); color: var(--warning-600); }
.row-icon.access   { background: var(--success-bg); color: var(--success-600); }
.row-icon.role     { background: var(--orange-bg-subtle); color: var(--orange-accent); }

.row-info { flex: 1; min-width: 0; }
.row-main { display: flex; flex-direction: column; gap: 2px; }
.row-label {
  font-size: var(--text-sm); font-weight: var(--weight-bold); color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.row-sub { font-size: var(--text-xs); color: var(--text-secondary); }
.row-sub strong { color: var(--text-primary); font-weight: var(--weight-bold); }

.type-chip {
  padding: 3px 8px; border-radius: var(--radius-xs); font-size: 10px; font-weight: var(--weight-bold);
  text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
.type-chip.creation { background: var(--info-bg); color: var(--info-700); border: 1px solid var(--info-border); }
.type-chip.delete   { background: var(--error-bg); color: var(--error-700); border: 1px solid var(--error-border); }
.type-chip.edit     { background: var(--warning-bg); color: var(--warning-700); border: 1px solid var(--warning-border); }
.type-chip.access   { background: var(--success-bg); color: var(--success-700); border: 1px solid var(--success-border); }
.type-chip.role     { background: var(--orange-bg-subtle); color: var(--orange-accent); border: 1px solid var(--orange-border); }

.row-date {
  display: flex; align-items: center; gap: 6px;
  font-size: var(--text-xs); color: var(--text-secondary); font-weight: var(--weight-medium);
  white-space: nowrap; flex-shrink: 0;
}
.row-date i { color: var(--orange-accent); font-size: 11px; }

.row-id {
  font-family: monospace; font-size: 11px; font-weight: var(--weight-bold); color: var(--neutral-700);
  background: var(--neutral-100); border: 1px solid var(--neutral-200);
  padding: 2px 8px; border-radius: var(--radius-xs); flex-shrink: 0;
}

@media (max-width: 640px) {
  .tab-bar { width: 100%; }
  .tab-btn { flex: 1; justify-content: center; }
  .row-date, .row-id { display: none; }
}
</style>
