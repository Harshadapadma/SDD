<template>
  <div class="layout" @click="closePanel">

    <!-- SIDEBAR -->
    <aside :class="['sidebar', { collapsed: isCollapsed }]">

      <!-- TOGGLE BUTTON -->
      <button class="hamburger" @click.stop="toggleSidebar">
        <i class="fas fa-bars"></i>
      </button>

      <!-- BRAND BLOCK -->
      <div class="brand-block">
        <img :src="logo" alt="Negen Logo" class="brand-logo" />
        <template v-if="!isCollapsed">
          <span class="brand-name">Negen Vault</span>
          <span class="brand-role">{{ userRole }}</span>
        </template>
      </div>

      <!-- DIVIDER -->
      <div class="divider" v-if="!isCollapsed"></div>

      <!-- NAV -->
      <nav class="nav">
        <div class="nav-item" :class="{ active: $route.path === '/' }" @click="$router.push('/')">
          <i class="fas fa-chart-pie"></i>
          <span v-if="!isCollapsed">Dashboard</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/records' }" @click="$router.push('/records')">
          <i class="fas fa-folder-open"></i>
          <span v-if="!isCollapsed">Records</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/requests' }" @click="$router.push('/requests')">
          <i class="fas fa-paper-plane"></i>
          <span v-if="!isCollapsed">Requests</span>
        </div>
      </nav>

      <!-- FOOTER -->
      <div class="sidebar-footer">
        <div class="footer-avatar" @click="$router.push('/records')">{{ userInitial }}</div>
        <div class="footer-info" v-if="!isCollapsed">
          <span class="footer-name">{{ userName }}</span>
          <span class="footer-email">{{ userEmail }}</span>
        </div>
        <button class="logout-btn" v-if="!isCollapsed" @click="logout">
          <i class="fas fa-sign-out-alt"></i>
        </button>
      </div>

    </aside>

    <!-- MAIN CONTENT -->
    <main class="content">

      <!-- TOPBAR -->
      <div class="topbar">
        <div class="topbar-right">

          <!-- ─── BELL BUTTON ───────────────────────────────── -->
          <div class="bell-wrap" @click.stop>
            <button class="icon-btn" @click="togglePanel" title="Notifications" :class="{ active: panelOpen }">
              <i class="fas fa-bell"></i>
              <span class="badge" v-if="unreadCount > 0">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
            </button>

            <!-- ─── NOTIFICATION PANEL ─────────────────────── -->
            <transition name="panel">
              <div class="notif-panel" v-if="panelOpen">

                <!-- Panel Header -->
                <div class="panel-header">
                  <span class="panel-title">Notifications</span>
                  <div class="panel-actions">
                    <button
                      class="panel-icon-btn"
                      :title="isMuted ? 'Unmute popups' : 'Mute popups'"
                      @click="toggleMute"
                    >
                      <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? '#ef4444' : undefined }"></i>
                    </button>
                    <button class="panel-icon-btn" title="Mark all read" @click="markAllRead" :disabled="unreadCount === 0">
                      <i class="fas fa-check-double"></i>
                    </button>
                    <button class="panel-icon-btn" title="View all" @click="$router.push('/notifications'); panelOpen = false">
                      <i class="fas fa-arrow-up-right-from-square"></i>
                    </button>
                  </div>
                </div>

                <!-- Muted banner -->
                <div class="muted-banner" v-if="isMuted">
                  <i class="fas fa-bell-slash"></i> Popups are muted
                </div>

                <!-- Panel Items -->
                <div class="panel-body">
                  <div v-if="notifications.length === 0" class="panel-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications yet</p>
                  </div>

                  <div
                    v-for="n in notifications.slice(0, 20)"
                    :key="n.id"
                    :class="['panel-item', n.type.toLowerCase(), { unread: !n.is_read }]"
                    @click="markRead(n.id)"
                  >
                    <div class="panel-item-icon">
                      <i :class="['fas', typeIcon(n.type)]"></i>
                    </div>
                    <div class="panel-item-body">
                      <div class="panel-item-title">{{ n.title }}</div>
                      <div class="panel-item-msg">{{ n.message }}</div>
                      <div class="panel-item-time">{{ formatTime(n.created_at) }}</div>
                    </div>
                    <div class="panel-unread-dot" v-if="!n.is_read"></div>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <div class="profile-pill" @click="$router.push('/profile')" style="cursor: pointer;">{{ userInitial }}</div>
        </div>
      </div>

      <!-- PAGE CONTENT -->
      <div class="page-body">
        <router-view />
      </div>

    </main>

    <!-- ─── TOAST POPUPS (top-right, below bell) ────────────── -->
    <teleport to="body">
      <div class="toast-stack">
        <div
          v-for="t in toasts"
          :key="t._tid"
          :class="['toast', t.type.toLowerCase(), { leaving: t.leaving }]"
        >
          <div class="toast-icon">
            <i :class="['fas', typeIcon(t.type)]"></i>
          </div>
          <div class="toast-body">
            <div class="toast-title">{{ t.title }}</div>
            <div class="toast-msg">{{ t.message }}</div>
          </div>
          <button class="toast-close" @click="dismissToast(t._tid)">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import logo from '../assets/logo.png'
