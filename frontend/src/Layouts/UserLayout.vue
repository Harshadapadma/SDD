<template>
  <div class="layout" @click="closePanel">

    <!-- ── SIDEBAR ──────────────────────────────────────────── -->
    <aside :class="['sidebar', { collapsed: isCollapsed }]">

      <!-- Hamburger -->
      <button class="hamburger" @click.stop="toggleSidebar" title="Toggle Sidebar">
        <i class="fas fa-bars"></i>
      </button>

      <!-- Brand -->
      <div class="brand-block">
        <div class="brand-logo-wrap">
          <img :src="logo" alt="Negen Logo" class="brand-logo" />
        </div>
        <template v-if="!isCollapsed">
          <span class="brand-name">Negen SDD</span>
          <span class="brand-role">{{ userRole }}</span>
        </template>
      </div>

      <div class="nav-divider" v-if="!isCollapsed"></div>

      <!-- Nav -->
      <nav class="nav">
        <div class="nav-item" :class="{ active: $route.path === '/' }" @click="$router.push('/')" title="Dashboard">
          <i class="fas fa-chart-pie"></i>
          <span v-if="!isCollapsed" class="nav-label">Dashboard</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/records' }" @click="$router.push('/records')" title="Records">
          <i class="fas fa-folder-open"></i>
          <span v-if="!isCollapsed" class="nav-label">Records</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/requests' }" @click="$router.push('/requests')" title="Requests">
          <i class="fas fa-paper-plane"></i>
          <span v-if="!isCollapsed" class="nav-label">Requests</span>
        </div>
        <div class="nav-item" :class="{ active: $route.path === '/clarifications' }" @click="$router.push('/clarifications')" title="Clarifications">
          <i class="fas fa-question-circle"></i>
          <span v-if="!isCollapsed" class="nav-label">Clarifications</span>
        </div>
      </nav>

      <!-- Sidebar Footer -->
      <div class="sidebar-footer profile-pill-btn" @click="$router.push('/profile')" role="button" tabindex="0" title="View Profile">
        <div class="footer-avatar">
          {{ userInitial }}
        </div>
        <div class="footer-info" v-if="!isCollapsed">
          <span class="footer-name">{{ userName }}</span>
          <span class="footer-email">{{ userEmail }}</span>
        </div>
        <button class="logout-btn" v-if="!isCollapsed" @click.stop="logout" title="Sign Out / Switch Account" aria-label="Sign Out">
          <i class="fas fa-sign-out-alt"></i>
        </button>
      </div>

    </aside>

    <!-- ── MAIN CONTENT ──────────────────────────────────────── -->
    <main class="content">

      <!-- TOPBAR -->
      <header class="topbar">
        <div class="topbar-left">
          <div class="topbar-breadcrumb">
            <span class="topbar-page">{{ currentPageLabel }}</span>
          </div>
        </div>

        <div class="topbar-right">
          <!-- Bell + Notification Panel -->
          <div class="bell-wrap" @click.stop>
            <button
              :class="['icon-btn', { active: panelOpen }]"
              @click="togglePanel"
              title="Notifications"
              :aria-label="`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`"
            >
              <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? 'var(--error-500)' : undefined }"></i>
              <span class="badge" v-if="unreadCount > 0">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
            </button>

            <transition name="panel">
              <div :class="['notif-panel', { expanded: panelExpanded }]" v-if="panelOpen">
                <!-- Panel Header -->
                <div class="panel-header">
                  <div class="panel-title">
                    <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? 'var(--error-500)' : undefined }"></i>
                    <span>Notifications</span>
                    <span class="panel-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
                  </div>
                  <div class="panel-actions">
                    <button class="panel-icon-btn" :title="isSoundMuted ? 'Unmute sound' : 'Mute sound'" @click="toggleSoundMute">
                      <i :class="['fas', isSoundMuted ? 'fa-volume-xmark' : 'fa-volume-high']" :style="{ color: isSoundMuted ? 'var(--error-500)' : undefined }"></i>
                    </button>
                    <button class="panel-icon-btn" :title="isMuted ? 'Unmute popups' : 'Mute popups'" @click="toggleMute">
                      <i :class="['fas', isMuted ? 'fa-bell-slash' : 'fa-bell']" :style="{ color: isMuted ? 'var(--error-500)' : undefined }"></i>
                    </button>
                    <button class="panel-icon-btn" title="Mark all read" @click="markAllRead" :disabled="unreadCount === 0">
                      <i class="fas fa-check-double"></i>
                    </button>
                    <button class="panel-icon-btn" :title="panelExpanded ? 'Collapse panel' : 'View notification history'" @click.stop="togglePanelExpand">
                      <i :class="['fas', panelExpanded ? 'fa-compress' : 'fa-clock-rotate-left']"></i>
                    </button>
                  </div>
                </div>

                <!-- Muted Banner -->
                <div class="muted-banner" v-if="isMuted">
                  <i class="fas fa-bell-slash"></i>
                  <span>Popup notifications are muted</span>
                </div>

                <!-- Notification Items -->
                <div class="panel-body">
                  <div v-if="notifications.length === 0" class="panel-empty">
                    <div class="panel-empty-icon"><i class="fas fa-inbox"></i></div>
                    <p>No notifications yet</p>
                    <small>We'll notify you when something happens</small>
                  </div>
                  <div v-else-if="!panelExpanded && notifications.filter(n => !n.is_read).length === 0" class="panel-empty">
                    <div class="panel-empty-icon"><i class="fas fa-inbox"></i></div>
                    <p>All caught up!</p>
                    <small>No unread notifications</small>
                  </div>

                  <div
                    v-for="n in (panelExpanded ? notifications : notifications.filter(n => !n.is_read).slice(0, 20))"
                    :key="n.id"
                    :class="['panel-item', n.type.toLowerCase(), { unread: !n.is_read }]"
                    @click="handleNotificationClick(n)"
                  >
                    <div :class="['panel-item-icon', n.type.toLowerCase()]">
                      <i :class="['fas', typeIcon(n.type)]"></i>
                    </div>
                    <div class="panel-item-body">
                      <div class="panel-item-header">
                        <div class="panel-item-title">{{ n.title }}</div>
                        <div class="panel-item-time">{{ formatTime(n.created_at) }}</div>
                      </div>
                      <div class="panel-item-msg">{{ n.message }}</div>
                    </div>
                    <div class="unread-dot" v-if="!n.is_read"></div>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- Profile Pill -->
          <button class="profile-pill" @click="$router.push('/profile')" title="My Profile">
            {{ userInitial }}
          </button>
        </div>
      </header>

      <!-- PAGE CONTENT -->
      <div class="page-body">
        <router-view />
      </div>

    </main>

    <!-- ── TOASTS ────────────────────────────────────────────── -->
    <teleport to="body">
      <div class="toast-stack">
        <div
          v-for="t in toasts"
          :key="t._tid"
          :class="['toast', t.type.toLowerCase(), { leaving: t.leaving }]"
        >
          <div :class="['toast-icon', t.type.toLowerCase()]">
            <i :class="['fas', typeIcon(t.type)]"></i>
          </div>
          <div class="toast-body">
            <div class="toast-title">{{ t.title }}</div>
            <div class="toast-msg">{{ t.message }}</div>
          </div>
          <button class="toast-close" @click="dismissToast(t._tid)" aria-label="Dismiss">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import logo from '../assets/logo.png'
