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
              :class="['list-row-wrapper', { 'is-expanded': expandedReqId === req._key }]"
              :style="{ animationDelay: i * 50 + 'ms' }"
            >
              <!-- Collapsed Header -->
              <div class="list-row-header" @click="toggleExpand(req)">
                <!-- Type Icon -->
                <div class="row-icon" :class="req._type">
                  <i :class="typeIcon(req._type)"></i>
                </div>

                <!-- Main Info -->
                <div class="row-info">
                  <div class="row-main">
                    <span class="row-label">
                      <template v-if="req._type !== 'role'">
                        <strong>{{ req.record_id || req.record_name || '—' }}</strong>
                        <span v-if="req.record_name && req.record_id" class="row-record-name"> — {{ req.record_name }}</span>
                      </template>
                      <template v-else>
                        Requested to change role to <strong>{{ req.requested_role ? req.requested_role.toLowerCase() : 'viewer' }}</strong>
                      </template>
                    </span>
                    <span class="row-sub">
                      {{ req._typeLabel }} request
                      &nbsp;·&nbsp;
                      <i class="fas fa-clock"></i>
                      {{ formatDate(req.created_at) }}
                    </span>
                  </div>
                </div>

                <!-- Type Chip -->
                <span :class="['type-chip', req._type]">
                  {{ req._typeLabel }}
                </span>

                <!-- ID -->
                <span class="row-id">#{{ req.id }}</span>

                <!-- Chevron -->
                <button class="expand-chevron-btn" aria-label="Expand request details">
                  <i :class="['fas', expandedReqId === req._key ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                </button>
              </div>

              <!-- Expanded Drawer (Clean & Minimalist) -->
              <transition name="expand">
                <div class="expanded-drawer" v-if="expandedReqId === req._key">
                  
                  <!-- Clean Summary Bar -->
                  <div class="clean-summary-bar">
                    <div class="summary-statement">
                      <i :class="['fas', req._type === 'delete' ? 'fa-trash-alt' : req._type === 'access' ? 'fa-key' : req._type === 'role' ? 'fa-user-shield' : req._type === 'creation' ? 'fa-plus-circle' : 'fa-pen-to-square']"></i>
                      <span>{{ getRequestStatement(req).text }}</span>
                    </div>

                    <!-- Quick Specs Pills Row -->
                    <div class="specs-pills-row">
                      <span class="spec-pill">
                        <i class="fas fa-user-circle"></i> {{ req.user_name || req.requested_by || userState.name || '—' }}
                      </span>
                      <span class="spec-pill mono" v-if="req.user_id || userState.public_id">
                        <i class="fas fa-id-card"></i> {{ req.user_id || userState.public_id }}
                      </span>
                      <span :class="['spec-pill role', (req.user_role || userState.role || 'COLLABORATOR').toLowerCase()]">
                        Current: {{ req.user_role || userState.role || 'COLLABORATOR' }}
                      </span>
                      <span class="spec-pill mono" v-if="req._type !== 'role' && req.record_id">
                        <i class="fas fa-file-lines"></i> {{ req.record_id }}
                      </span>
                      <span :class="['status-pill', req.status.toLowerCase()]">{{ req.status }}</span>
                    </div>
                  </div>

                  <!-- Payload details -->
                  <div v-if="req._type === 'creation'" class="expanded-section">
                    <h4 class="section-heading"><i class="fas fa-file-invoice"></i> Record Specifications</h4>
                    <div class="details-grid-container">
                      <div 
                        v-for="(val, key) in getCreationDetails(req)" 
                        :key="key" 
                        :class="['details-item-card', isLongValue(val) ? 'full-width' : '']"
                      >
                        <div class="item-label">{{ formatFieldName(key) }}</div>
                        <div class="item-value">
                          <span v-if="isMonospaceField(key)" class="monospace-badge">{{ val || '—' }}</span>
                          <div v-else-if="isLongValue(val)" class="long-value-box">{{ val || '—' }}</div>
                          <span v-else-if="val === null || val === undefined || val === ''" class="empty-val">—</span>
                          <span v-else class="val-text">{{ val }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else-if="req._type === 'edit'" class="expanded-section">
                    <h4 class="section-heading"><i class="fas fa-right-left"></i> Proposed Changes</h4>
                    <div class="diff-table-container">
                      <table class="diff-table">
                        <thead>
                          <tr>
                            <th>Field Name</th>
                            <th>Current Value</th>
                            <th>Proposed New Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(val, key) in getProposedChanges(req)" :key="key">
                            <td class="field-name">{{ formatFieldName(key) }}</td>
                            <td class="old-val">
                              <span class="diff-badge old">{{ req.current_data?.[key] || '—' }}</span>
                            </td>
                            <td class="new-val">
                              <span class="diff-badge new">{{ val || '—' }}</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                </div>
              </transition>
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
const expandedReqId = ref<string | null>(null)
const userState = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))