import { useNotifications } from '../composables/useNotifications'
import api from '../api/client'

const router = useRouter()
const isCollapsed = ref(false)
const panelOpen   = ref(false)

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const userName = computed(() => user.value?.name || 'User')
const userEmail = computed(() => user.value?.email || '')
const userRole = computed(() => {
  if (user.value?.role === 'COLLABORATOR') return 'Collaborator'
  if (user.value?.role === 'VIEWER') return 'Viewer'
  return 'User'
})
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())

async function fetchProfile() {
  try {
    const res = await api.get('auth/profile/')
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  } catch (e) {
    console.error("Failed to fetch profile", e)
  }
}

const {
  notifications, unreadCount, isMuted, toasts,
  startPolling, stopPolling,
  markRead, markAllRead, toggleMute, dismissToast,
  typeIcon, formatTime,
} = useNotifications()

const toggleSidebar = () => { isCollapsed.value = !isCollapsed.value }
const togglePanel   = () => { panelOpen.value = !panelOpen.value }
const closePanel    = () => { panelOpen.value = false }

const logout = () => {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(() => {
  startPolling()
  fetchProfile()
})
onUnmounted(stopPolling)
</script>

<style scoped>
/* ─── Layout ───────────────────────────────────────────────── */
.layout {
  display: flex;
  height: 100vh;
  /* Linen Blue Background */
  background: #eef2f6;
  font-family: system-ui, -apple-system, sans-serif;
  color: #1e293b;
}

/* ─── Sidebar ───────────────────────────────────────────────── */
@keyframes sidebarSlideIn {
  from { opacity: 0; transform: translateX(-24px); }
  to   { opacity: 1; transform: translateX(0); }
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-5px); }
}

@keyframes bellShake {
  0%, 100% { transform: rotate(0deg); }
  20%       { transform: rotate(15deg); }
  40%       { transform: rotate(-12deg); }
  60%       { transform: rotate(8deg); }
  80%       { transform: rotate(-5deg); }
}

@keyframes badgePulse {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.25); }
}

@keyframes navItemIn {
  from { opacity: 0; transform: translateX(-10px); }
  to   { opacity: 1; transform: translateX(0); }
}

.sidebar {
  width: 230px;
  min-width: 230px;
  margin: 14px;
  border-radius: 22px;
  padding: 18px 14px;

  display: flex;
  flex-direction: column;
  gap: 10px;

  /* Primary Linen Blue */
  background: #3d5a80;
  color: white;

  transition: width 0.35s cubic-bezier(0.4,0,0.2,1),
              min-width 0.35s cubic-bezier(0.4,0,0.2,1),
              padding 0.35s cubic-bezier(0.4,0,0.2,1);
  overflow: hidden;
  animation: sidebarSlideIn 0.45s ease both;
}

.sidebar.collapsed {
  width: 58px;
  min-width: 58px;
  padding: 18px 8px;
  align-items: center;
}

