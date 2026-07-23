<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Notifications</h1>
        <p class="page-sub">System alerts, record events, and workflow updates</p>
      </div>
      <button class="btn-ghost" @click="markAllRead" :disabled="!hasUnread">
        <i class="fas fa-check-double"></i> Mark All Read
      </button>
    </div>

    <!-- STATS (Neomorphism) -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon-wrap green">
          <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? 'var(--error-500)' : undefined }"></i>
        </div>
        <div>
          <div class="stat-val">{{ notifications.length }}</div>
          <div class="stat-label">Total Notifications</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap orange">
          <i class="fas fa-envelope-open"></i>
        </div>
        <div>
          <div class="stat-val">{{ unreadCount }}</div>
          <div class="stat-label">Unread Alerts</div>
        </div>
      </div>
    </div>

    <!-- FILTER TABS -->
    <div class="tab-bar">
      <button
        v-for="t in tabs" :key="t.val"
        :class="['tab-btn', { active: activeTab === t.val }]"
        @click="activeTab = t.val"
      >
        <i :class="['fas', t.icon]"></i>
        <span>{{ t.label }}</span>
      </button>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading notifications…
    </div>

    <!-- EMPTY -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="fas fa-bell-slash empty-icon"></i>
      <p class="empty-title">No notifications here</p>
      <p class="empty-sub">You're all caught up with your notifications.</p>
    </div>

    <!-- NOTIFICATION LIST -->
    <div v-else class="notif-list">
      <div
        v-for="n in filtered"
        :key="n.id"
        :class="['notif-card', n.type.toLowerCase(), { unread: !n.is_read }]"
        @click="markRead(n)"
      >
        <div :class="['notif-icon-wrap', n.type.toLowerCase()]">
          <i :class="['fas', typeIcon(n.type)]"></i>
        </div>
        <div class="notif-body">
          <div class="notif-top">
            <span class="notif-title">{{ n.title }}</span>
            <span class="notif-time"><i class="fas fa-clock"></i> {{ formatTime(n.created_at) }}</span>
          </div>
          <p class="notif-msg">{{ n.message }}</p>
        </div>
        <div class="unread-dot" v-if="!n.is_read"></div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNotifications } from '../../composables/useNotifications'
import api from '../../api/client'

const { isMuted } = useNotifications()
const notifications = ref<any[]>([])
const loading = ref(false)
const activeTab = ref('ALL')

const tabs = [
  { val: 'ALL',     label: 'All',     icon: 'fa-layer-group' },
  { val: 'INFO',    label: 'Info',    icon: 'fa-circle-info' },
  { val: 'SUCCESS', label: 'Success', icon: 'fa-circle-check' },
  { val: 'WARNING', label: 'Warning', icon: 'fa-triangle-exclamation' },
  { val: 'ERROR',   label: 'Error',   icon: 'fa-circle-xmark' },
]

const filtered = computed(() =>
  activeTab.value === 'ALL'
    ? notifications.value
    : notifications.value.filter(n => n.type === activeTab.value)
)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)
const hasUnread   = computed(() => unreadCount.value > 0)

function typeIcon(type: string) {
  const map: Record<string, string> = {
    INFO: 'fa-circle-info',
    SUCCESS: 'fa-circle-check',
    WARNING: 'fa-triangle-exclamation',
    ERROR: 'fa-circle-xmark',
  }
  return map[type] || 'fa-bell'
}

function formatTime(d: string) {
  if (!d) return ''
  const date = new Date(d)
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diff < 60)  return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

async function fetchNotifications() {
  loading.value = true
  try {
    const res = await api.get('notifications/')
    notifications.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function markRead(n: any) {
  if (n.is_read) return
  try {
    await api.post(`notifications/${n.id}/read/`)
    n.is_read = true
  } catch (e) {
    console.error(e)
  }
}

async function markAllRead() {
  const unread = notifications.value.filter(n => !n.is_read)
  await Promise.all(unread.map(n => api.post(`notifications/${n.id}/read/`)))
  notifications.value.forEach(n => n.is_read = true)
}

onMounted(fetchNotifications)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; }
.page-title  { font-size: var(--text-xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub    { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 2px; }

/* Stats */
.stats-row { display: flex; gap: 14px; }
.stat-card {
  flex: 1; max-width: 220px; display: flex; align-items: center; gap: 12px;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow); border-radius: var(--radius-lg);
  padding: 12px 16px; transition: all var(--duration-base) var(--ease-out);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--sku-btn-secondary-shadow-hover); }

.stat-icon-wrap {
  width: 36px; height: 36px; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow); flex-shrink: 0;
}
.stat-icon-wrap.green  { color: var(--success-600); }
.stat-icon-wrap.orange { color: var(--orange-accent); }