function toggleExpand(req: any) {
  const key = req._key
  expandedReqId.value = expandedReqId.value === key ? null : key
}

function getRequestStatement(req: any) {
  const userName = req.user_name || req.requested_by || userState.value.name || 'User'
  const userId = req.user_id || userState.value.public_id ? `(${req.user_id || userState.value.public_id})` : ''
  const userRole = req.user_role || userState.value.role || 'VIEWER'
  const recordId = req.record_id ? `Record ${req.record_id}` : 'a record'
  const recordName = req.record_name ? ` (${req.record_name})` : ''

  if (req._type === 'role') {
    const targetRole = req.requested_role || 'COLLABORATOR'
    return {
      text: `${userName} ${userId} is requesting a system role change from ${userRole} to ${targetRole}.`,
      typeLabel: 'Role Modification'
    }
  }
  if (req._type === 'access') {
    const access = req.requested_access || 'EDIT'
    return {
      text: `${userName} ${userId} (${userRole}) is requesting ${access} access for ${recordId}${recordName}.`,
      typeLabel: 'Access Upgrade'
    }
  }
  if (req._type === 'creation') {
    return {
      text: `${userName} ${userId} (${userRole}) requested approval to create ${recordId}${recordName}.`,
      typeLabel: 'Record Creation'
    }
  }
  if (req._type === 'edit') {
    return {
      text: `${userName} ${userId} (${userRole}) proposed modifications for ${recordId}${recordName}.`,
      typeLabel: 'Record Modification'
    }
  }
  if (req._type === 'delete') {
    return {
      text: `${userName} ${userId} (${userRole}) requested permanent deletion of ${recordId}${recordName}.`,
      typeLabel: 'Record Deletion'
    }
  }
  return {
    text: `${userName} ${userId} submitted a request.`,
    typeLabel: 'Workflow Request'
  }
}

function isMonospaceField(key: string): boolean {
  return ['employee_code', 'employee_id', 'pan', 'record_id', 'public_id'].includes(String(key).toLowerCase())
}

function isLongValue(val: any): boolean {
  if (typeof val !== 'string') return false
  return val.length > 45
}

function formatFieldName(key: string) {
  const mapping: Record<string, string> = {
    name: 'Full Name', designation: 'Designation', employee_code: 'Employee Code',
    pan: 'PAN', source_company: 'Disclosure Company', info_details: 'Information Details',
    info_received_date: 'Date Received', disclosure_name: 'Disclosure Name',
    disclosure_designation: 'Disclosure Designation', disclosure_department: 'Disclosure Department',
    created_by_name: 'Created By Name', updated_by_name: 'Updated By Name', access_type: 'Access Type'
  }
  if (mapping[key]) return mapping[key]
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function getCreationDetails(req: any) {
  const details: Record<string, any> = {}
  if (!req.current_data) return details
  for (const key of Object.keys(req.current_data)) {
    if (['id','public_id','created_by','updated_by','created_at','updated_at','status','access_type','access_list'].includes(key)) continue
    details[key] = req.current_data[key]
  }
  return details
}

function getProposedChanges(req: any) {
  const changes: Record<string, any> = {}
  if (!req.proposed_data) return changes
  for (const key of Object.keys(req.proposed_data)) {
    if (['id','public_id','created_by','updated_by','created_at','updated_at','status','access_type','access_list'].includes(key)) continue
    if (req.proposed_data[key] !== req.current_data?.[key]) changes[key] = req.proposed_data[key]
  }
  return changes
}

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

/* Expandable Rows */
.list-row-wrapper {
  border-bottom: 1px solid var(--card-divider);
  transition: background var(--duration-fast), border-color var(--duration-fast);
}
.list-row-wrapper:last-child {
  border-bottom: none;
}
.list-row-wrapper.is-expanded {
  background: rgba(234, 108, 0, 0.03);
}

.list-row-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
  transition: background var(--duration-fast);
}
.list-row-header:hover {
  background: rgba(234, 108, 0, 0.06);
}

.row-record-name {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: normal;
}

