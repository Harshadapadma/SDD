<template>
  <div class="page">
    
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Clarifications Inbox</h1>
        <p class="page-sub">Resolve questions raised by the Compliance Officer regarding your record submissions</p>
      </div>
      <div class="header-badges">
        <span class="count-badge"><i class="fas fa-comments"></i> {{ activeConversationsCount }} Active Conversations</span>
      </div>
    </div>

    <!-- LOADING STATE -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading clarifications...
    </div>

    <!-- MAIN VIEW -->
    <div v-else class="clarifications-layout">
      
      <!-- LEFT PANEL: LIST OF REQUESTS (Neomorphism) -->
      <aside class="requests-sidebar">
        <div class="sidebar-header">
          <h3>Record Requests ({{ requests.length }})</h3>
        </div>
        <div class="sidebar-body">
          <div v-if="requests.length === 0" class="empty-list">
            <i class="fas fa-inbox"></i>
            <p>No clarifications requested on your records.</p>
          </div>
          <div
            v-else
            v-for="req in requests"
            :key="req.id"
            :class="['request-item', { active: selectedRequest?.id === req.id }]"
            @click="selectRequest(req)"
          >
            <div class="item-header">
              <span class="pub-id">{{ req.record_id || 'Pending ID' }}</span>
              <span :class="['status-chip', req.status.toLowerCase()]">{{ req.status }}</span>
            </div>
            <div class="item-name">{{ req.record_name }}</div>
            <div class="item-date"><i class="fas fa-clock"></i> {{ formatDate(req.created_at) }}</div>
          </div>
        </div>
      </aside>

      <!-- RIGHT PANEL: CHAT AND DETAILS -->
      <main class="chat-main">
        <div v-if="!selectedRequest" class="no-selection">
          <i class="fas fa-comments"></i>
          <h2>Select a conversation to begin</h2>
          <p>Choose a record request from the left panel to review questions and post clarification replies.</p>
        </div>
        
        <div v-else class="chat-workspace">
          
          <!-- WORKSPACE HEADER -->
          <div class="workspace-header">
            <div>
              <h2>{{ selectedRequest.record_name }}</h2>
              <p class="sub">Record ID: <strong>{{ selectedRequest.record_id }}</strong> | Request ID: <strong>#{{ selectedRequest.id }}</strong></p>
            </div>
            <div class="header-action-group">
              <button class="btn-ghost" @click="showDetailsModal = true">
                <i class="fas fa-file-alt"></i> Form Details
              </button>
              <button v-if="isCollaborator && selectedRequest.status === 'PENDING'" class="btn-primary" @click="openEdit">
                <i class="fas fa-pen"></i> Edit Form
              </button>
              <button class="chat-close-btn" @click="selectedRequest = null" title="Exit Chat" aria-label="Exit Chat">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>

          <!-- CHAT BODY -->
          <div class="chat-body" ref="chatBody">
            <div v-if="loadingMessages" class="chat-loading">
              <i class="fas fa-spinner fa-spin"></i> Fetching conversation history...
            </div>
            <div v-else-if="messages.length === 0" class="chat-empty">
              No messages exchanged yet for this request.
            </div>
            <div v-else class="chat-message-list">
              <div v-for="msg in messages" :key="msg.id" :class="['chat-bubble-wrap', msg.is_me ? 'me' : 'them']">
                <div class="bubble-sender">{{ formatSender(msg) }}</div>
                <div class="bubble-text">{{ msg.message }}</div>
                <div class="bubble-time">{{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
          </div>

          <!-- CHAT INPUT -->
          <div class="chat-input-area" v-if="selectedRequest.status === 'PENDING'">
            <textarea
              v-model="newMessage"
              placeholder="Type your reply to the Compliance Officer..."
              @keyup.enter.exact.prevent="sendReply"
            ></textarea>
            <button class="send-btn" @click="sendReply" :disabled="!newMessage.trim()">
              <i class="fas fa-paper-plane"></i> Send
            </button>
          </div>
          <div class="chat-closed-notice" v-else>
            <i class="fas fa-lock"></i> Conversation closed (Request {{ selectedRequest.status.toLowerCase() }})
          </div>

        </div>
      </main>

    </div>

    <!-- DETAILS MODAL (Glassmorphism & Tactile Data Cards) -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showDetailsModal && selectedRequest" @click.self="showDetailsModal = false">
        <div class="modal modal-lg">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-file-lines"></i></div>
              <div>
                <h2>Creation Details: {{ selectedRequest.record_id || ('#' + selectedRequest.id) }}</h2>
                <span class="modal-subtitle">Submitted record dataset &amp; governance details</span>
              </div>
            </div>
            <button class="modal-close" @click="showDetailsModal = false" aria-label="Close"><i class="fas fa-times"></i></button>
          </div>

          <div class="modal-body">
            <div class="details-grid-container">
              <div 
                v-for="(val, key) in getCreationDetails(selectedRequest)" 
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

          <div class="modal-footer">
            <button class="btn-ghost" @click="showDetailsModal = false">Close</button>
            <template v-if="isComplianceOrAdmin && selectedRequest.status === 'PENDING'">
              <button class="btn-danger" @click="reviewRequest('REJECT')" :disabled="reviewing">
                <i class="fas fa-spinner fa-spin" v-if="reviewing"></i>
                <i class="fas fa-circle-xmark" v-else></i>
                <span>Reject Request</span>
              </button>
              <button class="btn-accept" @click="reviewRequest('APPROVE')" :disabled="reviewing">
                <i class="fas fa-spinner fa-spin" v-if="reviewing"></i>
                <i class="fas fa-circle-check" v-else></i>
                <span>Accept Request</span>
              </button>
            </template>
          </div>
        </div>
      </div>
    </teleport>

    <!-- EDIT MODAL (Glassmorphism) -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showEditModal && selectedRequest" @click.self="showEditModal = false">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-pen-to-square"></i></div>
              <h2>Edit Form — {{ selectedRequest.record_id }}</h2>
            </div>
            <button class="modal-close" @click="showEditModal = false" aria-label="Close"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
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
                <input type="date" v-model="editForm.info_received_date" :max="todayDate" />
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
            <button class="btn-ghost" @click="showEditModal = false">Cancel</button>
            <button class="btn-primary" @click="saveEdit" :disabled="editing">
              <i class="fas fa-spinner fa-spin" v-if="editing"></i>
              <span>{{ editing ? 'Saving…' : 'Save Changes' }}</span>
            </button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const { notify } = useNotifications()
const route = useRoute()

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isCollaborator = computed(() => user?.role === 'COLLABORATOR')

const loading = ref(true)
const requests = ref<any[]>([])
const activeConversationsCount = computed(() => {
  return requests.value.filter(r => r && r.status && !['APPROVED', 'REJECTED'].includes(r.status.toUpperCase())).length
})
const selectedRequest = ref<any | null>(null)
const messages = ref<any[]>([])
const newMessage = ref('')
const loadingMessages = ref(false)
const showDetailsModal = ref(false)
const showEditModal = ref(false)
const editing = ref(false)
const editError = ref('')
const editForm = ref<any>({})
const chatBody = ref<HTMLElement | null>(null)

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

async function fetchRequests() {
  loading.value = true
  try {
    const res = await api.get('workflows/clarifications/')
    requests.value = res.data
    
    const targetReqId = route.query.req_id
    if (targetReqId) {
      const match = requests.value.find(r => r.id === Number(targetReqId))
      if (match) {
        selectRequest(match)
      }
    }
  } catch (e) {
    console.error('Failed to fetch requests with clarifications:', e)
  } finally {
    loading.value = false
  }
}

async function selectRequest(req: any) {
  selectedRequest.value = req
  loadingMessages.value = true
  messages.value = []
  try {
    const res = await api.get(`workflows/creation/${req.id}/clarification/`)
    messages.value = res.data
    scrollToBottom()
  } catch (e) {
    console.error('Failed to fetch messages:', e)
  } finally {
    loadingMessages.value = false
  }
}

function openEdit() {
  if (!selectedRequest.value || !selectedRequest.value.current_data) return
  const data = selectedRequest.value.current_data
  editForm.value = {
    name: data.name || '',
    designation: data.designation || '',
    employee_code: data.employee_code || '',
    pan: data.pan || '',
    source_company: data.source_company || '',
    info_details: data.info_details || '',
    info_received_date: data.info_received_date || '',
    disclosure_name: data.disclosure_name || '',
    disclosure_designation: data.disclosure_designation || ''
  }
  editError.value = ''
  showEditModal.value = true
}

async function saveEdit() {
  const validationError = validateRecord(editForm.value)
  if (validationError) {
    editError.value = validationError
    return
  }
  editing.value = true
  editError.value = ''
  try {
    await api.put(`records/${selectedRequest.value.record_id}/update/`, editForm.value)
    showEditModal.value = false
    await fetchRequests()
    const updatedReq = requests.value.find(r => r.id === selectedRequest.value.id)
    if (updatedReq) {
      selectedRequest.value = updatedReq
    }
  } catch (e: any) {
    editError.value = formatApiError(e) || 'Failed to update record'
  } finally {
    editing.value = false
  }
}

async function sendReply() {
  if (!newMessage.value.trim() || !selectedRequest.value) return
  const reqId = selectedRequest.value.id
  try {
    const res = await api.post(`workflows/creation/${reqId}/clarification/`, {
      message: newMessage.value.trim()
    })
    messages.value.push(res.data)
    newMessage.value = ''
    scrollToBottom()
  } catch (e) {
    console.error('Failed to send message:', e)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}

function formatSender(msg: any) {
  if (msg.is_me) return 'Me'
  if (msg.sender_role === 'COMPLIANCE_OFFICER' || msg.sender_role === 'ADMIN') return 'Compliance Officer'
  return msg.sender_name || 'Collaborator'
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatTime(dateStr: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

const isComplianceOrAdmin = computed(() => ['ADMIN', 'COMPLIANCE_OFFICER'].includes(user.role?.toUpperCase()))
const reviewing = ref(false)

async function reviewRequest(action: 'APPROVE' | 'REJECT') {
  if (!selectedRequest.value) return
  reviewing.value = true
  try {
    await api.post(`workflows/creation/review/${selectedRequest.value.id}/`, { action })
    notify(
      action === 'APPROVE' ? 'Request Accepted' : 'Request Rejected',
      `Creation request for ${selectedRequest.value.record_id || ('#' + selectedRequest.value.id)} has been ${action === 'APPROVE' ? 'accepted' : 'rejected'}.`,
      action === 'APPROVE' ? 'SUCCESS' : 'INFO'
    )
    selectedRequest.value.status = action === 'APPROVE' ? 'APPROVED' : 'REJECTED'
    showDetailsModal.value = false
    fetchRequests()
  } catch (err: any) {
    console.error(err)
    const msg = err?.response?.data?.error || 'Failed to process request review'
    notify('Review Failed', msg, 'ERROR')
  } finally {
    reviewing.value = false
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
    name: 'Full Name',
    designation: 'Designation',
    employee_code: 'Employee Code',
    pan: 'PAN',
    source_company: 'Disclosure Company',
    info_details: 'Information Details',
    info_received_date: 'Date Received',
    disclosure_name: 'Disclosure Name',
    disclosure_designation: 'Disclosure Designation',
    disclosure_department: 'Disclosure Department',
    created_by_name: 'Created By Name',
    updated_by_name: 'Updated By Name',
    access_type: 'Access Type'
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
    if (['id', 'public_id', 'created_by', 'updated_by', 'created_at', 'updated_at', 'status', 'access_type', 'access_list'].includes(key)) continue
    details[key] = req.current_data[key]
  }
  return details
}

onMounted(fetchRequests)
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title  { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); margin: 0; }
.page-sub    { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

.count-badge {
  padding: 6px 14px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold);
  background: var(--bg-base); box-shadow: var(--neu-btn); color: var(--orange-accent);
  display: flex; align-items: center; gap: 8px;
}

.loading-state { text-align: center; padding: 48px 24px; color: var(--orange-accent); font-size: var(--text-sm); font-weight: var(--weight-bold); }

/* Layout Grid */
.clarifications-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

/* Sidebar (Neomorphism) */
.requests-sidebar {
  background: var(--bg-base);
  border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--neutral-200);
}
.sidebar-header h3 { font-size: var(--text-sm); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }

.sidebar-body { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 6px; }

.empty-list { text-align: center; padding: 40px 16px; color: var(--text-muted); font-size: var(--text-xs); }
.empty-list i { font-size: 28px; margin-bottom: 8px; color: var(--neutral-400); }

.request-item {
  padding: 12px 14px;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast);
  background: var(--bg-content);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-xs);
}
.request-item:hover { background: var(--orange-bg-subtle); border-color: var(--orange-border); }
.request-item.active {
  background: var(--orange-bg-subtle);
  border-color: var(--orange-accent);
  box-shadow: var(--neu-pressed);
}

.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.pub-id { font-family: monospace; font-size: 11px; font-weight: var(--weight-bold); color: var(--orange-accent); }
.status-chip {
  padding: 1px 6px; border-radius: var(--radius-pill); font-size: 9px; font-weight: var(--weight-bold); text-transform: uppercase;
}
.status-chip.pending  { background: var(--warning-bg); color: var(--warning-700); }
.status-chip.approved { background: var(--success-bg); color: var(--success-700); }
.status-chip.rejected { background: var(--error-bg);   color: var(--error-700); }

.item-name { font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-date { font-size: 10px; color: var(--text-muted); margin-top: 4px; display: flex; align-items: center; gap: 4px; }

/* Workspace */
.chat-main {
  background: var(--bg-base);
  border-radius: var(--radius-2xl);
  box-shadow: var(--neu-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.no-selection {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 40px; text-align: center; color: var(--text-muted); gap: 12px;
}
.no-selection i { font-size: 48px; color: var(--neutral-300); }
.no-selection h2 { font-size: var(--text-lg); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.no-selection p { font-size: var(--text-xs); max-width: 360px; }

.chat-workspace { display: flex; flex-direction: column; height: 100%; }

.workspace-header {
  padding: 16px 24px; border-bottom: 1px solid var(--card-divider);
  display: flex; justify-content: space-between; align-items: center;
  background: var(--bg-base);
}
.workspace-header h2 { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.workspace-header .sub { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 2px; }

.header-action-group { display: flex; align-items: center; gap: 8px; }

.chat-close-btn {
  width: 32px; height: 32px; border-radius: 50%; background: var(--bg-content);
  border: 1px solid var(--card-divider); color: var(--text-secondary); display: flex;
  align-items: center; justify-content: center; cursor: pointer; transition: all var(--duration-fast);
  margin-left: 4px; box-shadow: var(--shadow-xs);
}
.chat-close-btn:hover {
  background: var(--orange-bg-subtle); color: var(--orange-accent); border-color: var(--orange-border);
}

.chat-body { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
.chat-loading, .chat-empty { text-align: center; margin: auto; color: var(--text-muted); font-size: var(--text-xs); }

.chat-message-list { display: flex; flex-direction: column; gap: 12px; }
.chat-bubble-wrap { display: flex; flex-direction: column; max-width: 75%; }
.chat-bubble-wrap.me { align-self: flex-end; align-items: flex-end; }
.chat-bubble-wrap.them { align-self: flex-start; align-items: flex-start; }

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

.chat-input-area {
  padding: 16px 20px; border-top: 1px solid var(--card-divider);
  display: flex; gap: 10px; background: var(--bg-base);
}
.chat-input-area textarea {
  flex: 1; min-height: 42px; max-height: 100px; resize: none;
  background: var(--bg-content); border: 1px solid var(--card-divider);
  border-radius: var(--radius-md); padding: 10px 14px; font-size: var(--text-xs);
  color: var(--text-primary); font-family: inherit; line-height: 1.4;
  box-shadow: var(--neu-inset); outline: none; transition: border-color var(--duration-fast);
}
.chat-input-area textarea:focus { border-color: var(--orange-accent); }

.send-btn {
  padding: 0 18px; border-radius: var(--radius-md); border: none;
  background: var(--orange-gradient); color: white; font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; display: flex; align-items: center; gap: 6px;
  box-shadow: var(--sku-btn-primary-shadow); transition: all var(--duration-fast);
}
.send-btn:hover:not(:disabled) { box-shadow: var(--sku-btn-primary-shadow-hover); transform: translateY(-1px); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.chat-closed-notice {
  padding: 14px 20px; background: var(--bg-content); color: var(--text-muted);
  font-size: var(--text-xs); font-weight: var(--weight-semibold); text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  border-top: 1px solid var(--card-divider);
}

/* Modals */
.modal-overlay {
  position: fixed; inset: 0; background: var(--overlay-bg);
  backdrop-filter: var(--glass-blur-sm); display: flex; align-items: center;
  justify-content: center; z-index: var(--z-modal); padding: 20px;
}
.modal {
  background: var(--bg-base); border-radius: var(--radius-2xl); width: 100%;
  max-width: 600px; max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: var(--glass-shadow-lg); border: none; overflow: hidden;
}
.modal-lg { max-width: 720px; }

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px; border-bottom: none;
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
.modal-close:hover { background: var(--bg-content); color: var(--text-primary); }

.modal-body { padding: 20px 24px; overflow-y: auto; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px; border-top: none; background: var(--bg-base);
}

.details-grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  background: var(--bg-content);
  padding: 16px;
  border-radius: var(--radius-xl);
  box-shadow: var(--neu-inset);
  border: 1px solid rgba(166, 169, 173, 0.3);
}

.details-item-card {
  background: var(--bg-card);
  border: 1px solid rgba(166, 169, 173, 0.25);
  border-radius: var(--radius-lg);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
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
  font-size: 10px;
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
  padding: 2px 8px;
  border-radius: 6px;
  display: inline-block;
  letter-spacing: 0.5px;
}

.long-value-box {
  background: var(--bg-app);
  border: 1px solid rgba(166, 169, 173, 0.3);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: var(--text-xs);
  line-height: 1.5;
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

.modal-subtitle {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: var(--weight-medium);
}
</style>

<style>
/* Global Unscoped Styles for Teleported Modals (Edit Form & Details) */
body .modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.55);
  backdrop-filter: blur(12px) saturate(1.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

body .modal {
  background: var(--bg-app);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.6);
  overflow: hidden;
}

body .modal-lg {
  max-width: 720px;
}

body .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px 14px;
  border-bottom: 1px solid rgba(166, 169, 173, 0.2);
}

body .modal-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

body .modal-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  box-shadow: var(--sku-btn-primary-shadow);
  flex-shrink: 0;
}

body .modal-header h2 {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}

body .modal-subtitle {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: var(--weight-medium);
}

body .modal-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-input);
  box-shadow: var(--neu-inset);
  border: 1px solid rgba(166, 169, 173, 0.3);
  cursor: pointer;
  font-size: 11px;
  color: var(--text-muted);
  transition: all var(--duration-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

body .modal-close:hover {
  background: var(--orange-bg-subtle);
  color: var(--orange-accent);
}

body .modal-body {
  padding: 20px 24px;
  overflow-y: auto;
}

body .modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px 18px;
  border-top: 1px solid rgba(166, 169, 173, 0.15);
  background: var(--bg-app);
}

/* Skeuomorphic Form Controls for Teleported Edit Modal */
body .form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

body .form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

body .form-group.full-width {
  grid-column: 1 / -1;
}

body .form-group label {
  font-size: 11px;
  font-weight: 800;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

body .form-group input,
body .form-group textarea,
body .form-group select {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(166, 169, 173, 0.55);
  background: var(--bg-input);
  box-shadow: var(--neu-inset);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: inherit;
  outline: none;
  transition: all var(--duration-fast);
  width: 100%;
  box-sizing: border-box;
}

body .form-group input:focus,
body .form-group textarea:focus,
body .form-group select:focus {
  border-color: var(--orange-accent);
  background: var(--bg-input-focus);
  box-shadow: inset 0 2px 4px rgba(35, 28, 20, 0.08), 0 0 0 3px var(--orange-glow);
}

/* Button overrides for teleported modals */
body .btn-primary {
  background: var(--orange-gradient);
  color: white;
  border: none;
  padding: 9px 18px;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all var(--duration-base);
  box-shadow: var(--sku-btn-primary-shadow);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

body .btn-primary:hover:not(:disabled) {
  box-shadow: var(--sku-btn-primary-shadow-hover);
  transform: translateY(-1px);
}

body .btn-ghost {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid rgba(166, 169, 173, 0.45);
  padding: 9px 18px;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--duration-base);
  box-shadow: var(--shadow-xs);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

body .btn-ghost:hover {
  background: var(--orange-bg-subtle);
  color: var(--orange-accent);
  border-color: var(--orange-border);
}
</style>
