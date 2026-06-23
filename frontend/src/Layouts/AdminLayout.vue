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
          <span class="brand-name">Negen SDD</span>
          <span class="brand-role">Administrator</span>
        </template>
      </div>

      <!-- DIVIDER -->
      <div class="divider" v-if="!isCollapsed"></div>

      <!-- NAV -->
      <nav class="nav">
        <div class="nav-item" :class="{ active: $route.path === '/' }" @click="$router.push('/')">
          <i class="fas fa-chart-line"></i>
          <span v-if="!isCollapsed">Dashboard</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/records' }" @click="$router.push('/records')">
          <i class="fas fa-database"></i>
          <span v-if="!isCollapsed">Records</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/users' }" @click="$router.push('/users')">
          <i class="fas fa-users"></i>
          <span v-if="!isCollapsed">Users</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/requests' }" @click="$router.push('/requests')">
          <i class="fas fa-clipboard-check"></i>
          <span v-if="!isCollapsed">Requests</span>
        </div>
      </nav>

      <!-- FOOTER -->
      <div class="sidebar-footer">
        <div class="footer-avatar" @click="$router.push('/profile')" title="Go to Profile">{{ userName.charAt(0).toUpperCase() }}</div>
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
            <transition name="a-panel">
              <div class="a-notif-panel" v-if="panelOpen">

                <!-- Panel Header -->
                <div class="a-panel-header">
                  <span class="a-panel-title admin-title">Notifications</span>
                  <div class="a-panel-actions">
                    <!-- Mute toggle -->
                    <button
                      class="a-panel-icon-btn"
                      :title="isMuted ? 'Unmute popups' : 'Mute popups'"
                      @click="toggleMute"
                    >
                      <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? '#ef4444' : undefined }"></i>
                    </button>
                    <!-- Mark all read -->
                    <button class="a-panel-icon-btn" title="Mark all read" @click="markAllRead" :disabled="unreadCount === 0">
                      <i class="fas fa-check-double"></i>
                    </button>
                    <!-- View all -->
                    <button class="a-panel-icon-btn" title="View all" @click="$router.push('/notifications'); panelOpen = false">
                      <i class="fas fa-arrow-up-right-from-square"></i>
                    </button>
                  </div>
                </div>

                <!-- Muted banner -->
                <div class="a-muted-banner" v-if="isMuted">
                  <i class="fas fa-bell-slash"></i> Popups are muted
                </div>

                <!-- Panel Items -->
                <div class="a-panel-body">
                  <div v-if="notifications.filter(n => !n.is_read).length === 0" class="a-panel-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>No unread notifications</p>
                  </div>

                  <div
                    v-for="n in notifications.filter(n => !n.is_read).slice(0, 20)"
                    :key="n.id"
                    :class="['a-panel-item', n.type.toLowerCase(), { unread: !n.is_read }]"
                    @click="markRead(n.id)"
                  >
                    <div class="a-panel-item-icon">
                      <i :class="['fas', typeIcon(n.type)]"></i>
                    </div>
                    <div class="a-panel-item-body">
                      <div class="a-panel-item-header">
                        <div class="a-panel-item-title">{{ n.title }}</div>
                        <div class="a-panel-item-time">{{ formatTime(n.created_at) }}</div>
                      </div>
                      <div class="a-panel-item-msg">{{ n.message }}</div>
                    </div>
                    <div class="a-panel-unread-dot" v-if="!n.is_read"></div>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <div class="profile-pill" @click="$router.push('/profile')" style="cursor: pointer;" title="Go to Profile">{{ userName.charAt(0).toUpperCase() }}</div>
        </div>
      </div>

      <!-- PAGE CONTENT -->
      <div class="page-body">
        <router-view />
      </div>

    </main>

    <!-- ─── TOAST POPUPS (top-right, below bell) ────────────── -->
    <teleport to="body">
      <div class="a-toast-stack">
        <div
          v-for="t in toasts"
          :key="t._tid"
          :class="['a-toast', t.type.toLowerCase(), { leaving: t.leaving }]"
        >
          <div class="a-toast-icon">
            <i :class="['fas', typeIcon(t.type)]"></i>
          </div>
          <div class="a-toast-body">
            <div class="a-toast-title">{{ t.title }}</div>
            <div class="a-toast-msg">{{ t.message }}</div>
          </div>
          <button class="a-toast-close" @click="dismissToast(t._tid)">
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
const userName = computed(() => user.value?.name || 'Admin User')
const userEmail = computed(() => user.value?.email || 'admin@negen.com')

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
  background: #e6f0ec;
  font-family: system-ui, -apple-system, sans-serif;
  color: #2f3e2f;
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

  background: #2f7d65;
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
  background: rgba(255, 255, 255, 0.15);
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
  background: rgba(255, 255, 255, 0.28);
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
}

