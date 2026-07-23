<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Trail Log</h1>
        <p class="page-sub">Historical trail record of all approved changes, creations, and deletions</p>
      </div>
      <span class="total-badge">
        <i class="fas fa-history"></i>
        <span>{{ totalEntries }} Entries Logged</span>
      </span>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading audit logs...
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
          :id="'audit-tab-' + tab.key"
        >
          <i :class="tab.icon"></i>
          <span>{{ tab.label }}</span>
          <span class="tab-count" :class="tab.key">{{ tab.count }}</span>
        </button>
      </div>

      <!-- TIMELINE LIST -->
      <div class="timeline-section">
        <transition name="fade-slide" mode="out-in">

          <!-- EMPTY STATE -->
          <div class="empty-state" v-if="activeList.length === 0" :key="'empty-' + activeTab">
            <div class="empty-icon-wrap" :class="activeTab">
              <i :class="tabs.find(t => t.key === activeTab)?.icon"></i>
            </div>
            <p class="empty-title">No {{ activeTab }} recorded</p>
            <p class="empty-sub">No approved {{ activeTab }} have been logged yet.</p>
          </div>

          <!-- TIMELINE ITEMS (Neomorphism) -->
          <div class="timeline" v-else :key="'list-' + activeTab">
            <div
              v-for="(log, i) in activeList"
              :key="log._key"
              class="timeline-item"
              :style="{ animationDelay: i * 45 + 'ms' }"
            >
              <!-- Timeline dot + line -->
              <div class="tl-spine">
                <div class="tl-dot" :class="log._category"></div>
                <div class="tl-line" v-if="i < activeList.length - 1"></div>
              </div>

              <!-- Content card (Neomorphism) -->
              <div class="tl-card">
                <div class="tl-card-top">
                  <div class="tl-label-group">
                    <span class="tl-chip" :class="log._category">
                      <i :class="tabs.find(t => t.key === log._category)?.icon"></i>
                      {{ log._label }}
                    </span>
                    <span class="tl-record">
                      <span class="pub-id-chip">{{ log.record_id }}</span>
                      <span class="record-name">{{ log.record_name }}</span>
                    </span>
                  </div>
                  <div class="tl-date">
                    <i class="fas fa-clock"></i>
                    <span>{{ formatDate(log.updated_at) }}</span>
                  </div>
                </div>

                <div class="tl-statement">
                  Requested by
                  <span class="user-tag">{{ log.requested_by || 'Unknown' }}</span>
                  &nbsp;·&nbsp; Approved by
                  <span class="officer-tag">{{ log.reviewed_by || 'Unknown' }}</span>
                </div>

                <div class="tl-card-footer" v-if="log._category === 'editions'">
                  <button class="view-btn" @click="viewChanges(log)">
                    <i class="fas fa-eye"></i> View Changes Diff
                  </button>
                </div>
              </div>
            </div>
          </div>

        </transition>
      </div>
    </template>

    <!-- CHANGES MODAL (Glassmorphism) -->
    <teleport to="body">
      <div class="modal-overlay" v-if="selectedEdition" @click.self="selectedEdition = null">
        <div class="modal modal-lg">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon-wrap"><i class="fas fa-pen-to-square"></i></div>
              <h2>Edit Diff Details — {{ selectedEdition.record_id }}</h2>
            </div>
            <button class="modal-close" @click="selectedEdition = null" aria-label="Close"><i class="fas fa-times"></i></button>
          </div>
          <div class="modal-body">
            <div class="meta-grid">
              <div class="meta-item">
                <span class="meta-label">Record Identifier</span>
                <span class="meta-val">{{ selectedEdition.record_id }} ({{ selectedEdition.record_name }})</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Requested By</span>
                <span class="meta-val">{{ selectedEdition.requested_by }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Reviewed & Approved By</span>
                <span class="meta-val">{{ selectedEdition.reviewed_by || '—' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Execution Date & Time</span>
                <span class="meta-val">{{ formatFullDateTime(selectedEdition.updated_at) }}</span>
              </div>
            </div>
            <h3 class="diff-title">Field Modifications</h3>
            <div class="diff-table-container">
              <table class="diff-table">
                <thead>
                  <tr><th>Field</th><th>Previous Value</th><th>New Value</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(val, key) in proposedChangesList" :key="key">
                    <td class="field-name">{{ formatFieldName(key) }}</td>
                    <td class="old-val">{{ selectedEdition.current_data?.[key] || '—' }}</td>
                    <td class="new-val">{{ val || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="selectedEdition = null">Close</button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'

const loading   = ref(true)
const activeTab = ref<'all' | 'creations' | 'editions' | 'deletions'>('all')

const creations = ref<any[]>([])
const editions  = ref<any[]>([])
const deletions = ref<any[]>([])

const selectedEdition = ref<any | null>(null)

async function fetchAuditLogs() {
  loading.value = true
  try {
    const res = await api.get('workflows/audit-log/')
    creations.value = (res.data.creations || []).map((r: any) => ({ ...r, _key: 'c-' + r.id }))
    editions.value  = (res.data.editions  || []).map((r: any) => ({ ...r, _key: 'e-' + r.id }))
    deletions.value = (res.data.deletions || []).map((r: any) => ({ ...r, _key: 'd-' + r.id }))
  } catch (e) {
    console.error('Failed to fetch audit log data:', e)
  } finally {
    loading.value = false
  }
}

const totalEntries = computed(() => creations.value.length + editions.value.length + deletions.value.length)

const tabs = computed<{ key: 'all' | 'creations' | 'editions' | 'deletions', label: string, icon: string, count: number }[]>(() => [
  { key: 'all',       label: 'All Logs',  icon: 'fas fa-layer-group',  count: totalEntries.value     },
  { key: 'creations', label: 'Creations', icon: 'fas fa-plus-circle',  count: creations.value.length },
  { key: 'editions',  label: 'Editions',  icon: 'fas fa-pen-to-square',count: editions.value.length  },
  { key: 'deletions', label: 'Deletions', icon: 'fas fa-trash-alt',    count: deletions.value.length },
])

const allEntries = computed(() => [
  ...creations.value.map(r => ({ ...r, _category: 'creations', _label: 'Created'  })),
  ...editions.value.map(r  => ({ ...r, _category: 'editions',  _label: 'Edited'   })),
  ...deletions.value.map(r => ({ ...r, _category: 'deletions', _label: 'Deleted'  })),
].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()))

const activeList = computed(() => {
  if (activeTab.value === 'all')       return allEntries.value
  if (activeTab.value === 'creations') return creations.value.map(r => ({ ...r, _category: 'creations', _label: 'Created'  }))
  if (activeTab.value === 'editions')  return editions.value.map(r  => ({ ...r, _category: 'editions',  _label: 'Edited'   }))
  return deletions.value.map(r => ({ ...r, _category: 'deletions', _label: 'Deleted' }))
})

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatFullDateTime(dateStr: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('en-GB')
}

function formatFieldName(key: string) {
  const mapping: Record<string, string> = {
    name: 'Full Name', designation: 'Designation', employee_code: 'Employee Code',
    pan: 'PAN', source_company: 'Disclosure Company', info_details: 'Information Details',
    info_received_date: 'Date Received', disclosure_name: 'Disclosure Name',
    disclosure_designation: 'Disclosure Designation', disclosure_department: 'Disclosure Department'
  }
  return mapping[key] || key
}

function viewChanges(log: any) {
  selectedEdition.value = log
}

const proposedChangesList = computed(() => {
  const changes: Record<string, any> = {}
  if (!selectedEdition.value || !selectedEdition.value.proposed_data) return changes
  const proposed = selectedEdition.value.proposed_data
  const current  = selectedEdition.value.current_data || {}
  for (const key of Object.keys(proposed)) {
    if (['id','public_id','created_by','updated_by','created_at','updated_at','status'].includes(key)) continue
    if (proposed[key] !== current[key]) changes[key] = proposed[key]
  }
  return changes
})

onMounted(fetchAuditLogs)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; }
.page-title  { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub    { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

.total-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 16px; border-radius: var(--radius-pill);
  background: var(--bg-base); box-shadow: var(--neu-btn);
  font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-secondary);
}
.total-badge i { color: var(--orange-accent); }

.loading-state { text-align: center; padding: 48px 24px; color: var(--orange-accent); font-size: var(--text-sm); font-weight: var(--weight-bold); }

/* Tab Bar */
.tab-bar {
  display: flex; gap: 6px; width: fit-content;
  background: var(--bg-app); border-radius: var(--radius-xl);
  padding: 4px; box-shadow: var(--neu-inset);
}
.tab-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; border: none; border-radius: var(--radius-lg);
  font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-secondary);
  background: transparent; cursor: pointer; transition: all var(--duration-fast);
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow); color: var(--text-primary); }
.tab-btn.active[data-tab="all"]       { color: var(--text-primary); }
.tab-btn.active[data-tab="creations"] { color: var(--info-700); }
.tab-btn.active[data-tab="editions"]  { color: var(--warning-700); }
.tab-btn.active[data-tab="deletions"] { color: var(--error-700); }

