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
            <div class="avatar-circle-lock">{{ (user.name || 'U').charAt(0).toUpperCase() }}</div>
            <div class="lock-user-info">
              <div class="user-name-lock">{{ user.name }}</div>
              <div class="user-email-lock">{{ user.email }}</div>
              <span class="user-role-chip">{{ user.role }}</span>
            </div>
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
  border-radius: 18px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.avatar-circle-lock {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  box-shadow: var(--sku-btn-primary-shadow);
}

.lock-user-info { display: flex; flex-direction: column; gap: 2px; }
.user-name-lock { font-size: 13px; font-weight: 800; color: var(--text-primary); }
.user-email-lock { font-size: 11px; color: var(--text-muted); }

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