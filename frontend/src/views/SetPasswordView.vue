<script setup lang="ts">
import { ref, onMounted } from "vue";
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

  if (password.value.length < 8) {
    errorMsg.value = "Password must be at least 8 characters.";
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
    errorMsg.error = err?.response?.data?.detail || "Failed to set password.";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="setup-container">
    <div class="setup-box">
      <div class="brand">
        <i class="fas fa-shield-halved"></i> Negen Vault
      </div>

      <!-- USER INFO CARD -->
      <div class="user-info-card" v-if="userData">
        <div class="avatar-sm">
          <i class="fas fa-user"></i>
        </div>
        <div class="info-content">
          <h3>{{ userData.name }}</h3>
          <p>{{ userData.email }}</p>
          <span class="id-tag">{{ userData.public_id }}</span>
        </div>
      </div>

      <h2>Setup Account</h2>
      <p class="subtext">Choose a secure password to activate your access to Negen SDD Portal.</p>

      <div v-if="successMsg" class="alert success">
        <i class="fas fa-check-circle"></i> {{ successMsg }}
      </div>
      
      <div v-if="errorMsg" class="alert error">
        <i class="fas fa-exclamation-circle"></i> {{ errorMsg }}
      </div>

      <!-- PASSWORD FIELD -->
      <div class="form-group">
        <label>New Password</label>
        <div class="input-wrap">
          <input 
            v-model="password" 
            :type="showPassword ? 'text' : 'password'" 
            placeholder="Min. 8 characters" 
            :disabled="!!successMsg || loading || !userData"
          />
          <button class="peek-btn" @click="showPassword = !showPassword" type="button" tabindex="-1">
            <i :class="['fas', showPassword ? 'fa-eye-slash' : 'fa-eye']"></i>
          </button>
        </div>
      </div>

      <!-- CONFIRM FIELD -->
      <div class="form-group">
        <label>Confirm Password</label>
        <div class="input-wrap">
          <input 
            v-model="confirmPassword" 
            :type="showConfirmPassword ? 'text' : 'password'" 
            placeholder="Repeat password" 
            :disabled="!!successMsg || loading || !userData"
          />
          <button class="peek-btn" @click="showConfirmPassword = !showConfirmPassword" type="button" tabindex="-1">
            <i :class="['fas', showConfirmPassword ? 'fa-eye-slash' : 'fa-eye']"></i>
          </button>
        </div>
      </div>

      <button class="submit-btn" @click="handleSetPassword" :disabled="!!successMsg || loading || !userData">
        <i class="fas fa-spinner fa-spin" v-if="loading"></i>
        {{ loading ? 'Saving...' : 'Activate Account' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.setup-container {
  height: 100vh; display: flex; align-items: center; justify-content: center;
  background: #f1f5f9; padding: 20px;
}

.setup-box {
  width: 100%; max-width: 440px; padding: 40px; background: white;
  border-radius: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.04);
  display: flex; flex-direction: column;
}

.brand {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  font-size: 20px; font-weight: 800; color: #3d5a80; margin-bottom: 30px;
}

/* ─── User Info Card ────────────────────────────────────────── */
.user-info-card {
  display: flex; align-items: center; gap: 16px; background: #f8fafc;
  border: 1.5px solid #e2e8f0; border-radius: 16px; padding: 16px;
  margin-bottom: 30px;
}
.avatar-sm {
  width: 44px; height: 44px; border-radius: 50%; background: #e0f2fe;
  color: #0284c7; display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.info-content h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.info-content p { font-size: 12px; color: #64748b; margin: 2px 0 6px; }
.id-tag {
  background: #fff; border: 1px solid #e2e8f0; padding: 2px 8px;
  border-radius: 6px; font-size: 10px; font-weight: 700; color: #3d5a80; font-family: monospace;
}

h2 { font-size: 24px; color: #1e293b; margin: 0 0 8px 0; text-align: center; font-weight: 800; }
.subtext { font-size: 14px; color: #64748b; text-align: center; margin: 0 0 24px 0; line-height: 1.6; }

.form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.form-group label { font-size: 13px; font-weight: 700; color: #475569; }

.input-wrap { position: relative; display: flex; align-items: center; }
.input-wrap input {
  width: 100%; padding: 14px 44px 14px 16px; border: 2px solid #f1f5f9;
  border-radius: 12px; font-size: 15px; outline: none; transition: all 0.2s;
  color: #1e293b; background: #f8fafc;
}
.input-wrap input:focus { border-color: #3d5a80; background: white; box-shadow: 0 0 0 4px rgba(61, 90, 128, 0.05); }

.peek-btn {
  position: absolute; right: 12px; background: none; border: none;
  color: #94a3b8; cursor: pointer; font-size: 16px; padding: 4px;
  transition: color 0.2s;
}
.peek-btn:hover { color: #3d5a80; }

.submit-btn {
  margin-top: 10px; padding: 16px; background: #3d5a80; color: white;
  border: none; border-radius: 12px; cursor: pointer; font-weight: 700;
  font-size: 16px; transition: all 0.2s; display: flex; align-items: center;
  justify-content: center; gap: 10px;
}
.submit-btn:hover:not(:disabled) { background: #293241; transform: translateY(-1px); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.alert {
  padding: 14px 18px; border-radius: 12px; font-size: 14px;
  font-weight: 600; margin-bottom: 24px; display: flex; align-items: center; gap: 10px;
}
.alert.error { background: #fff1f2; color: #e11d48; border: 1.5px solid #ffe4e6; }
.alert.success { background: #f0fdf4; color: #16a34a; border: 1.5px solid #dcfce7; }
</style>
