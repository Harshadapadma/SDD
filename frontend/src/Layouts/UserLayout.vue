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
        <div class="footer-avatar" @click="$router.push('/profile')" title="Go to Profile">{{ userInitial }}</div>
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
            <transition name="u-panel">
              <div class="u-notif-panel" v-if="panelOpen">

                <!-- Panel Header -->
                <div class="u-panel-header">
                  <span class="u-panel-title">Notifications</span>
                  <div class="u-panel-actions">
                    <button
                      class="u-panel-icon-btn"
                      :title="isMuted ? 'Unmute popups' : 'Mute popups'"
                      @click="toggleMute"
                    >
                      <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? '#ef4444' : undefined }"></i>
                    </button>
                    <button class="u-panel-icon-btn" title="Mark all read" @click="markAllRead" :disabled="unreadCount === 0">
                      <i class="fas fa-check-double"></i>
                    </button>
                    <button class="u-panel-icon-btn" title="View all" @click="$router.push('/notifications'); panelOpen = false">
                      <i class="fas fa-arrow-up-right-from-square"></i>
                    </button>
                  </div>
                </div>

                <!-- Muted banner -->
                <div class="u-muted-banner" v-if="isMuted">
                  <i class="fas fa-bell-slash"></i> Popups are muted
                </div>

                <!-- Panel Items -->
                <div class="u-panel-body">
                  <div v-if="notifications.filter(n => !n.is_read).length === 0" class="u-panel-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>No unread notifications</p>
                  </div>

                  <div
                    v-for="n in notifications.filter(n => !n.is_read).slice(0, 20)"
                    :key="n.id"
                    :class="['u-panel-item', n.type.toLowerCase(), { unread: !n.is_read }]"
                    @click="markRead(n.id)"
                  >
                    <div class="u-panel-item-icon">
                      <i :class="['fas', typeIcon(n.type)]"></i>
                    </div>
                    <div class="u-panel-item-body">
                      <div class="u-panel-item-header">
                        <div class="u-panel-item-title">{{ n.title }}</div>
                        <div class="u-panel-item-time">{{ formatTime(n.created_at) }}</div>
                      </div>
                      <div class="u-panel-item-msg">{{ n.message }}</div>
                    </div>
                    <div class="u-panel-unread-dot" v-if="!n.is_read"></div>
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
      <div class="u-toast-stack">
        <div
          v-for="t in toasts"
          :key="t._tid"
          :class="['u-toast', t.type.toLowerCase(), { leaving: t.leaving }]"
        >
          <div class="u-toast-icon">
            <i :class="['fas', typeIcon(t.type)]"></i>
          </div>
          <div class="u-toast-body">
            <div class="u-toast-title">{{ t.title }}</div>
            <div class="u-toast-msg">{{ t.message }}</div>
          </div>
          <button class="u-toast-close" @click="dismissToast(t._tid)">
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

.u-notif-panel {
  --u-accent: 61, 90, 128;
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 360px;
  border-radius: 20px;
  background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)), rgba(var(--u-accent), 0.4);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(var(--u-accent), 0.2);
  box-shadow: 
    0 8px 32px rgba(var(--u-accent), 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1),
    inset 0 0 12px 6px rgba(var(--u-accent), 0.20);
  z-index: 50;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: top right;
  color: #1e293b;
}

.u-panel-enter-active, .u-panel-leave-active { transition: opacity 0.2s, transform 0.2s; }
.u-panel-enter-from, .u-panel-leave-to { opacity: 0; transform: scale(0.96) translateY(-4px); }

.u-panel-header {
  padding: 14px 18px;
  background: rgba(var(--u-accent), 0.08);
  border-bottom: 1px solid rgba(var(--u-accent), 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.u-panel-title { font-weight: 700; font-size: 14px; color: #1e293b; }
.user-title { color: #3d5a80; }
.u-panel-actions { display: flex; gap: 4px; }
.u-panel-icon-btn {
  background: none; border: none; padding: 6px; border-radius: 8px;
  cursor: pointer; color: #3d5a80; transition: all 0.2s;
}
.u-panel-icon-btn:hover { background: rgba(61,90,128,0.12); }
.u-panel-icon-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.u-muted-banner {
  background: rgba(254, 226, 226, 0.8); color: #ef4444; padding: 8px 16px; font-size: 12px;
  font-weight: 600; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid rgba(239, 68, 68, 0.2);
}

.u-panel-body { max-height: 400px; overflow-y: auto; }
.u-panel-empty { padding: 40px; text-align: center; color: #64748b; }
.u-panel-empty i { font-size: 32px; margin-bottom: 10px; }

.u-panel-item {
  display: flex;
  margin: 6px 10px;
  padding: 10px 14px;
  gap: 10px;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;

  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 20px;
  border: 1px solid rgba(var(--u-accent), 0.15);
  box-shadow: 
    0 4px 16px rgba(var(--u-accent), 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1);
}

.u-panel-item::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
}

.u-panel-item::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8), transparent, rgba(255, 255, 255, 0.3));
}

.u-panel-item:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateY(-1px);
  box-shadow: 
    0 8px 24px rgba(var(--u-accent), 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1);
}