import { useNotifications } from '../composables/useNotifications'
import api from '../api/client'

const router = useRouter()
const route = useRoute()
const isCollapsed   = ref(false)
const panelOpen     = ref(false)
const panelExpanded = ref(false)

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const userName = computed(() => user.value?.name || 'User')
const userEmail = computed(() => user.value?.email || '')
const userRole = computed(() => {
  if (user.value?.role === 'COLLABORATOR') return 'Collaborator'
  if (user.value?.role === 'VIEWER') return 'Viewer'
  return 'User'
})
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())

const currentPageLabel = computed(() => {
  const map: Record<string, string> = {
    '/': 'Dashboard',
    '/records': 'Records',
    '/requests': 'Requests',
    '/clarifications': 'Clarifications',
    '/profile': 'Profile',
    '/notifications': 'Notifications',
  }
  const path = route.path
  if (path.startsWith('/records/')) return 'Record Detail'
  return map[path] || 'Overview'
})

async function fetchProfile() {
  try {
    const res = await api.get('auth/profile/')
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  } catch (e) {
    console.error('Failed to fetch profile', e)
  }
}

const {
  notifications, unreadCount, isMuted, isSoundMuted, toasts,
  startPolling, stopPolling,
  markRead, markAllRead, toggleMute, toggleSoundMute, dismissToast,
  typeIcon, formatTime,
} = useNotifications()