/* ─── Divider ───────────────────────────────────────────────── */
.divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.18);
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
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s, color 0.2s, transform 0.15s;
  white-space: nowrap;
  overflow: hidden;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}

/* staggered entrance for each nav item */
.nav-item:nth-child(1) { animation: navItemIn 0.4s ease 0.2s both; }
.nav-item:nth-child(2) { animation: navItemIn 0.4s ease 0.3s both; }
.nav-item:nth-child(3) { animation: navItemIn 0.4s ease 0.4s both; }
.nav-item:nth-child(4) { animation: navItemIn 0.4s ease 0.5s both; }

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
  background: rgba(255, 255, 255, 0.15);
  color: white;
  transform: translateX(3px);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.22);
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
  background: rgba(255, 255, 255, 0.1);
  margin-top: auto;
  overflow: hidden;
  white-space: nowrap;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  transition: background 0.2s;
}

.sidebar-footer:hover {
  background: rgba(255, 255, 255, 0.16);
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
  color: #2f7d65;
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
  box-shadow: 0 0 0 3px rgba(255,255,255,0.4);
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
  background: #2f7d65;
  color: white;
  transform: scale(1.08);
}

.icon-btn:hover i {
  animation: bellShake 0.5s ease;
}

.badge {
  position: absolute;
  top: 1px;
  right: 1px;
  background: #ee6c4d; /* Warm orange — matches user panel */
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
  background: #2f7d65;
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
  box-shadow: 0 0 0 3px rgba(47,125,101,0.3);
}

/* ─── Page content area ─────────────────────────────────────── */
.page-body {
  flex: 1;
  overflow-y: auto;
  animation: fadeInUp 0.4s ease 0.3s both;
}

/* ─── Notification Panel ────────────────────────────────────── */
.bell-wrap {
  position: relative;
}

.icon-btn.active {
  background: #2f7d65;
  color: white;
}

.a-notif-panel {
  --a-accent: 47, 125, 101;
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 360px;
  border-radius: 20px;
  background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)), rgba(var(--a-accent), 0.4);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(var(--a-accent), 0.2);
  box-shadow: 
    0 8px 32px rgba(var(--a-accent), 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1),
    inset 0 0 12px 6px rgba(var(--a-accent), 0.15);
  z-index: 50;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: top right;
  color: #1e293b;
}

.a-panel-enter-active, .a-panel-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.a-panel-enter-from, .a-panel-leave-to {
  opacity: 0;
  transform: scale(0.96) translateY(-4px);
}

.a-panel-header {
  padding: 14px 18px;
  background: rgba(var(--a-accent), 0.08);
  border-bottom: 1px solid rgba(var(--a-accent), 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.a-panel-title { font-weight: 700; font-size: 14px; color: #1e293b; }
.admin-title { color: #2f7d65; }

.a-panel-actions {
  display: flex;
  gap: 4px;
}

.a-panel-icon-btn {
  background: none;
  border: none;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  color: #2f7d65;
  transition: all 0.2s;
}
.a-panel-icon-btn:hover {
  background: rgba(47,125,101,0.12);
}
.a-panel-icon-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.a-muted-banner {
  background: rgba(254, 226, 226, 0.8);
  color: #ef4444;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(239, 68, 68, 0.2);
}

.a-panel-body {
  max-height: 400px;
  overflow-y: auto;
}
.a-panel-empty {
  padding: 40px;
  text-align: center;
  color: #64748b;
}
.a-panel-empty i {
  font-size: 32px;
  margin-bottom: 10px;
}

.a-panel-item {
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
  border: 1px solid rgba(var(--a-accent), 0.15);
  box-shadow: 
    0 4px 16px rgba(var(--a-accent), 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1);
}

.a-panel-item::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
}

.a-panel-item::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8), transparent, rgba(255, 255, 255, 0.3));
}