.u-panel-item.unread {
  background: rgba(255, 255, 255, 0.90);
}

.u-panel-item.info { background: rgba(59, 130, 246, 0.10); }
.u-panel-item.success { background: rgba(34, 197, 94, 0.10); }
.u-panel-item.warning { background: rgba(245, 158, 11, 0.10); }
.u-panel-item.error { background: rgba(239, 68, 68, 0.10); }

.u-panel-item-icon {
  width: 32px; height: 32px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0; font-size: 14px;
}
.u-panel-item.info .u-panel-item-icon { background: #e0f2fe; color: #0284c7; }
.u-panel-item.success .u-panel-item-icon { background: #dcfce7; color: #15803d; }
.u-panel-item.warning .u-panel-item-icon { background: #fef3cd; color: #b45309; }
.u-panel-item.error .u-panel-item-icon { background: #fee2e2; color: #b91c1c; }

.u-panel-item-body { flex: 1; min-width: 0; }
.u-panel-item-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 2px;
}
.u-panel-item-title { font-size: 12.5px; font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.u-panel-item-msg { font-size: 12px; color: #475569; line-height: 1.4; margin-bottom: 4px; }
.u-panel-item-time {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0.8;
}

.u-panel-unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(var(--u-accent), 1);
  box-shadow: 0 0 6px rgba(var(--u-accent), 0.6);
  flex-shrink: 0;
}

/* ─── Toasts ────────────────────────────────────────────────── */
.u-toast-stack {
  position: fixed; top: 70px; right: 24px; z-index: 100;
  display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}

.u-toast {
  pointer-events: auto;
  width: 340px;
  border-radius: 20px;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(24px) saturate(150%);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
  transition: all 0.2s ease;
  animation: utoastEnter 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.u-toast::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
}

.u-toast::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8), transparent, rgba(255, 255, 255, 0.3));
}

.u-toast.leaving {
  animation: utoastLeave 0.3s ease-in forwards;
}

.u-toast.info { --u-t-accent: 234, 179, 8; }
.u-toast.success { --u-t-accent: 34, 197, 94; }
.u-toast.warning { --u-t-accent: 245, 158, 11; }
.u-toast.error { --u-t-accent: 239, 68, 68; }

.u-toast {
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(var(--u-t-accent), 0.25);
  box-shadow: 
    0 12px 40px rgba(var(--u-t-accent), 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 rgba(255, 255, 255, 0.15),
    inset 0 0 14px 7px rgba(var(--u-t-accent), 0.15);
}

.u-toast-icon { width: 32px; height: 32px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.u-toast.info .u-toast-icon { color: #a16207; background: #fef9c3; }
.u-toast.success .u-toast-icon { color: #15803d; background: #dcfce7; }
.u-toast.warning .u-toast-icon { color: #b45309; background: #fef3cd; }
.u-toast.error .u-toast-icon { color: #b91c1c; background: #fee2e2; }

.u-toast-body { flex: 1; }
.u-toast-title { font-weight: 700; font-size: 13px; color: #1e293b; margin-bottom: 4px; }
.u-toast-msg { font-size: 12px; color: #475569; line-height: 1.4; }

.u-toast-close {
  background: none; border: none; padding: 4px; color: #64748b;
  cursor: pointer; border-radius: 6px; transition: background 0.2s, color 0.2s;
}
.u-toast-close:hover { background: rgba(0, 0, 0, 0.05); color: #1e293b; }

@keyframes utoastEnter {
  from { opacity: 0; transform: translateX(40px) scale(0.95); }
  to   { opacity: 1; transform: translateX(0) scale(1); }
}
@keyframes utoastLeave {
  from { opacity: 1; transform: translateX(0) scale(1); }
  to   { opacity: 0; transform: translateX(40px) scale(0.95); }
}
</style>