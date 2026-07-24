<template>
  <router-view />

  <!-- ─── INACTIVITY SESSION LOCK MODAL ───────────────────────── -->
  <teleport to="body">
    <div class="lock-overlay" v-if="isLocked">
      <div class="lock-modal modal">
        <div class="lock-header">
          <div class="lock-icon-wrap">
            <i class="fas fa-user-lock"></i>
          </div>
          <h2>Session Locked</h2>
          <p>Locked due to 15 minutes of inactivity to protect confidential SDD data.</p>
        </div>

        <div class="lock-body">
          <div class="lock-user-card" v-if="user">
            <div class="lock-user-left">
              <div class="avatar-circle-lock">{{ (user.name || 'U').charAt(0).toUpperCase() }}</div>
              <div class="lock-user-info">
                <div class="user-name-lock">{{ user.name }}</div>
                <div class="user-email-lock">
                  <i class="fas fa-envelope"></i>
                  <span>{{ user.email }}</span>
                </div>
              </div>
            </div>
            <span :class="['user-role-chip', (user.role || '').toLowerCase()]">
              <i :class="['fas', roleIcon(user.role)]"></i>
              {{ formatRole(user.role) }}
            </span>
          </div>

          <form @submit.prevent="verifyUnlock" class="unlock-form">
            <div class="form-group">
              <label>Enter Password to Resume</label>
              <div class="input-password-wrap">
                <input 
                  v-model="unlockPassword" 
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter account password" 
                  required
                  ref="passwordInput"
                />
                <button type="button" class="eye-toggle-btn" @click="showPassword = !showPassword">
                  <i :class="['fas', showPassword ? 'fa-eye-slash' : 'fa-eye']"></i>
                </button>
              </div>
            </div>

            <p class="error-msg-lock" v-if="unlockError">{{ unlockError }}</p>

            <div class="lock-actions">
              <button type="button" class="btn-ghost" @click="handleSignOut">
                <i class="fas fa-sign-out-alt"></i> Sign Out
              </button>
              <button type="submit" class="btn-primary" :disabled="unlocking || !unlockPassword">
                <i class="fas fa-spinner fa-spin" v-if="unlocking"></i>
                <i class="fas fa-lock-open" v-else></i>
                <span>{{ unlocking ? 'Verifying…' : 'Unlock Session' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from './api/client'
import { useInactivityLock } from './composables/useInactivityLock'

const router = useRouter()
const { isLocked, unlockSession, setupListeners, removeListeners } = useInactivityLock()

const user = computed(() => {
  const raw = localStorage.getItem('user')
  return raw ? JSON.parse(raw) : null
})

const unlockPassword = ref('')
const showPassword = ref(false)
const unlocking = ref(false)
const unlockError = ref('')
const passwordInput = ref<HTMLInputElement | null>(null)

function formatRole(role: string): string {
  if (!role) return ''
  const r = role.toUpperCase()
  if (r === 'COMPLIANCE_OFFICER') return 'Compliance Officer'
  if (r === 'COLLABORATOR') return 'Collaborator'
  if (r === 'VIEWER') return 'Viewer'
  if (r === 'ADMIN') return 'Administrator'
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase()
}

function roleIcon(role: string): string {
  if (!role) return 'fa-user'
  const r = role.toUpperCase()
  if (r === 'COMPLIANCE_OFFICER' || r === 'ADMIN') return 'fa-shield-halved'
  if (r === 'COLLABORATOR') return 'fa-user-pen'
  return 'fa-eye'
}

watch(isLocked, (val) => {
  if (val) {
    unlockPassword.value = ''
    unlockError.value = ''
    nextTick(() => {
      passwordInput.value?.focus()
    })
  }
})

async function verifyUnlock() {
  if (!user.value || !unlockPassword.value) return
  unlocking.value = true
  unlockError.value = ''
  try {
    const res = await api.post('auth/login/', {
      email: user.value.email,
      password: unlockPassword.value
    })
    if (res.data.access) {
      localStorage.setItem('access', res.data.access)
      if (res.data.user) localStorage.setItem('user', JSON.stringify(res.data.user))
    }
    unlockSession()
  } catch (e: any) {
    unlockError.value = e?.response?.data?.error || e?.response?.data?.detail || 'Incorrect password. Please try again.'
  } finally {
    unlocking.value = false
  }
}

async function handleSignOut() {
  try {
    await api.post('auth/logout/')
  } catch (_) {
    // Ignore error on logout call
  }
  localStorage.clear()
  isLocked.value = false
  router.push('/login')
}

onMounted(() => {
  setupListeners()
})

onUnmounted(() => {
  removeListeners()
})
</script>

<style>
.lock-overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 15, 10, 0.65) !important;
  backdrop-filter: blur(16px) saturate(1.5) !important;
  -webkit-backdrop-filter: blur(16px) saturate(1.5) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999999 !important;
  padding: 20px;
}

.lock-modal {
  background: #F4EFE6 !important;
  border-radius: 28px !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  box-shadow: 
    0 30px 70px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
  width: 100%;
  max-width: 440px !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.lock-header {
  padding: 24px 24px 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.lock-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: #FFFFFF;
  color: var(--orange-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 6px 16px rgba(234, 108, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.05);
  margin-bottom: 4px;
}

.lock-header h2 {
  font-size: 20px;
  font-weight: 800;
  color: var(--neutral-800);
  margin: 0;
}

.lock-header p {
  font-size: 12px;
  color: var(--neutral-600);
  margin: 0;
  line-height: 1.4;
}

.lock-body {
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.lock-user-card {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border: 1px solid rgba(166, 169, 173, 0.35);
  box-shadow: 0 4px 16px rgba(35, 28, 20, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.lock-user-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.avatar-circle-lock {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 19px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(234, 88, 12, 0.3);
  border: 2px solid #FFFFFF;
  flex-shrink: 0;
}

.lock-user-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.user-name-lock {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email-lock {
  font-size: 11px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email-lock i {
  font-size: 10px;
  color: var(--text-muted);
}

.user-role-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 11px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.2px;
  flex-shrink: 0;
}

.user-role-chip.compliance_officer,
.user-role-chip.admin {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  color: #c2410c;
  border: 1px solid rgba(234, 88, 12, 0.35);
  box-shadow: 0 2px 6px rgba(234, 88, 12, 0.12);
}

.user-role-chip.collaborator {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #1d4ed8;
  border: 1px solid rgba(29, 78, 216, 0.3);
  box-shadow: 0 2px 6px rgba(29, 78, 216, 0.1);
}

.user-role-chip.viewer {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #475569;
  border: 1px solid rgba(71, 85, 105, 0.3);
  box-shadow: 0 2px 6px rgba(71, 85, 105, 0.08);
}

.unlock-form { display: flex; flex-direction: column; gap: 14px; }

.input-password-wrap { position: relative; display: flex; align-items: center; }
.input-password-wrap input { width: 100%; padding-right: 36px !important; }
.eye-toggle-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
}

.error-msg-lock {
  font-size: 11.5px;
  color: #dc2626;
  font-weight: 600;
  text-align: center;
  margin: 0;
}

.lock-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}
</style>