.a-panel-item:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateY(-1px);
  box-shadow: 
    0 8px 24px rgba(var(--a-accent), 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1);
}

.a-panel-item.unread {
  background: rgba(255, 255, 255, 0.90);
}

.a-panel-item.info { background: rgba(59, 130, 246, 0.10); }
.a-panel-item.success { background: rgba(34, 197, 94, 0.10); }
.a-panel-item.warning { background: rgba(245, 158, 11, 0.10); }
.a-panel-item.error { background: rgba(239, 68, 68, 0.10); }

.a-panel-item-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
}
.a-panel-item.info .a-panel-item-icon { background: #e0f2fe; color: #0284c7; }
.a-panel-item.success .a-panel-item-icon { background: #dcfce7; color: #15803d; }
.a-panel-item.warning .a-panel-item-icon { background: #fef3cd; color: #b45309; }
.a-panel-item.error .a-panel-item-icon { background: #fee2e2; color: #b91c1c; }

.a-panel-item-body {
  flex: 1;
  min-width: 0;
}
.a-panel-item-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 2px;
}
.a-panel-item-title {
  font-size: 12.5px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.a-panel-item-msg {
  font-size: 12px;
  color: #475569;
  line-height: 1.4;
  margin-bottom: 4px;
}
.a-panel-item-time {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0.8;
}

.a-panel-unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(var(--a-accent), 1);
  box-shadow: 0 0 6px rgba(var(--a-accent), 0.6);
  flex-shrink: 0;
}

/* ─── Toasts ────────────────────────────────────────────────── */
.a-toast-stack {
  position: fixed;
  top: 70px;
  right: 24px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.a-toast {
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
  animation: atoastIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}

.a-toast::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
}

.a-toast::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8), transparent, rgba(255, 255, 255, 0.3));
}

.a-toast.leaving {
  animation: atoastOut 0.5s ease-in forwards;
}

.a-toast.info { --a-t-accent: 234, 179, 8; }
.a-toast.success { --a-t-accent: 34, 197, 94; }
.a-toast.warning { --a-t-accent: 245, 158, 11; }
.a-toast.error { --a-t-accent: 239, 68, 68; }

.a-toast {
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(var(--a-t-accent), 0.25);
  box-shadow: 
    0 12px 40px rgba(var(--a-t-accent), 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 rgba(255, 255, 255, 0.15),
    inset 0 0 14px 7px rgba(var(--a-t-accent), 0.15);
}

.a-toast-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
}
.a-toast.info .a-toast-icon { background: #fef9c3; color: #a16207; }
.a-toast.success .a-toast-icon { background: #dcfce7; color: #15803d; }
.a-toast.warning .a-toast-icon { background: #fef3cd; color: #b45309; }
.a-toast.error .a-toast-icon { background: #fee2e2; color: #b91c1c; }

.a-toast-body {
  flex: 1;
}
.a-toast-title {
  font-size: 12.5px;
  font-weight: 700;
  margin-bottom: 2px;
  color: #1e293b;
}
.a-toast-msg {
  font-size: 12px;
  color: #475569;
  line-height: 1.4;
}

.a-toast-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  font-size: 14px;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
}
.a-toast-close:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1e293b;
}

@keyframes atoastIn {
  0% { transform: translateX(100%); opacity: 0; }
  100% { transform: translateX(0); opacity: 1; }
}

@keyframes atoastOut {
  0% { transform: scale(1) translateY(0); opacity: 1; }
  100% { transform: scale(0.5) translate(30px, -60px); opacity: 0; } /* flies slightly up toward bell */
}
</style>