.stat-val   { font-size: 20px; font-weight: var(--weight-extrabold); color: var(--text-primary); line-height: 1.1; }
.stat-label { font-size: 11px; color: var(--text-secondary); font-weight: var(--weight-semibold); margin-top: 2px; }

/* Tabs */
.tab-bar { display: flex; gap: 8px; flex-wrap: wrap; }
.tab-btn {
  padding: 6px 14px; border-radius: var(--radius-pill); border: none;
  background: var(--bg-base); box-shadow: var(--sku-btn-secondary-shadow);
  font-size: 12px; font-weight: var(--weight-bold); cursor: pointer;
  display: flex; align-items: center; gap: 6px; transition: all var(--duration-fast); color: var(--text-secondary);
}
.tab-btn.active {
  background: var(--orange-gradient); color: white;
  box-shadow: var(--sku-btn-primary-shadow);
}
.tab-btn:hover:not(.active) { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); transform: translateY(-1px); }

/* States */
.loading-state { text-align: center; padding: 40px 20px; color: var(--orange-accent); font-size: var(--text-sm); font-weight: var(--weight-bold); }
.empty-state {
  display: flex; flex-direction: column; align-items: center; padding: 48px 20px; text-align: center; gap: 6px;
  background: var(--bg-base); border-radius: var(--radius-xl); box-shadow: var(--sku-btn-secondary-shadow);
}
.empty-icon { font-size: 34px; color: var(--neutral-300); margin-bottom: 2px; }
.empty-title { font-size: var(--text-sm); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }
.empty-sub   { font-size: var(--text-xs); color: var(--text-secondary); margin: 0; }

/* Notification List — Compact 3D Skeuomorphic Tiles */
.notif-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 2px;
  overflow: visible;
}

.notif-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  background: var(--bg-base);
  border: none;
  box-shadow: var(--sku-btn-secondary-shadow);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  position: relative;
  user-select: none;
}

.notif-card:hover {
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
  transform: translateY(-2px);
}

.notif-card:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
  transform: translateY(1px);
}

.notif-card.unread {
  border: none !important;
}

.notif-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow);
  color: var(--text-primary);
  transition: all var(--duration-base) var(--ease-out);
}

.notif-card:hover .notif-icon-wrap {
  transform: scale(1.05);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}

.notif-icon-wrap.info,
.notif-icon-wrap.success,
.notif-icon-wrap.warning,
.notif-icon-wrap.error {
  color: var(--text-primary);
}

.notif-body { flex: 1; min-width: 0; }
.notif-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px; }
.notif-title { font-size: 13px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em; transition: color var(--duration-base); }
.notif-card:hover .notif-title { color: var(--orange-accent); }
.notif-time  { font-size: 11px; color: var(--text-secondary); flex-shrink: 0; display: flex; align-items: center; gap: 4px; font-weight: 500; }
.notif-msg   { font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.4; font-weight: 400; }

.unread-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--orange-accent);
  flex-shrink: 0; box-shadow: 0 0 6px var(--orange-glow);
}

.btn-ghost {
  background: var(--bg-base); color: var(--text-secondary); border: none;
  padding: 6px 14px; border-radius: var(--radius-pill); font-size: 12px;
  font-weight: var(--weight-bold); cursor: pointer; display: flex; align-items: center; gap: 6px;
  box-shadow: var(--sku-btn-secondary-shadow); transition: all var(--duration-base);
}
.btn-ghost:hover:not(:disabled) { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); transform: translateY(-1px); }
.btn-ghost:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