const handleNotificationClick = (n: any) => {
  markRead(n.id)
  panelOpen.value = false
  panelExpanded.value = false
  if (n.title === 'Clarification Requested' || n.title === 'Clarification Reply') {
    const match = n.message.match(/creation #(\d+)/)
    if (match && match[1]) {
      router.push(`/clarifications?req_id=${match[1]}`)
    } else {
      router.push('/clarifications')
    }
  }
}

const toggleSidebar = () => { isCollapsed.value = !isCollapsed.value }
const togglePanel   = () => {
  panelOpen.value = !panelOpen.value
  if (!panelOpen.value) panelExpanded.value = false
}
const closePanel    = () => {
  panelOpen.value = false
  panelExpanded.value = false
}
const togglePanelExpand = () => {
  panelExpanded.value = !panelExpanded.value
}

const logout = async () => {
  try {
    await api.post('auth/logout/')
  } catch (_) {}
  localStorage.removeItem('access')
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
.layout {
  display: flex;
  height: 100vh;
  background: var(--bg-app);
  font-family: var(--font-family);
  color: var(--text-primary);
  overflow: hidden;
}

.sidebar {
  width: 228px;
  min-width: 228px;
  margin: 12px;
  border-radius: var(--radius-2xl);
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--bg-sidebar);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  color: var(--text-primary);
  transition:
    width var(--duration-slow) var(--ease-inout),
    min-width var(--duration-slow) var(--ease-inout),
    padding var(--duration-slow) var(--ease-inout);
  overflow: hidden;
  flex-shrink: 0;
  animation: slideInLeft var(--duration-enter) var(--ease-spring) both;
}

.sidebar.collapsed {
  width: 60px;
  min-width: 60px;
  padding: 16px 8px;
  align-items: center;
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0); }
}

.hamburger {
  background: var(--bg-base);
  border: none;
  padding: 9px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  align-self: flex-start;
  transition: all var(--duration-base) var(--ease-out);
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--sku-btn-secondary-shadow);
}
.sidebar.collapsed .hamburger { align-self: auto; }
.hamburger:hover {
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}
.hamburger:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
  transform: translateY(1px);
}

.brand-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 4px 4px;
  white-space: nowrap;
  overflow: hidden;
  animation: fadeIn 0.4s ease 0.1s both;
}

.brand-logo-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-base);
  box-shadow: var(--neu-inset);
  flex-shrink: 0;
  transition: box-shadow var(--duration-base) var(--ease-out);
}
.sidebar.collapsed .brand-logo-wrap { width: 36px; height: 36px; }
.brand-logo-wrap:hover { box-shadow: var(--neu-card); }

.brand-logo {
  width: 44px;
  height: 44px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.10));
  transition: transform var(--duration-base) var(--ease-spring);
}
.sidebar.collapsed .brand-logo { width: 26px; height: 26px; }
.brand-logo-wrap:hover .brand-logo { transform: scale(1.06); }

.brand-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--orange-accent);
  letter-spacing: 0.2px;
  text-align: center;
}

.brand-role {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: var(--weight-semibold);
  text-align: center;
  letter-spacing: 0.1px;
}

.nav-divider {
  height: 1px;
  background: var(--neutral-200);
  margin: 4px 8px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
}

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
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  transition: all var(--duration-base) var(--ease-out);
  white-space: nowrap;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  animation: slideInLeft 0.4s var(--ease-out) both;
  user-select: none;
}

.nav-item i {
  width: 16px;
  text-align: center;
  flex-shrink: 0;
  font-size: var(--text-sm);
  transition: color var(--duration-base);
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item:hover {
  color: var(--orange-accent);
  background: var(--orange-bg-subtle);
}

.nav-item.active {
  color: var(--orange-accent);
  background: var(--orange-bg-light);
  box-shadow: var(--neu-pressed);
  font-weight: var(--weight-bold);
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 10px 0;
  width: 40px;
  border-radius: var(--radius-md);
}
.sidebar.collapsed .nav-item:hover { transform: scale(1.1); }

/* ── Sidebar Footer (Profile Pill Button — 3D Skeuomorphic Blend) ── */
.sidebar-footer.profile-pill-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px 6px 6px;
  border-radius: var(--radius-pill);
  background: var(--bg-base);
  border: none;
  box-shadow: var(--sku-btn-secondary-shadow);
  margin-top: auto;
  overflow: hidden;
  white-space: nowrap;
  box-sizing: border-box;
  width: 100%;
  flex-shrink: 0;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  user-select: none;
}

.sidebar-footer.profile-pill-btn:hover {
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}

