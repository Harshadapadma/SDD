<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Workflow Requests</h1>
        <p class="page-sub">Review, discuss, and process record changes, system role requests, and access modifications</p>
      </div>
      <div class="header-metrics">
        <div class="metric-chip yellow">
          <span class="dot yellow"></span>
          <strong>{{ pendingRequests.length }}</strong> Pending
        </div>
        <div class="metric-chip green">
          <span class="dot green"></span>
          <strong>{{ pendingRequests.filter(r => r.type === 'CREATION').length }}</strong> Creations
        </div>
        <div class="metric-chip blue">
          <span class="dot blue"></span>
          <strong>{{ pendingRequests.filter(r => r.type === 'EDIT').length }}</strong> Editions
        </div>
      </div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Fetching workflow requests…
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
            <p class="empty-sub">
              {{ activeTab === 'pending' ? 'All caught up! No pending requests at the moment.' : `No requests have been ${activeTab} yet.` }}
            </p>
          </div>

          <!-- LIST ROWS (Neomorphism) -->
          <div class="list-container" v-else :key="'list-' + activeTab">
            <div
              v-for="(req, i) in activeList"
              :key="req.type + req.id"
              :class="['list-row-wrapper', { 'is-expanded': expandedReqId === getReqKey(req) }]"
              :style="{ animationDelay: i * 50 + 'ms' }"
            >
              <!-- Collapsed Row Header -->
              <div class="list-row-header" @click="toggleExpand(req)">
                <!-- Type Icon -->
                <div class="row-icon" :class="req.type.toLowerCase()">
                  <i :class="typeIcon(req.type)"></i>
                </div>

                <!-- Main Info -->
                <div class="row-info">
                  <div class="row-label">
                    <template v-if="req.type === 'ROLE'">
                      <strong>{{ req.user_name || req.requested_by || 'User' }}</strong> requested to change role to <strong>{{ req.requested_role ? req.requested_role.toLowerCase() : 'viewer' }}</strong>
                    </template>
                    <template v-else>
                      <strong>{{ 'Record ' + (req.record_id || req.id) }}</strong>
                      <span v-if="req.record_name" class="row-record-name"> — {{ req.record_name }}</span>
                    </template>
                  </div>
                  <div class="row-sub">
                    <span class="user-pill"><i class="fas fa-user-circle"></i> {{ req.user_name || req.requested_by || 'User' }}</span>
                    <span class="uid-pill" v-if="req.user_id"><i class="fas fa-id-card"></i> {{ req.user_id }}</span>
                    &nbsp;·&nbsp;
                    <i class="fas fa-clock"></i>
                    {{ formatDate(req.created_at) }}
                  </div>
                </div>

                <!-- Type Chip -->
                <span :class="['type-chip', req.type.toLowerCase()]">
                  {{ req.type === 'DELETE' ? 'Deletion' : req.type === 'ACCESS' ? 'Access' : req.type === 'ROLE' ? 'Role' : req.type === 'CREATION' ? 'Creation' : 'Edition' }}
                </span>

                <!-- ID badge -->
                <span class="row-id">#{{ req.id }}</span>

                <!-- Chevron Icon -->
                <button class="expand-chevron-btn" aria-label="Expand request details">
                  <i :class="['fas', expandedReqId === getReqKey(req) ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                </button>

                <!-- Actions (pending only) -->
                <div class="row-actions" v-if="activeTab === 'pending'">
                  <button class="action-pill approve" @click.stop="review(req, 'APPROVE')" :disabled="reviewing === req.type + req.id">
                    <i class="fas fa-check"></i> Approve
                  </button>
                  <button class="action-pill reject" @click.stop="review(req, 'REJECT')" :disabled="reviewing === req.type + req.id">
                    <i class="fas fa-times"></i> Reject
                  </button>
                  <button v-if="req.type === 'CREATION'" class="action-pill chat" @click.stop="review(req, 'REVIEW')">
                    <i class="fas fa-comments"></i> Review
                  </button>
                </div>
              </div>

              <!-- Expanded Drawer (Clean & Minimalist) -->
              <transition name="expand">
                <div class="expanded-drawer" v-if="expandedReqId === getReqKey(req)">
                  
                  <!-- Clean Summary Bar -->
                  <div class="clean-summary-bar">
                    <div class="summary-statement">
                      <i :class="['fas', req.type === 'DELETE' ? 'fa-trash-alt' : req.type === 'ACCESS' ? 'fa-key' : req.type === 'ROLE' ? 'fa-user-shield' : req.type === 'CREATION' ? 'fa-plus-circle' : 'fa-pen-to-square']"></i>
                      <span>{{ getRequestStatement(req).text }}</span>
                    </div>

                    <!-- Quick Specs Pills Row -->
                    <div class="specs-pills-row">
                      <span class="spec-pill">
                        <i class="fas fa-user-circle"></i> {{ req.user_name || req.requested_by || '—' }}
                      </span>
                      <span class="spec-pill mono" v-if="req.user_id">
                        <i class="fas fa-id-card"></i> {{ req.user_id }}
                      </span>
                      <span :class="['spec-pill role', (req.user_role || 'COLLABORATOR').toLowerCase()]">
                        Current: {{ req.user_role || 'COLLABORATOR' }}
                      </span>
                      <span class="spec-pill mono" v-if="req.type !== 'ROLE' && req.record_id">
                        <i class="fas fa-file-lines"></i> {{ req.record_id }}
                      </span>
                    </div>
                  </div>

                  <!-- Payloads -->

                  <!-- CREATION DETAILS -->
                  <div v-if="req.type === 'CREATION'" class="expanded-section">
                    <div class="section-header-flex">
                      <h4 class="section-heading"><i class="fas fa-file-invoice"></i> Proposed Record Creation Details</h4>
                      <button class="action-pill chat sm" @click.stop="review(req, 'REVIEW')">
                        <i class="fas fa-comments"></i> Clarification History
                      </button>
                    </div>
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

                  <!-- EDIT DETAILS -->
                  <div v-else-if="req.type === 'EDIT'" class="expanded-section">
                    <h4 class="section-heading"><i class="fas fa-right-left"></i> Proposed Changes</h4>
                    <div class="diff-table-container">
                      <table class="diff-table">
                        <thead>
                          <tr>
                            <th>Field</th>
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

                  <!-- ACCESS WARNING (Viewer) -->
                  <div v-else-if="req.type === 'ACCESS' && req.user_role === 'VIEWER'" class="expanded-section">
                    <div class="viewer-warning-banner">
                      <i class="fas fa-exclamation-triangle"></i>
                      <span><strong>Role Restriction:</strong> Viewers cannot be assigned EDIT access until promoted to Collaborator.</span>
                    </div>
                  </div>

                  <!-- DELETE WARNING -->
                  <div v-else-if="req.type === 'DELETE'" class="expanded-section">
                    <div class="danger-banner">
                      <i class="fas fa-triangle-exclamation"></i>
                      <span>Permanently erases Record <strong>{{ req.record_id }}</strong> and all associated access permissions.</span>
                    </div>
                  </div>

                </div>
              </transition>
            </div>
          </div>

        </transition>
      </div>
    </template>

    <!-- CONFIRM / REVIEW MODAL (Glassmorphism Overlay) -->
    <teleport to="body">
    <div class="modal-overlay" v-if="confirmModal" @click.self="confirmModal = null">
      <div :class="['modal', (confirmModal.req.type === 'EDIT' || confirmModal.req.type === 'CREATION') ? 'modal-lg' : 'modal-sm']">
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon-wrap" :class="confirmModal.action.toLowerCase()">
              <i :class="['fas', confirmModal.action === 'APPROVE' ? 'fa-circle-check' : confirmModal.action === 'REJECT' ? 'fa-circle-xmark' : 'fa-clipboard-check']"></i>
            </div>
            <h2>{{ confirmModal.action === 'APPROVE' ? 'Approve Request' : confirmModal.action === 'REJECT' ? 'Reject Request' : 'Review Request Details' }}</h2>
          </div>
          <button class="modal-close" @click="confirmModal = null" aria-label="Close"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="confirm-text">
            <span v-if="confirmModal.action === 'APPROVE' && confirmModal.req.type === 'DELETE'">
              This will <strong>permanently delete</strong> the record. This action cannot be undone.
            </span>
            <span v-else-if="confirmModal.action === 'APPROVE' && confirmModal.req.type === 'ROLE'">
              This will upgrade the user's permissions to <strong>{{ confirmModal.req.requested_role }}</strong>.
            </span>
            <span v-else-if="confirmModal.req.type === 'ACCESS'">
              <div v-if="confirmModal.action === 'APPROVE' && confirmModal.req.user_role === 'VIEWER'" class="viewer-warning-banner">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                  <strong>Role Restriction Alert:</strong>
                  <p>User <strong>{{ confirmModal.req.user_name || confirmModal.req.user_id }}</strong> is currently a <strong>VIEWER</strong>. To get full edit access, the user has to be a <strong>COLLABORATOR</strong>.</p>
                </div>
              </div>
              <span v-else-if="confirmModal.action === 'APPROVE'">
                This will grant the user <strong>EDIT</strong> access to record <strong>{{ confirmModal.req.record_id }}</strong>.
              </span>
              <span v-else>
                This will reject the access upgrade request for record <strong>{{ confirmModal.req.record_id }}</strong>.
              </span>
            </span>
            <span v-else-if="confirmModal.req.type === 'CREATION'">
              <div class="split-view">
                <div class="split-left">
                  <span v-if="confirmModal.action === 'APPROVE'">
                    This will <strong>approve</strong> the creation of record <strong>{{ confirmModal.req.record_id }}</strong> with the following details:
                  </span>
                  <span v-else-if="confirmModal.action === 'REJECT'">
                    This will <strong>reject and discard</strong> the creation of record <strong>{{ confirmModal.req.record_id }}</strong>.
                  </span>
                  <span v-else>
                    Reviewing details for creation request of record <strong>{{ confirmModal.req.record_id }}</strong>:
                  </span>
                  <div class="details-grid-container">
                    <div 
                      v-for="(val, key) in getCreationDetails(confirmModal.req)" 
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
                <div class="split-right">
                  <h3><i class="fas fa-comments"></i> Clarification History</h3>
                  <div class="chat-messages-container" ref="chatMessagesRef">
                    <div v-if="loadingMessages" class="chat-loading"><i class="fas fa-spinner fa-spin"></i> Loading messages...</div>
                    <div v-else-if="messages.length === 0" class="chat-empty">No clarifications requested yet.</div>
                    <div v-else class="chat-bubble-list">
                      <div v-for="msg in messages" :key="msg.id" :class="['chat-bubble-wrap', msg.is_me ? 'me' : 'them']">
                        <div class="bubble-sender">{{ formatSender(msg) }}</div>
                        <div class="bubble-text">{{ msg.message }}</div>
                        <div class="bubble-time">{{ formatTime(msg.created_at) }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="chat-input-wrap" v-if="confirmModal.req.status === 'PENDING'">
                    <textarea v-model="newMessage" placeholder="Ask a doubt about details..." @keyup.enter.exact.prevent="sendMessage(confirmModal.req.id)"></textarea>
                    <button class="chat-send-btn" @click="sendMessage(confirmModal.req.id)">
                      <i class="fas fa-paper-plane"></i>
                    </button>
                  </div>
                  <div class="chat-closed-notice" v-else>
                    <i class="fas fa-lock"></i> Chat is closed for this request
                  </div>
                </div>
              </div>
            </span>
            <span v-else-if="confirmModal.req.type === 'EDIT'">
              <span v-if="confirmModal.action === 'APPROVE'">
                This will <strong>apply the following edits</strong> to record <strong>{{ confirmModal.req.record_id }}</strong>:
              </span>
              <span v-else-if="confirmModal.action === 'REJECT'">
                This will <strong>reject</strong> the proposed edits for record <strong>{{ confirmModal.req.record_id }}</strong>.
              </span>
              <span v-else>
                Reviewing proposed changes for record <strong>{{ confirmModal.req.record_id }}</strong>:
              </span>
              <div class="diff-table-container">
                <table class="diff-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Current Value</th>
                      <th>Proposed Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(val, key) in getProposedChanges(confirmModal.req)" :key="key">
                      <td class="field-name">{{ formatFieldName(key) }}</td>
                      <td class="old-val">
                        <span class="diff-badge old">{{ confirmModal.req.current_data?.[key] || '—' }}</span>
                      </td>
                      <td class="new-val">
                        <span class="diff-badge new">{{ val || '—' }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </span>
            <span v-else>The request will be rejected and the user will be notified.</span>
          </div>
        </div>
        <div class="modal-footer" v-if="confirmModal.action === 'REVIEW'">
          <button class="btn-ghost" @click="confirmModal = null">Close</button>
          <button class="btn-danger" @click="doReviewWithAction('REJECT')" :disabled="reviewing !== null">
            <i class="fas fa-spinner fa-spin" v-if="reviewing"></i>
            <i class="fas fa-circle-xmark" v-else></i>
            <span>Reject Request</span>
          </button>
          <button class="btn-accept" @click="doReviewWithAction('APPROVE')" :disabled="reviewing !== null">
            <i class="fas fa-spinner fa-spin" v-if="reviewing"></i>
            <i class="fas fa-circle-check" v-else></i>
            <span>Accept Request</span>
          </button>
        </div>
        <div class="modal-footer" v-else>
          <button class="btn-ghost" @click="confirmModal = null">Cancel</button>
          <button
            :class="confirmModal.action === 'APPROVE' ? 'btn-primary' : 'btn-danger'"
            @click="doReview"
            :disabled="reviewing !== null || (confirmModal.action === 'APPROVE' && confirmModal.req.type === 'ACCESS' && confirmModal.req.user_role === 'VIEWER')"
          >
            {{ reviewing !== null ? 'Processing…' : confirmModal.action === 'APPROVE' ? (confirmModal.req.type === 'DELETE' ? 'Yes, Delete' : 'Approve') : 'Reject' }}
          </button>
        </div>
      </div>
    </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const { notify, fetchNotifications } = useNotifications()
const chatMessagesRef = ref<HTMLDivElement | null>(null)
const requests  = ref<any[]>([])
const loading   = ref(false)
const reviewing = ref<string | null>(null)
const activeTab = ref<'pending' | 'approved' | 'rejected'>('pending')
const expandedReqId = ref<string | null>(null)

function getReqKey(req: any): string {
  return `${req.type || req._type}-${req.id}`
}

function toggleExpand(req: any) {
  const key = getReqKey(req)
  expandedReqId.value = expandedReqId.value === key ? null : key
  if (req.type === 'CREATION' && expandedReqId.value === key) {
    fetchMessages(req.id)
  }
}

function getRequestStatement(req: any) {
  const userName = req.user_name || req.requested_by || 'User'
  const userId = req.user_id ? `(${req.user_id})` : ''
  const userRole = req.user_role || 'VIEWER'
  const recordId = req.record_id ? `Record ${req.record_id}` : 'a record'
  const recordName = req.record_name ? ` (${req.record_name})` : ''

  if (req.type === 'ROLE') {
    const targetRole = req.requested_role || 'COLLABORATOR'
    return {
      text: `${userName} ${userId} is requesting a system role change from ${userRole} to ${targetRole}.`,
      typeLabel: 'Role Modification'
    }
  }
  if (req.type === 'ACCESS') {
    const access = req.requested_access || 'EDIT'
    return {
      text: `${userName} ${userId} (${userRole}) is requesting ${access} access for ${recordId}${recordName}.`,
      typeLabel: 'Access Upgrade'
    }
  }
  if (req.type === 'CREATION') {
    return {
      text: `${userName} ${userId} (${userRole}) requested approval to create ${recordId}${recordName}.`,
      typeLabel: 'Record Creation'
    }
  }
  if (req.type === 'EDIT') {
    return {
      text: `${userName} ${userId} (${userRole}) proposed modifications for ${recordId}${recordName}.`,
      typeLabel: 'Record Modification'
    }
  }
  if (req.type === 'DELETE') {
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

const pendingRequests  = computed(() => requests.value.filter(r => r.status === 'PENDING'))
const approvedRequests = computed(() => requests.value.filter(r => r.status === 'APPROVED'))
const rejectedRequests = computed(() => requests.value.filter(r => r.status === 'REJECTED'))

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
    CREATION: 'fas fa-plus-circle',
    DELETE:   'fas fa-trash-alt',
    EDIT:     'fas fa-pen-to-square',
    ACCESS:   'fas fa-key',
    ROLE:     'fas fa-user-shield',
  }
  return map[type] || 'fas fa-circle'
}

async function fetchRequests() {
  loading.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    let reqsList: any[] = []
    if (user.role === 'COMPLIANCE_OFFICER') {
      const [delRes, createRes, editRes, roleRes, accRes] = await Promise.all([
        api.get('workflows/'),
        api.get('workflows/creation/'),
        api.get('workflows/edit/'),
        api.get('workflows/role-change/'),
        api.get('workflows/access-upgrade/')
      ])
      reqsList = [
        ...delRes.data.map((r: any) => ({ ...r, type: 'DELETE' })),
        ...createRes.data.map((r: any) => ({ ...r, type: 'CREATION' })),
        ...editRes.data.map((r: any) => ({ ...r, type: 'EDIT' })),
        ...roleRes.data.map((r: any) => ({ ...r, type: 'ROLE' })),
        ...accRes.data.map((r: any) => ({ ...r, type: 'ACCESS' })),
      ]
    }
    requests.value = reqsList.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function formatSender(msg: any) {
  if (msg.is_me) return 'Me'
  if (msg.sender_role === 'COMPLIANCE_OFFICER' || msg.sender_role === 'ADMIN') return 'Compliance Officer'
  return msg.sender_name || 'Collaborator'
}

function formatDate(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Review ────────────────────────────────────────────────────
const confirmModal    = ref<{ req: any, action: string } | null>(null)
const messages        = ref<any[]>([])
const newMessage      = ref('')
const loadingMessages = ref(false)

function scrollToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

async function fetchMessages(reqId: number) {
  loadingMessages.value = true
  try {
    const res = await api.get(`workflows/creation/${reqId}/clarification/`)
    messages.value = res.data
    scrollToBottom()
  } catch (e) { console.error(e) }
  finally { loadingMessages.value = false }
}

async function sendMessage(reqId: number) {
  if (!newMessage.value.trim()) return
  try {
    const res = await api.post(`workflows/creation/${reqId}/clarification/`, { message: newMessage.value.trim() })
    messages.value.push(res.data)
    newMessage.value = ''
    scrollToBottom()
  } catch (e) { console.error(e) }
}

function review(req: any, action: string) {
  confirmModal.value = { req, action }
  if (req.type === 'CREATION') fetchMessages(req.id)
}

async function doReviewWithAction(action: string) {
  if (!confirmModal.value) return
  confirmModal.value.action = action
  await doReview()
}

function formatTime(d: string) {
  if (!d) return '—'
  return new Date(d).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

async function doReview() {
  if (!confirmModal.value) return
  const req    = confirmModal.value.req
  const action = confirmModal.value.action
  reviewing.value = req.type + req.id
  const endpoint =
    req.type === 'DELETE'   ? `workflows/review/${req.id}/` :
    req.type === 'ROLE'     ? `workflows/role-change/review/${req.id}/` :
    req.type === 'CREATION' ? `workflows/creation/review/${req.id}/` :
    req.type === 'EDIT'     ? `workflows/edit/review/${req.id}/` :
                              `workflows/access-upgrade/review/${req.id}/`
  try {
    await api.post(endpoint, { action })
    notify(
      action === 'APPROVE' ? 'Request Approved' : 'Request Rejected',
      `Workflow request #${req.id} has been ${action.toLowerCase()}d.`,
      action === 'APPROVE' ? 'SUCCESS' : 'INFO'
    )
    confirmModal.value = null
    fetchRequests()
    fetchNotifications()
  } catch (e) {
    console.error(e)
    notify('Review Failed', 'Failed to process request.', 'ERROR')
  } finally {
    reviewing.value = null
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

function getProposedChanges(req: any) {
  const changes: Record<string, any> = {}
  if (!req.proposed_data) return changes
  for (const key of Object.keys(req.proposed_data)) {
    if (['id','public_id','created_by','updated_by','created_at','updated_at','status','access_type','access_list'].includes(key)) continue
    if (req.proposed_data[key] !== req.current_data?.[key]) changes[key] = req.proposed_data[key]
  }
  return changes
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

onMounted(fetchRequests)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 16px; }
.page-title  { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub    { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

.header-metrics { display: flex; gap: 10px; }
.metric-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold);
  background: var(--bg-base); box-shadow: var(--neu-btn); color: var(--text-secondary);
}
.metric-chip strong { color: var(--text-primary); }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.yellow { background: var(--warning-500); }
.dot.green  { background: var(--success-500); }
.dot.blue   { background: var(--info-500); }

.loading-state { text-align: center; padding: 48px 24px; color: var(--orange-accent); font-size: var(--text-sm); font-weight: var(--weight-bold); }

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
.empty-sub   { font-size: var(--text-xs); color: var(--text-secondary); margin: 0; max-width: 320px; }

/* List Row */
.list-container {
  background: var(--bg-base); border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card); overflow: hidden;
}

.list-row {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; border-bottom: 1px solid var(--card-divider);
  transition: background var(--duration-fast);
}
.list-row:last-child { border-bottom: none; }
.list-row:hover { background: rgba(234, 108, 0, 0.06); }

.row-icon {
  width: 40px; height: 40px; border-radius: var(--radius-lg); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: var(--text-base);
}
.row-icon.creation { background: var(--info-bg);    color: var(--info-600); }
.row-icon.delete   { background: var(--error-bg);   color: var(--error-600); }
.row-icon.edit     { background: var(--warning-bg); color: var(--warning-600); }
.row-icon.access   { background: var(--success-bg); color: var(--success-600); }
.row-icon.role     { background: var(--orange-bg-subtle); color: var(--orange-accent); }

.row-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.row-label { font-size: var(--text-sm); font-weight: var(--weight-bold); color: var(--text-primary); }
.row-sub { font-size: var(--text-xs); color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.row-sub i { color: var(--orange-accent); font-size: 11px; }

.type-chip {
  padding: 3px 8px; border-radius: var(--radius-xs); font-size: 10px; font-weight: var(--weight-bold);
  text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
.type-chip.creation { background: var(--info-bg); color: var(--info-700); border: 1px solid var(--info-border); }
.type-chip.delete   { background: var(--error-bg); color: var(--error-700); border: 1px solid var(--error-border); }
.type-chip.edit     { background: var(--warning-bg); color: var(--warning-700); border: 1px solid var(--warning-border); }
.type-chip.access   { background: var(--success-bg); color: var(--success-700); border: 1px solid var(--success-border); }
.type-chip.role     { background: var(--orange-bg-subtle); color: var(--orange-accent); border: 1px solid var(--orange-border); }

.row-id {
  font-family: monospace; font-size: 11px; font-weight: var(--weight-bold); color: var(--neutral-700);
  background: var(--neutral-100); border: 1px solid var(--neutral-200);
  padding: 2px 8px; border-radius: var(--radius-xs); flex-shrink: 0;
}

.row-actions { display: flex; gap: 8px; flex-shrink: 0; }

.action-pill {
  padding: 6px 12px; border-radius: var(--radius-md); border: none;
  font-size: var(--text-xs); font-weight: var(--weight-bold); cursor: pointer;
  display: inline-flex; align-items: center; gap: 4px;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow);
  transition: all var(--duration-fast);
}
.action-pill:hover:not(:disabled) { transform: translateY(-1px); box-shadow: var(--sku-btn-secondary-shadow-hover); }
.action-pill.approve { color: var(--success-700); }
.action-pill.reject  { color: var(--error-700); }
.action-pill.chat    { color: var(--info-700); }

/* Modals */
.modal-overlay {
  position: fixed; inset: 0; background: var(--overlay-bg);
  backdrop-filter: var(--glass-blur-sm); display: flex; align-items: center;
  justify-content: center; z-index: var(--z-modal); padding: 20px;
}

.modal {
  background: var(--bg-base); border-radius: var(--radius-2xl); width: 100%;
  max-width: 600px; max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: var(--neu-card-hover); border: none; overflow: hidden;
}
.modal-sm { max-width: 440px; }
.modal-lg { max-width: 800px; }

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px; border-bottom: 1px solid var(--neutral-200);
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
  display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: var(--neutral-100); color: var(--text-primary); }

.modal-body { padding: 20px 24px; overflow-y: auto; }
.confirm-text { font-size: var(--text-sm); color: var(--text-primary); line-height: 1.5; margin: 0; }

.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px; border-top: 1px solid rgba(166, 169, 173, 0.4); background: var(--bg-content);
}

.btn-primary {
  background: var(--orange-gradient); color: white; border: none;
  padding: 10px 18px; border-radius: var(--radius-pill); font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; transition: all var(--duration-base);
  box-shadow: var(--sku-btn-primary-shadow);
}
.btn-primary:hover:not(:disabled) { box-shadow: var(--sku-btn-primary-shadow-hover); transform: translateY(-1px); }

.btn-danger {
  background: var(--error-600); color: white; border: none;
  padding: 10px 18px; border-radius: var(--radius-pill); font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; transition: all var(--duration-base);
}
.btn-danger:hover:not(:disabled) { background: var(--error-700); }

.btn-ghost {
  background: var(--bg-base); color: var(--text-secondary); border: none;
  padding: 8px 16px; border-radius: var(--radius-pill); font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; transition: all var(--duration-base);
  box-shadow: var(--sku-btn-secondary-shadow);
}
.btn-ghost:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }

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
  transition: all var(--duration-fast);
}

.details-item-card:hover {
  border-color: var(--orange-border);
  box-shadow: var(--shadow-sm);
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

.monospace-badge {
  font-family: 'Courier New', Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--neutral-800);
  background: rgba(35, 28, 20, 0.06);
  border: 1px solid rgba(35, 28, 20, 0.08);
  padding: 2px 7px;
  border-radius: 6px;
  display: inline-block;
  letter-spacing: 0.5px;
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

.btn-accept {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #15803d;
  border: 1px solid rgba(34, 197, 94, 0.4);
  padding: 9px 18px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--weight-extrabold);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.8);
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.btn-accept:hover:not(:disabled) {
  background: linear-gradient(135deg, #bbf7d0 0%, #86efac 100%);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.28);
  transform: translateY(-1px);
}
.btn-accept:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-danger {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.4);
  padding: 9px 18px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--weight-extrabold);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.8);
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.28);
  transform: translateY(-1px);
}
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid rgba(166, 169, 173, 0.45);
  padding: 9px 18px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-xs);
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.btn-ghost:hover {
  background: var(--orange-bg-subtle);
  color: var(--orange-accent);
  border-color: var(--orange-border);
  box-shadow: var(--shadow-sm);
}