/* ─── Toggle Button ─────────────────────────────────────────── */
.hamburger {
  background: rgba(255, 255, 255, 0.12);
  border: none;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: white;
  align-self: flex-start;
  transition: background 0.2s;
  flex-shrink: 0;
  width: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar.collapsed .hamburger {
  align-self: center;
}

.hamburger:hover {
  background: rgba(255, 255, 255, 0.22);
}

/* ─── Brand ─────────────────────────────────────────────────── */
.brand-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 6px 4px;
  white-space: nowrap;
  overflow: hidden;
  animation: fadeIn 0.5s ease 0.15s both;
}

.brand-logo {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: contain;
  background: #ffffff;
  padding: 8px;
  flex-shrink: 0;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
  animation: logoFloat 3.5s ease-in-out infinite;
}

.sidebar.collapsed .brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  padding: 4px;
}

.brand-name {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.3px;
  white-space: nowrap;
  text-align: center;
}

.brand-role {
  font-size: 13px;
  opacity: 0.75;
  font-weight: 500;
  white-space: nowrap;
  text-align: center;
  color: #e0f2fe;
}

/* ─── Divider ───────────────────────────────────────────────── */
.divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.15);
  margin: 2px 4px;
}

/* ─── Nav ───────────────────────────────────────────────────── */
.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 999px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s, color 0.2s, transform 0.15s;
  white-space: nowrap;
  overflow: hidden;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}

.nav-item:nth-child(1) { animation: navItemIn 0.4s ease 0.2s both; }
.nav-item:nth-child(2) { animation: navItemIn 0.4s ease 0.3s both; }
.nav-item:nth-child(3) { animation: navItemIn 0.4s ease 0.4s both; }

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 11px 0;
  width: 38px;
}

.nav-item i {
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  font-size: 15px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transform: translateX(3px);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.18);
  color: white;
}

.sidebar.collapsed .nav-item:hover {
  transform: scale(1.1);
}

/* ─── Sidebar Footer ────────────────────────────────────────── */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  margin-top: auto;
  overflow: hidden;
  white-space: nowrap;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  transition: background 0.2s;
}

.sidebar-footer:hover {
  background: rgba(255, 255, 255, 0.14);
}

.sidebar.collapsed .sidebar-footer {
  justify-content: center;
  padding: 8px;
  background: transparent;
  width: 38px;
  border-radius: 50%;
}

.footer-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: white;
  color: #3d5a80;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
}

.footer-avatar:hover {
  box-shadow: 0 0 0 3px rgba(255,255,255,0.3);
  transform: scale(1.08);
}

.footer-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.footer-name {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.footer-email {
  font-size: 10px;
  opacity: 0.65;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  color: white;
}

/* ─── Main Content ──────────────────────────────────────────── */
.content {
  flex: 1;
  margin: 14px 14px 14px 0;
  padding: 20px 24px;
  border-radius: 22px;
  background: #ffffff;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  min-width: 0;
  animation: fadeIn 0.4s ease 0.1s both;
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
}

/* ─── Topbar ────────────────────────────────────────────────── */
.topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 24px;
  position: relative;
  z-index: 10;
  animation: fadeInDown 0.4s ease 0.2s both;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ─── Notification Button ───────────────────────────────────── */
.icon-btn {
  position: relative;
  background: #f1f5f9;
  border: none;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #475569;
  font-size: 15px;
  transition: background 0.2s, color 0.2s, transform 0.2s;
}

.icon-btn:hover {
  background: #3d5a80;
  color: white;
  transform: scale(1.08);
}

.icon-btn:hover i {
  animation: bellShake 0.5s ease;
}

.icon-btn.active {
  background: #3d5a80;
  color: white;
}

.badge {
  position: absolute;
  top: 1px;
  right: 1px;
  background: #ee6c4d; /* Warm orange */
  color: white;
  font-size: 9px;
  font-weight: 700;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: badgePulse 2s ease-in-out infinite;
}

/* ─── Profile Pill ──────────────────────────────────────────── */
.profile-pill {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #3d5a80;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.profile-pill:hover {
  transform: scale(1.1);
  box-shadow: 0 0 0 3px rgba(61,90,128,0.25);
}

/* ─── Page content area ─────────────────────────────────────── */
.page-body {
  flex: 1;
  overflow-y: auto;
  animation: fadeInUp 0.4s ease 0.3s both;
}

/* ─── Notification Panel ────────────────────────────────────── */
.bell-wrap { position: relative; }

.notif-panel {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 360px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.12), 0 2px 10px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: top right;
}