.sidebar-footer.profile-pill-btn:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
  transform: translateY(1px);
}

.sidebar.collapsed .sidebar-footer.profile-pill-btn {
  justify-content: center;
  padding: 4px;
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow);
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.sidebar.collapsed .sidebar-footer.profile-pill-btn:hover {
  box-shadow: var(--sku-btn-secondary-shadow-hover);
  transform: scale(1.08);
}

.footer-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--weight-bold);
  font-size: var(--text-xs);
  flex-shrink: 0;
  box-shadow: var(--sku-btn-primary-shadow);
  transition: all var(--duration-base) var(--ease-out);
}

.footer-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  min-width: 0;
  text-align: left;
}
.footer-name {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--duration-base);
}
.sidebar-footer.profile-pill-btn:hover .footer-name {
  color: var(--orange-accent);
}
.footer-email {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  transition: all var(--duration-base) var(--ease-out);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
}
.logout-btn:hover {
  color: var(--error-600);
  background: var(--error-bg);
  box-shadow: var(--sku-btn-secondary-shadow);
  transform: scale(1.1);
}
.logout-btn:active {
  transform: scale(0.95);
}

.content {
  flex: 1;
  margin: 12px 12px 12px 0;
  border-radius: var(--radius-2xl);
  background: var(--bg-content);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
  animation: fadeIn 0.4s var(--ease-out) 0.1s both;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--bg-content);
  border-bottom: none;
  position: relative;
  z-index: var(--z-sticky);
  flex-shrink: 0;
  animation: fadeInDown 0.4s var(--ease-out) 0.15s both;
}

.topbar-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  padding: 6px 14px;
  background: var(--bg-content);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-sm);
}
.topbar-company {
  color: var(--text-muted);
  font-weight: var(--weight-semibold);
}
.topbar-sep {
  color: var(--neutral-300);
  font-size: 9px;
}
.topbar-page {
  color: var(--text-primary);
  font-weight: var(--weight-bold);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  position: relative;
  background: var(--bg-base);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  box-shadow: var(--sku-btn-secondary-shadow);
  transition: all var(--duration-base) var(--ease-out);
}
.icon-btn:hover {
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
  transform: translateY(-1px);
}
.icon-btn:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
  transform: translateY(0);
}
.icon-btn.active {
  color: var(--orange-accent);
  background: var(--orange-bg-subtle);
  box-shadow: var(--neu-pressed);
}

.badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--orange-accent);
  color: white;
  font-size: 9px;
  font-weight: var(--weight-bold);
  min-width: 16px;
  height: 16px;
  padding: 0 3px;
  border-radius: var(--radius-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--bg-base);
  animation: badgePulse 2s ease-in-out infinite;
}

.profile-pill {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--weight-bold);
  font-size: var(--text-sm);
  cursor: pointer;
  border: none;
  box-shadow: var(--sku-btn-primary-shadow);
  transition: all var(--duration-base) var(--ease-out);
}
.profile-pill:hover {
  box-shadow: var(--sku-btn-primary-shadow-hover);
  transform: translateY(-1px);
}
.profile-pill:active {
  box-shadow: var(--sku-btn-primary-shadow-active);
  transform: translateY(0);
}

.bell-wrap { position: relative; }

.notif-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 360px;
  border-radius: var(--radius-xl);
  background: var(--bg-base);
  border: none;
  box-shadow: var(--neu-card-hover);
  z-index: var(--z-dropdown);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: top right;
  color: var(--text-primary);
  transition: width var(--duration-slow) var(--ease-spring), max-height var(--duration-slow) var(--ease-spring), box-shadow var(--duration-base);
}