.tab-count {
  min-width: 20px; height: 20px; border-radius: var(--radius-pill); font-size: 10px; font-weight: var(--weight-bold);
  display: inline-flex; align-items: center; justify-content: center; padding: 0 6px;
}
.tab-count.all       { background: var(--neutral-200); color: var(--text-secondary); }
.tab-count.creations { background: var(--info-bg);    color: var(--info-700); }
.tab-count.editions  { background: var(--warning-bg); color: var(--warning-700); }
.tab-count.deletions { background: var(--error-bg);   color: var(--error-700); }

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px 24px; gap: 10px; text-align: center;
}
.empty-icon-wrap {
  width: 56px; height: 56px; border-radius: var(--radius-xl);
  display: flex; align-items: center; justify-content: center; font-size: 24px;
}
.empty-icon-wrap.all       { background: var(--neutral-100); color: var(--text-muted); }
.empty-icon-wrap.creations { background: var(--info-bg);    color: var(--info-600); }
.empty-icon-wrap.editions  { background: var(--warning-bg); color: var(--warning-600); }
.empty-icon-wrap.deletions { background: var(--error-bg);   color: var(--error-600); }
.empty-title { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.empty-sub   { font-size: var(--text-xs); color: var(--text-secondary); margin: 0; max-width: 280px; }

/* Timeline */
.timeline-section { min-height: 200px; }
.timeline { display: flex; flex-direction: column; gap: 0; padding-left: 4px; }
.timeline-item { display: flex; gap: 16px; }

.tl-spine { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; width: 20px; }
.tl-dot {
  width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; margin-top: 18px;
  box-shadow: 0 0 0 3px var(--bg-base);
}
.tl-dot.creations { background: var(--info-500); }
.tl-dot.editions  { background: var(--warning-500); }
.tl-dot.deletions { background: var(--error-500); }

.tl-line { flex: 1; width: 2px; background: var(--neutral-200); margin: 4px 0; min-height: 20px; }

/* Card (Neomorphism) */
.tl-card {
  flex: 1; margin-bottom: 16px; background: var(--bg-base); border-radius: var(--radius-xl);
  box-shadow: var(--neu-card); padding: 16px 20px; display: flex; flex-direction: column; gap: 10px;
  transition: transform var(--duration-base) var(--ease-out), box-shadow var(--duration-base);
}
.tl-card:hover { transform: translateX(4px); box-shadow: var(--neu-card-hover); }

.tl-card-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.tl-label-group { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.tl-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 8px; border-radius: var(--radius-xs); font-size: 10px;
  font-weight: var(--weight-bold); text-transform: uppercase; letter-spacing: 0.5px;
}
.tl-chip.creations { background: var(--info-bg); color: var(--info-700); border: 1px solid var(--info-border); }
.tl-chip.editions  { background: var(--warning-bg); color: var(--warning-700); border: 1px solid var(--warning-border); }
.tl-chip.deletions { background: var(--error-bg); color: var(--error-700); border: 1px solid var(--error-border); }

.tl-record { display: flex; align-items: center; gap: 6px; }
.pub-id-chip {
  background: var(--neutral-100); border: 1px solid var(--neutral-200);
  padding: 2px 8px; border-radius: var(--radius-xs);
  color: var(--orange-accent); font-family: monospace; font-size: 11px; font-weight: var(--weight-bold);
}
.record-name { font-size: var(--text-sm); font-weight: var(--weight-bold); color: var(--text-primary); }

.tl-date { display: flex; align-items: center; gap: 6px; font-size: var(--text-xs); color: var(--text-secondary); font-weight: var(--weight-medium); flex-shrink: 0; }
.tl-date i { color: var(--orange-accent); font-size: 11px; }

.tl-statement { font-size: var(--text-xs); color: var(--text-secondary); line-height: 1.5; }
.user-tag { font-weight: var(--weight-bold); color: var(--orange-accent); }
.officer-tag { font-weight: var(--weight-bold); color: var(--success-600); }

.tl-card-footer { display: flex; padding-top: 2px; }

.view-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: var(--radius-md); border: none;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow);
  color: var(--text-secondary); font-size: var(--text-xs); font-weight: var(--weight-bold);
  cursor: pointer; transition: all var(--duration-fast);
}
.view-btn:hover { color: var(--info-600); box-shadow: var(--sku-btn-secondary-shadow-hover); transform: translateY(-1px); }

