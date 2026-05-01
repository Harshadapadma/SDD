<template>
  <div class="page">

    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Notifications</h1>
        <p class="page-sub">System alerts and activity updates</p>
      </div>
      <button class="btn-ghost" @click="markAllRead" :disabled="!hasUnread">
        <i class="fas fa-check-double"></i> Mark All Read
      </button>
    </div>

    <!-- STATS -->
    <div class="stats-row">
      <div class="stat-card">
        <i class="fas fa-bell stat-icon green"></i>
        <div><div class="stat-val">{{ notifications.length }}</div><div class="stat-label">Total</div></div>
      </div>
      <div class="stat-card">
        <i class="fas fa-envelope stat-icon blue"></i>
        <div><div class="stat-val">{{ unreadCount }}</div><div class="stat-label">Unread</div></div>
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
        {{ t.label }}
      </button>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading notifications…
    </div>

    <!-- EMPTY -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="fas fa-bell-slash empty-icon"></i>
      <p>No notifications here.</p>
    </div>

    <!-- NOTIFICATION LIST -->
    <div v-else class="notif-list">
      <div
        v-for="n in filtered"
        :key="n.id"
        :class="['notif-card', n.type.toLowerCase(), { unread: !n.is_read }]"
        @click="markRead(n)"
      >
        <div class="notif-icon-wrap">
          <i :class="['fas', typeIcon(n.type)]"></i>
        </div>
        <div class="notif-body">
          <div class="notif-top">
            <span class="notif-title">{{ n.title }}</span>
            <span class="notif-time">{{ formatTime(n.created_at) }}</span>
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
import api from '../../api/client'

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
  flex: 1; max-width: 180px;
  display: flex; align-items: center; gap: 14px;
  background: #f5fbf7; border: 1.5px solid #e0f0e8;
  border-radius: 16px; padding: 16px 20px;
}
.stat-icon { font-size: 20px; }
.stat-icon.green { color: #2f7d65; }
.stat-icon.blue  { color: #3b82f6; }
.stat-val   { font-size: 22px; font-weight: 700; color: #1a2e1a; }
.stat-label { font-size: 12px; color: #7a9a7a; }

/* ─── Tabs ───────────────────────────────────────────────────── */
.tab-bar { display: flex; gap: 8px; flex-wrap: wrap; }
.tab-btn {
  padding: 8px 16px; border-radius: 999px; border: 1.5px solid #e0e0e0;
  background: white; font-size: 13px; font-weight: 500; cursor: pointer;
  display: flex; align-items: center; gap: 6px; transition: all 0.2s; color: #555;
}
.tab-btn.active { background: #2f7d65; color: white; border-color: #2f7d65; }
.tab-btn:hover:not(.active) { border-color: #2f7d65; color: #2f7d65; }

/* ─── States ─────────────────────────────────────────────────── */
.loading-state { text-align: center; padding: 40px; color: #999; font-size: 14px; }
.empty-state {
  text-align: center; padding: 60px 0; color: #bbb;
  animation: fadeInUp 0.3s ease;
}
.empty-icon { font-size: 48px; margin-bottom: 14px; display: block; }

/* ─── Notification cards ─────────────────────────────────────── */
.notif-list { display: flex; flex-direction: column; gap: 10px; }

.notif-card {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 16px 18px; border-radius: 16px;
  border: 1.5px solid #e8f0ea; background: #fff;
  cursor: pointer; transition: all 0.2s;
  position: relative;
  animation: fadeInUp 0.35s ease both;
}
.notif-card:hover { border-color: #b7e4ca; box-shadow: 0 2px 12px rgba(47,125,101,0.08); transform: translateX(3px); }

.notif-card.unread { background: #f5fbf7; border-color: #c8e6d4; }

/* left icon colour by type */
.notif-card.info    .notif-icon-wrap { background: #dbeafe; color: #1d4ed8; }
.notif-card.success .notif-icon-wrap { background: #dcfce7; color: #15803d; }
.notif-card.warning .notif-icon-wrap { background: #fef3cd; color: #b45309; }
.notif-card.error   .notif-icon-wrap { background: #fee2e2; color: #b91c1c; }

.notif-icon-wrap {
  width: 38px; height: 38px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px;
}

.notif-body { flex: 1; min-width: 0; }

.notif-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 4px;
}
.notif-title { font-size: 13px; font-weight: 700; color: #1a2e1a; }
.notif-time  { font-size: 11px; color: #aaa; flex-shrink: 0; }
.notif-msg   { font-size: 13px; color: #555; margin: 0; line-height: 1.5; }

.unread-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #2f7d65;
  flex-shrink: 0; margin-top: 4px;
}

/* ─── Buttons ────────────────────────────────────────────────── */
.btn-ghost {
  background: #f3f3f3; color: #444; border: none;
  padding: 10px 20px; border-radius: 999px; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: background 0.2s;
}
.btn-ghost:hover:not(:disabled) { background: #e8e8e8; }
.btn-ghost:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
