<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../api/client";

const route = useRoute();
const router = useRouter();

const uid = ref("");
const token = ref("");
const password = ref("");
const confirmPassword = ref("");

const userData = ref<any>(null);
const loading = ref(false);
const errorMsg = ref("");
const successMsg = ref("");

// Visibility Toggles
const showPassword = ref(false);
const showConfirmPassword = ref(false);

// Password strength rules
const passRules = computed(() => [
  { label: 'At least 8 characters', met: password.value.length >= 8 },
  { label: 'One uppercase letter', met: /[A-Z]/.test(password.value) },
  { label: 'One number', met: /[0-9]/.test(password.value) },
  { label: 'One special character', met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password.value) },
]);
const allRulesMet = computed(() => passRules.value.every(r => r.met));

onMounted(async () => {
  uid.value = (route.query.uid as string) || "";
  token.value = (route.query.token as string) || "";
  
  if (uid.value && token.value) {
    await fetchUserInfo();
  } else {
    errorMsg.value = "Invalid or missing setup link.";
  }
});

const fetchUserInfo = async () => {
  try {
    const res = await api.get(`auth/verify-token/`, {
      params: { uid: uid.value, token: token.value }
    });
    userData.value = res.data;
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.error || "Token expired or invalid.";
  }
};

const handleSetPassword = async () => {
  errorMsg.value = "";
  successMsg.value = "";

  if (password.value !== confirmPassword.value) {
    errorMsg.value = "Passwords do not match.";
    return;
  }

  if (!allRulesMet.value) {
    errorMsg.value = "Password does not meet all requirements.";
    return;
  }

  loading.value = true;
  try {
    await api.post("auth/set-password/", {
      uid: uid.value,
      token: token.value,
      password: password.value,
    });

    successMsg.value = "Password successfully set! Redirecting to login...";
    setTimeout(() => {
      router.push("/login");
    }, 2000);
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || "Failed to set password.";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="setup-container">
    <div class="glow-bg"></div>

    <div class="setup-card">
      <div class="brand">
        <i class="fas fa-shield-halved"></i>
        <span>Negen SDD</span>
      </div>

      <!-- USER INFO CARD -->
      <div class="user-info-card" v-if="userData">
        <div class="avatar-wrapper">
          <div class="avatar-sm">
            {{ userData.name?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
          <div class="verified-dot" title="Verified Account">
            <i class="fas fa-check"></i>
          </div>
        </div>
        <div class="info-content">
          <div class="card-top-row">
            <span class="user-name">{{ userData.name }}</span>
            <span class="identity-badge">VERIFIED USER</span>
          </div>
          <div class="user-email">{{ userData.email }}</div>
          <div class="id-row">
            <span class="id-label">ID</span>
            <span class="id-tag">{{ userData.public_id }}</span>
          </div>
        </div>
      </div>

      <div class="header">
        <h2>Setup Your Account</h2>
        <p class="subtext">Create a strong password to activate your portal access.</p>
      </div>

      <Transition name="fade">
        <div v-if="successMsg" class="alert success">
          <i class="fas fa-circle-check"></i> {{ successMsg }}
        </div>
      </Transition>
      
      <Transition name="fade">
        <div v-if="errorMsg" class="alert error">
          <i class="fas fa-circle-exclamation"></i> {{ errorMsg }}
        </div>
      </Transition>

      <!-- PASSWORD FIELD -->
      <div class="form-group">
        <label for="newPass">New Password</label>
        <div class="input-wrap">
          <i class="fas fa-lock input-icon"></i>
          <input 
            id="newPass"
            v-model="password" 
            :type="showPassword ? 'text' : 'password'" 
            placeholder="Enter new password" 
            :disabled="!!successMsg || loading || !userData"
          />
          <button class="peek-btn" @click="showPassword = !showPassword" type="button" tabindex="-1">
            <i :class="['fas', showPassword ? 'fa-eye-slash' : 'fa-eye']"></i>
          </button>
        </div>
        <!-- PASSWORD RULES -->
        <ul class="pass-rules" v-if="password">
          <li v-for="(rule, i) in passRules" :key="i" :class="{ met: rule.met }">
            <i :class="['fas', rule.met ? 'fa-circle-check' : 'fa-circle-xmark']"></i>
            {{ rule.label }}
          </li>
        </ul>
      </div>

      <!-- CONFIRM FIELD -->
      <div class="form-group">
        <label for="confirmPass">Confirm Password</label>
        <div class="input-wrap">
          <i class="fas fa-shield-cat input-icon"></i>
          <input 
            id="confirmPass"
            v-model="confirmPassword" 
            :type="showConfirmPassword ? 'text' : 'password'" 
            placeholder="Repeat new password" 
            :disabled="!!successMsg || loading || !userData"
          />
          <button class="peek-btn" @click="showConfirmPassword = !showConfirmPassword" type="button" tabindex="-1">
            <i :class="['fas', showConfirmPassword ? 'fa-eye-slash' : 'fa-eye']"></i>
          </button>
        </div>
      </div>

      <button class="submit-btn" @click="handleSetPassword" :disabled="!!successMsg || loading || !userData || !allRulesMet">
        <i class="fas fa-spinner fa-spin" v-if="loading"></i>
        <span>{{ loading ? 'Saving Password...' : 'Activate Account' }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.setup-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--neutral-900);
  font-family: var(--font-family);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.glow-bg {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--orange-glow) 0%, transparent 70%);
  top: -150px;
  left: -150px;
  pointer-events: none;
}

.setup-card {
  width: 100%;
  max-width: 440px;
  padding: 40px;
  background: var(--bg-card);
  border-radius: var(--radius-3xl);
  box-shadow: var(--glass-shadow-lg);
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.5);
  z-index: var(--z-raised);
  animation: cardEntrance 0.5s var(--ease-spring);
}

.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: var(--text-lg);
  font-weight: var(--weight-extrabold);
  color: var(--orange-accent);
  margin-bottom: 24px;
}