/* Split Review View */
.split-view { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 16px; min-height: 380px; max-height: 55vh; }
.split-left { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; padding-right: 6px; }
.split-right {
  display: flex; flex-direction: column; gap: 10px;
  background: var(--bg-content); border: 1px solid rgba(166, 169, 173, 0.4);
  border-radius: var(--radius-xl); padding: 14px; height: 100%; box-shadow: var(--neu-inset);
  box-sizing: border-box; justify-content: space-between;
}
.split-right h3 { font-size: var(--text-xs); margin: 0 0 4px; font-weight: var(--weight-bold); color: var(--text-primary); flex-shrink: 0; }
.chat-messages-container { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; }
.chat-loading, .chat-empty { text-align: center; margin: auto; padding: 24px 8px; color: var(--text-muted); font-size: var(--text-xs); }
.chat-bubble-list { display: flex; flex-direction: column; gap: 8px; }
.chat-bubble-wrap { display: flex; flex-direction: column; }
.chat-bubble-wrap.me { align-items: flex-end; }
.chat-bubble-wrap.them { align-items: flex-start; }
.bubble-sender {
  font-size: 11px; color: var(--text-secondary); font-weight: var(--weight-bold);
  margin-bottom: 4px; padding: 0 6px; letter-spacing: 0.2px;
}
.chat-bubble-wrap.me .bubble-sender {
  text-align: right; color: var(--orange-accent);
}
.bubble-text {
  padding: 10px 18px; border-radius: var(--radius-pill); font-size: var(--text-xs); line-height: 1.5;
  background: #DBD4CA; border: none; color: var(--text-primary);
  box-shadow: var(--sku-btn-secondary-shadow); word-break: break-word;
}
.chat-bubble-wrap.me .bubble-text {
  background: var(--orange-gradient); color: white; border: none;
  box-shadow: var(--sku-btn-primary-shadow); border-radius: var(--radius-pill);
}
.bubble-time { font-size: 9px; color: var(--text-muted); margin-top: 2px; }