.panel-enter-active, .panel-leave-active { transition: opacity 0.2s, transform 0.2s; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: scale(0.96) translateY(-4px); }

.panel-header {
  padding: 14px 18px; border-bottom: 1px solid #f1f5f9; display: flex;
  justify-content: space-between; align-items: center; background: #f8fafc;
}
.panel-title { font-weight: 700; font-size: 14px; color: #1e293b; }
.panel-actions { display: flex; gap: 4px; }
.panel-icon-btn {
  background: none; border: none; padding: 6px; border-radius: 8px;
  cursor: pointer; color: #64748b; transition: all 0.2s;
}
.panel-icon-btn:hover { background: #e2e8f0; color: #334155; }
.panel-icon-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.muted-banner {
  background: #fef2f2; color: #ef4444; padding: 8px 16px; font-size: 12px;
  font-weight: 600; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #fee2e2;
}

.panel-body { max-height: 400px; overflow-y: auto; }
.panel-empty { padding: 40px; text-align: center; color: #cbd5e1; }
.panel-empty i { font-size: 32px; margin-bottom: 10px; }

.panel-item {
  display: flex; padding: 14px 18px; gap: 12px; border-bottom: 1px solid #f8fafc;
  cursor: pointer; transition: background 0.2s;
}
.panel-item:hover { background: #f1f5f9; }
.panel-item.unread { background: #eff6ff; }

.panel-item-icon {
  width: 32px; height: 32px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0; font-size: 13px;
}
.panel-item.info .panel-item-icon { background: #e0f2fe; color: #0284c7; }
.panel-item.success .panel-item-icon { background: #dcfce7; color: #15803d; }
.panel-item.warning .panel-item-icon { background: #fef3cd; color: #b45309; }
.panel-item.error .panel-item-icon { background: #fee2e2; color: #b91c1c; }

.panel-item-body { flex: 1; }
.panel-item-title { font-size: 12px; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
.panel-item-msg { font-size: 12px; color: #475569; line-height: 1.4; margin-bottom: 4px; }
.panel-item-time { font-size: 10px; color: #94a3b8; }
.panel-unread-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #3d5a80;
  margin-top: 4px; flex-shrink: 0;
}

/* ─── Toasts ────────────────────────────────────────────────── */
.toast-stack {
  position: fixed; top: 70px; right: 24px; z-index: 100;
  display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}

.toast {
  background: white; border-radius: 12px; padding: 14px 16px; width: 300px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.05);
  display: flex; gap: 12px; align-items: flex-start; pointer-events: auto;
  border-left: 4px solid #3d5a80;
  animation: toastEnter 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.toast.leaving { animation: toastLeave 0.3s ease-in forwards; }

.toast.info { border-left-color: #3b82f6; }
.toast.success { border-left-color: #10b981; }
.toast.warning { border-left-color: #f59e0b; }
.toast.error { border-left-color: #ef4444; }

.toast-icon { font-size: 18px; margin-top: 2px; }
.toast.info .toast-icon { color: #3b82f6; }
.toast.success .toast-icon { color: #10b981; }
.toast.warning .toast-icon { color: #f59e0b; }
.toast.error .toast-icon { color: #ef4444; }

.toast-body { flex: 1; }
.toast-title { font-weight: 700; font-size: 13px; color: #1e293b; margin-bottom: 4px; }
.toast-msg { font-size: 12px; color: #64748b; line-height: 1.4; }

.toast-close {
  background: none; border: none; padding: 4px; color: #94a3b8;
  cursor: pointer; border-radius: 4px; transition: background 0.2s, color 0.2s;
}
.toast-close:hover { background: #f1f5f9; color: #1e293b; }

@keyframes toastEnter {
  from { opacity: 0; transform: translateX(40px) scale(0.95); }
  to   { opacity: 1; transform: translateX(0) scale(1); }
}
@keyframes toastLeave {
  from { opacity: 1; transform: translateX(0) scale(1); }
  to   { opacity: 0; transform: translateX(40px) scale(0.95); }
}
</style>