/* Modals */
.modal-overlay {
  position: fixed; inset: 0; background: var(--overlay-bg);
  backdrop-filter: var(--glass-blur-sm); display: flex; align-items: center;
  justify-content: center; z-index: var(--z-modal); padding: 20px;
}
.modal {
  background: var(--bg-base); border-radius: var(--radius-2xl); width: 100%;
  max-width: 680px; max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: var(--neu-card-hover); border: none; overflow: hidden;
}
.modal-lg { max-width: 760px; }

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
  display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: var(--bg-app); color: var(--text-primary); }

.modal-body { padding: 20px 24px; overflow-y: auto; }

.meta-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px;
  background: var(--bg-app); border: none; box-shadow: var(--neu-inset);
  padding: 14px 16px; border-radius: var(--radius-xl); margin-bottom: 16px;
}
.meta-item { display: flex; flex-direction: column; gap: 2px; }
.meta-label { font-size: 10px; color: var(--text-muted); font-weight: var(--weight-bold); text-transform: uppercase; }
.meta-val   { font-size: var(--text-xs); font-weight: var(--weight-bold); color: var(--text-primary); }

.diff-title { font-size: var(--text-sm); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0 0 8px; }

.diff-table-container { background: var(--bg-input); border: 1px solid rgba(166, 169, 173, 0.4); border-radius: var(--radius-md); padding: 8px; overflow-x: auto; max-height: 260px; box-shadow: var(--neu-inset); }
.diff-table { width: 100%; border-collapse: collapse; font-size: var(--text-xs); text-align: left; }
.diff-table th, .diff-table td { padding: 8px 12px; border-bottom: 1px solid rgba(166, 169, 173, 0.3); }
.diff-table th { font-weight: var(--weight-bold); color: var(--text-muted); }
.field-name { font-weight: var(--weight-bold); color: var(--text-primary); width: 30%; }
.old-val { color: var(--error-600); background: var(--error-bg); border-radius: var(--radius-xs); }
.new-val { color: var(--success-600); background: var(--success-bg); border-radius: var(--radius-xs); font-weight: var(--weight-bold); }

.modal-footer {
  display: flex; justify-content: flex-end; padding: 16px 24px; border-top: 1px solid rgba(166, 169, 173, 0.4); background: var(--bg-content);
}
.btn-ghost {
  background: var(--bg-base); color: var(--text-secondary); border: none;
  padding: 8px 16px; border-radius: var(--radius-pill); font-size: var(--text-xs);
  font-weight: var(--weight-bold); cursor: pointer; transition: all var(--duration-base);
  box-shadow: var(--sku-btn-secondary-shadow);
}
.btn-ghost:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }

@media (max-width: 640px) {
  .tab-bar { width: 100%; }
  .tab-btn { flex: 1; justify-content: center; }
  .tl-date { display: none; }
}
</style>