.expand-chevron-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: all var(--duration-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}
.list-row-header:hover .expand-chevron-btn {
  color: var(--orange-accent);
}

/* Expanded Drawer */
.expanded-drawer {
  padding: 0 20px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-top: 1px dashed rgba(234, 108, 0, 0.2);
  margin-top: 4px;
  animation: slideDown 0.25s ease-out forwards;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Clean Summary Bar */
.clean-summary-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 18px;
  border-radius: var(--radius-xl);
  background: var(--bg-card);
  border: 1px solid rgba(166, 169, 173, 0.25);
  box-shadow: var(--neu-inset);
  margin-top: 10px;
}

.summary-statement {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
  line-height: 1.4;
}

.summary-statement i {
  color: var(--orange-accent);
  font-size: 16px;
  flex-shrink: 0;
}

.specs-pills-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.spec-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: var(--weight-bold);
  background: var(--bg-base);
  color: var(--text-secondary);
  border: 1px solid rgba(166, 169, 173, 0.25);
}

.spec-pill i {
  color: var(--orange-accent);
  font-size: 11px;
}

.spec-pill.mono {
  font-family: 'Courier New', Consolas, monospace;
  font-weight: 700;
  color: var(--text-primary);
}

.spec-pill.role {
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.4px;
}
.spec-pill.role.collaborator { background: var(--orange-bg-subtle); color: var(--orange-accent); border-color: var(--orange-border); }
.spec-pill.role.viewer { background: var(--info-bg); color: var(--info-700); border-color: var(--info-border); }

.status-pill {
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}
.status-pill.pending  { background: var(--warning-bg); color: var(--warning-700); }
.status-pill.approved { background: var(--success-bg); color: var(--success-700); }
.status-pill.rejected { background: var(--error-bg);   color: var(--error-700); }

/* Details Grid Container */
.details-grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  background: var(--bg-content);
  padding: 12px;
  border-radius: var(--radius-xl);
  box-shadow: var(--neu-inset);
  border: 1px solid rgba(166, 169, 173, 0.3);
  margin-top: 10px;
}

.details-item-card {
  background: var(--bg-card);
  border: 1px solid rgba(166, 169, 173, 0.25);
  border-radius: var(--radius-lg);
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  box-shadow: var(--shadow-xs);
}

.details-item-card.full-width {
  grid-column: 1 / -1;
}

.item-label {
  font-size: 9.5px;
  font-weight: 800;
  color: var(--neutral-600);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

.item-value {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
  word-break: break-word;
}

.long-value-box {
  background: var(--bg-app);
  border: 1px solid rgba(166, 169, 173, 0.3);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  font-size: 11px;
  line-height: 1.45;
  color: var(--text-primary);
  font-weight: var(--weight-medium);
  box-shadow: var(--neu-inset);
  margin-top: 2px;
}

.empty-val {
  color: var(--neutral-400);
  font-weight: normal;
}

/* Diff Table Styling */
.diff-table-container {
  margin-top: 10px;
  background: var(--bg-content);
  border: 1px solid rgba(166, 169, 173, 0.4);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--neu-inset);
}
.diff-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: var(--text-xs);
  text-align: left;
}
.diff-table th {
  background: var(--bg-base);
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(166, 169, 173, 0.35);
}
.diff-table td {
  padding: 12px 14px;
  border-bottom: 1px dashed rgba(166, 169, 173, 0.25);
  vertical-align: middle;
}
.diff-table tr:last-child td {
  border-bottom: none;
}
.diff-table .field-name {
  font-weight: 700;
  color: var(--text-primary);
  width: 28%;
}
.diff-table .old-val, .diff-table .new-val {
  width: 36%;
}
.diff-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  word-break: break-word;
  max-width: 100%;
  line-height: 1.4;
}
.diff-badge.old {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border: 1px solid rgba(239, 68, 68, 0.3);
  text-decoration: line-through;
  font-weight: 600;
}
.diff-badge.new {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #166534;
  border: 1px solid rgba(34, 197, 94, 0.3);
  font-weight: 700;
  box-shadow: 0 1px 4px rgba(34, 197, 94, 0.15);
}

.section-heading {
  font-size: var(--text-xs);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-secondary);
  margin-top: 10px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 640px) {
  .tab-bar { width: 100%; }
  .tab-btn { flex: 1; justify-content: center; }
  .row-date, .row-id { display: none; }
  .details-grid-container { grid-template-columns: 1fr; }
}
</style>