.notif-panel.expanded {
  width: min(600px, calc(100vw - 40px));
  max-height: calc(80vh - 16px);
  height: calc(80vh - 16px);
  box-shadow: 0 28px 70px -12px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.panel-enter-active { animation: panelOpen 0.2s var(--ease-spring) both; }
.panel-leave-active { animation: panelClose 0.15s var(--ease-in) forwards; }
@keyframes panelOpen {
  from { opacity: 0; transform: scale(0.95) translateY(-6px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes panelClose {
  from { opacity: 1; transform: scale(1); }
  to   { opacity: 0; transform: scale(0.95) translateY(-6px); }
}

.panel-header {
  padding: 14px 16px;
  background: var(--bg-app);
  border-bottom: 1px solid var(--card-divider);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
}
.panel-title i { color: var(--orange-accent); font-size: var(--text-base); }

.panel-badge {
  background: var(--orange-accent);
  color: white;
  font-size: 10px;
  font-weight: var(--weight-bold);
  padding: 1px 6px;
  border-radius: var(--radius-pill);
}

.panel-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.panel-icon-btn {
  background: var(--bg-base);
  border: none;
  box-shadow: var(--sku-btn-secondary-shadow);
  padding: 5px 7px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  transition: all var(--duration-fast);
  line-height: 1;
}
.panel-icon-btn:hover {
  background: var(--bg-app);
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}
.panel-icon-btn:active { transform: scale(0.94); }
.panel-icon-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.muted-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--warning-bg);
  color: var(--warning-700);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  border-bottom: 1px solid var(--warning-border);
}

.panel-body {
  max-height: 380px;
  overflow-y: auto;
  padding: 8px 10px;
  margin: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  transition: max-height var(--duration-slow) var(--ease-spring);
}

.notif-panel.expanded .panel-body {
  max-height: calc(80vh - 110px);
  height: calc(80vh - 110px);
  overflow-y: auto;
}

.panel-empty {
  padding: 24px 16px;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: transparent;
}
.panel-empty-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  background: var(--neutral-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--neutral-400);
  margin-bottom: 4px;
}
.panel-empty p {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--text-secondary);
}
.panel-empty small { font-size: var(--text-xs); }

.panel-item {
  display: flex;
  margin: 0 0 8px 0;
  padding: 10px 12px;
  gap: 12px;
  align-items: flex-start;
  cursor: pointer;
  border-radius: var(--radius-lg);
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow);
  border: none;
  transition: all var(--duration-fast) var(--ease-out);
  user-select: none;
}
.panel-item:last-child {
  margin-bottom: 0;
}
.panel-item:hover {
  box-shadow: var(--sku-btn-secondary-shadow-hover);
  transform: translateY(-1px);
}
.panel-item:active {
  box-shadow: var(--sku-btn-secondary-shadow-active);
  transform: translateY(1px);
}
.panel-item.unread {
  border: none !important;
}

.panel-item-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow);
  color: var(--text-primary);
}

.panel-item-body { flex: 1; min-width: 0; }
.panel-item-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 2px;
}
.panel-item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
  transition: color var(--duration-fast);
}
.panel-item:hover .panel-item-title { color: var(--orange-accent); }
.panel-item-time {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}
.panel-item-msg {
  font-size: 12px;
  color: rgba(55, 65, 81, 0.88);
  line-height: 1.4;
}

.unread-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--orange-accent);
  flex-shrink: 0;
  margin-top: 4px;
  box-shadow: 0 0 8px var(--orange-glow);
}

.page-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
  animation: fadeInUp 0.4s var(--ease-out) 0.2s both;
}

.toast-stack {
  position: fixed;
  top: 70px;
  right: 20px;
  z-index: var(--z-toast);
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast,
.toast.success,
.toast.info,
.toast.warning,
.toast.error {
  pointer-events: auto;
  width: 340px;
  border-radius: var(--radius-2xl);
  padding: 14px 16px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: var(--bg-base);
  border: none !important;
  box-shadow: var(--neu-card-hover);
  transition: all var(--duration-base) var(--ease-out);
  animation: toastIn 0.4s var(--ease-spring) both;
  position: relative;
  overflow: hidden;
}

.toast.leaving { animation: toastOut 0.4s var(--ease-in) forwards; }

.toast-icon,
.toast-icon.success,
.toast-icon.info,
.toast-icon.warning,
.toast-icon.error {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: var(--text-base);
  background: var(--bg-app);
  box-shadow: var(--neu-inset);
  margin-left: 2px;
  color: var(--text-primary);
  border: none !important;
}

.toast-body { flex: 1; min-width: 0; padding-top: 1px; }
.toast-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-extrabold);
  color: var(--text-primary);
  margin-bottom: 3px;
  letter-spacing: -0.01em;
}
.toast-msg {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: 1.45;
  font-weight: var(--weight-medium);
}

.toast-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-base);
  box-shadow: var(--sku-btn-secondary-shadow);
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast);
  flex-shrink: 0;
}
.toast-close:hover {
  background: var(--bg-app);
  color: var(--orange-accent);
  box-shadow: var(--sku-btn-secondary-shadow-hover);
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes badgePulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.2); } }
@keyframes toastIn { from { transform: translateX(110%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes toastOut { from { transform: scale(1); opacity: 1; } to { transform: scale(0.85) translateX(60px); opacity: 0; } }
</style>