.chat-input-wrap {
  display: flex; gap: 6px; padding-top: 10px; border-top: 1px solid rgba(166, 169, 173, 0.4);
  margin-top: auto; flex-shrink: 0;
}
.chat-input-wrap textarea {
  flex: 1; min-height: 36px; max-height: 80px; resize: none;
  background: var(--bg-input); border: 1px solid rgba(166, 169, 173, 0.55);
  box-shadow: var(--neu-inset); font-weight: var(--weight-semibold);
  border-radius: var(--radius-md); padding: 8px 12px; font-size: var(--text-xs);
  color: var(--text-primary); font-family: inherit; line-height: 1.4;
}
.chat-input-wrap textarea:focus { outline: none; border-color: var(--orange-accent); background: var(--bg-input-focus); }
.chat-send-btn {
  width: 36px; height: 36px; flex-shrink: 0; border-radius: var(--radius-md); border: none;
  background: var(--orange-gradient); color: white; cursor: pointer;
  display: flex; align-items: center; justify-content: center; font-size: var(--text-xs);
  box-shadow: var(--sku-btn-primary-shadow);
}
.chat-closed-notice {
  padding: 8px 12px; border-radius: var(--radius-md); background: var(--neutral-100);
  color: var(--text-muted); font-size: var(--text-xs); font-weight: var(--weight-semibold);
  display: flex; align-items: center; gap: 6px; margin-top: auto; flex-shrink: 0;
}