/* User Info Card */
.user-info-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(135deg, rgba(234, 108, 0, 0.07) 0%, rgba(249, 248, 245, 0.95) 100%);
  border: 1px solid rgba(234, 108, 0, 0.25);
  border-radius: var(--radius-xl);
  padding: 16px 18px;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(35, 28, 20, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.95);
  position: relative;
  overflow: hidden;
}

.user-info-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--orange-gradient);
  border-radius: var(--radius-pill) 0 0 var(--radius-pill);
}

.avatar-wrapper {
  position: relative;
}

.avatar-sm {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: var(--orange-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--weight-extrabold);
  font-size: var(--text-md);
  box-shadow: 0 4px 12px rgba(234, 108, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.4);
  border: 2px solid #ffffff;
}

.verified-dot {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 16px;
  height: 16px;
  background: #16a34a;
  color: white;
  border-radius: 50%;
  font-size: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.info-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-name {
  font-size: 15px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.3px;
  line-height: 1.2;
}

.identity-badge {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.8px;
  color: var(--orange-700);
  background: rgba(234, 108, 0, 0.12);
  border: 1px solid rgba(234, 108, 0, 0.3);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  text-transform: uppercase;
}

.user-email {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: var(--weight-medium);
}

.id-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.id-label {
  font-size: 9px;
  font-weight: 800;
  color: var(--neutral-400);
  letter-spacing: 1px;
}

.id-tag {
  font-family: 'Courier New', Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--neutral-800);
  background: rgba(35, 28, 20, 0.06);
  border: 1px solid rgba(35, 28, 20, 0.08);
  padding: 2px 8px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

/* Forms */
.pass-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-group label {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.input-icon {
  position: absolute;
  left: 14px;
  color: var(--neutral-400);
  font-size: var(--text-sm);
  pointer-events: none;
}
.input-wrap input {
  width: 100%;
  padding: 12px 42px 12px 40px;
  border: 1px solid rgba(166, 169, 173, 0.55);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
  background: var(--bg-input);
  box-shadow: var(--neu-inset);
  transition: all var(--duration-fast);
}
.input-wrap input:focus {
  outline: none;
  border-color: var(--orange-accent);
  box-shadow: inset 0 2px 4px rgba(35, 28, 20, 0.08), 0 0 0 3px var(--orange-glow), 0 1px 0 rgba(255, 255, 255, 0.8);
  background: var(--bg-input-focus);
}

.peek-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--neutral-400);
  cursor: pointer;
  font-size: var(--text-sm);
  padding: 8px;
  transition: color var(--duration-fast);
}
.peek-btn:hover { color: var(--orange-accent); }

.submit-btn {
  margin-top: 8px;
  padding: 13px;
  background: var(--orange-gradient);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: var(--weight-bold);
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: var(--sku-btn-primary-shadow);
}
.submit-btn:hover:not(:disabled) {
  box-shadow: var(--sku-btn-primary-shadow-hover);
  transform: translateY(-1px);
}
.submit-btn:active:not(:disabled) {
  box-shadow: var(--sku-btn-primary-shadow-active);
  transform: translateY(1px);
}
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.alert {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.alert.success {
  background: var(--success-bg);
  border: 1px solid var(--success-border);
  color: var(--success-700);
}
.alert.error {
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  color: var(--error-700);
}

.pass-rules {
  list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-direction: column; gap: 4px;
}
.pass-rules li {
  font-size: 11px; font-weight: var(--weight-medium); color: var(--neutral-400);
  display: flex; align-items: center; gap: 6px;
  transition: color var(--duration-fast);
}
.pass-rules li.met { color: var(--success-600); }

@keyframes cardEntrance {
  from { opacity: 0; transform: translateY(20px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