.viewer-warning-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  padding: 14px 16px;
  border-radius: var(--radius-lg);
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 12px;
  box-shadow: var(--shadow-xs);
}
.viewer-warning-banner i {
  font-size: 18px;
  color: #d97706;
  margin-top: 2px;
  flex-shrink: 0;
}
.viewer-warning-banner p {
  margin: 4px 0 0;
  font-weight: 500;
}

/* Diff Table Styling */
.diff-table-container {
  margin-top: 14px;
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

.user-pill, .uid-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: var(--weight-bold);
  color: var(--text-primary);
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

.section-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.action-pill.sm {
  padding: 4px 10px;
  font-size: 11px;
}

/* Banners */
.info-banner, .danger-banner, .viewer-warning-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  font-size: var(--text-xs);
  line-height: 1.4;
  margin-top: 10px;
}
.info-banner {
  background: var(--info-bg);
  border: 1px solid var(--info-border);
  color: var(--info-700);
}
.danger-banner {
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  color: var(--error-700);
}
.viewer-warning-banner {
  background: #fefce8;
  border: 1px solid #fde047;
  color: #854d0e;
}

/* Section Heading */
.section-heading {
  font-size: var(--text-xs);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-secondary);
  margin-top: 12px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 800px) { .split-view { grid-template-columns: 1fr; } }
</style>
