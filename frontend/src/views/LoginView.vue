<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api/client";
import logo from "../assets/logo.png";
import { useNotifications } from "../composables/useNotifications";

const email = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");
const showPassword = ref(false);
const router = useRouter();
const { notify } = useNotifications();

// ── Forgot Password ──────────────────────────────────────────
const forgotLoading = ref(false);
const forgotFlash = ref<{ type: 'success' | 'error'; msg: string } | null>(null);

const handleForgotPassword = async () => {
  forgotFlash.value = null;
  if (!email.value || !email.value.includes("@")) {
    forgotFlash.value = { type: 'error', msg: 'Enter your email address above first.' };
    return;
  }
  forgotLoading.value = true;
  try {
    await api.post("auth/forgot-password/", { email: email.value });
    forgotFlash.value = { type: 'success', msg: 'Reset link sent! Check your inbox.' };
  } catch (err: any) {
    const msg = err?.response?.data?.error || "Something went wrong. Please try again.";
    forgotFlash.value = { type: 'error', msg };
  } finally {
    forgotLoading.value = false;
  }
};
// ─────────────────────────────────────────────────────────────

const handleLogin = async () => {
  forgotFlash.value = null;
  if (!email.value || !password.value) {
    errorMessage.value = "Please enter both email and password.";
    return;
  }

  if (!email.value.includes("@")) {
    errorMessage.value = "Email must include '@'";
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");

  try {
    const res = await api.post("auth/login/", {
      email: email.value,
      password: password.value,
    });

    localStorage.setItem("access", res.data.access);
    localStorage.setItem("refresh", res.data.refresh);
    localStorage.setItem("user", JSON.stringify(res.data.user));

    notify("Login Successful", "Welcome back to Negen SDD!", "SUCCESS");
    router.push("/");
  } catch (err: any) {
    errorMessage.value =
      err?.response?.data?.non_field_errors?.[0] ||
      err?.response?.data?.detail ||
      "Invalid credentials. Please try again.";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="page">
    <div class="card">

      <!-- LEFT SIDE -->
      <div class="left">
        <div class="logo-container">
          <img :src="logo" class="logo" alt="Negen SDD Logo" />
        </div>
        <h1>Negen SDD</h1>
        <div class="left-footer">
        </div>
      </div>

      <!-- RIGHT SIDE -->
      <div class="right">
        <div class="header">
          <h2>Welcome Back</h2>
          <p>Login to your portal</p>
        </div>

        <form @submit.prevent="handleLogin" class="login-form">
          <!-- Login error banner -->
          <div v-if="errorMessage" class="error-banner">
            <i class="fa-solid fa-circle-exclamation"></i>
            <span>{{ errorMessage }}</span>
          </div>

          <!-- Forgot-password flash banner -->
          <Transition name="flash">
            <div v-if="forgotFlash" :class="['forgot-flash', forgotFlash.type]">
              <i :class="forgotFlash.type === 'success' ? 'fa-solid fa-circle-check' : 'fa-solid fa-circle-exclamation'"></i>
              <span>{{ forgotFlash.msg }}</span>
            </div>
          </Transition>

          <div class="input-group">
            <label>Email Address</label>
            <div class="input-wrapper">
              <i class="fa-solid fa-envelope"></i>
              <input 
                v-model="email" 
                type="email" 
                placeholder="name@company.com" 
                required 
              />
            </div>
            <p v-if="email && !email.includes('@')" class="inline-error">
              Email must include '@'
            </p>
          </div>

          <div class="input-group">
            <div class="label-row">
              <label>Password</label>
              <button
                type="button"
                class="forgot-link"
                :disabled="forgotLoading"
                @click="handleForgotPassword"
              >
                <span v-if="!forgotLoading">Forgot Password?</span>
                <span v-else><i class="fa-solid fa-spinner fa-spin"></i> Sending…</span>
              </button>
            </div>
            <div class="input-wrapper">
              <i class="fa-solid fa-lock"></i>
              <input 
                v-model="password" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="••••••••" 
                required 
              />
              <button 
                type="button" 
                class="toggle-pass" 
                @click="showPassword = !showPassword"
              >
                <i :class="showPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'"></i>
              </button>
            </div>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="!loading">Sign In</span>
            <span v-else class="loader"></span>
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* BACKGROUND */
.page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #ffffff;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow: hidden;
  position: relative;
}

.page::before,
.page::after {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.15;
}

.page::before {
  background: #CA5728;
  top: -100px;
  left: -100px;
  animation: float 20s ease-in-out infinite alternate;
}

.page::after {
  background: #A64821;
  bottom: -100px;
  right: -100px;
  animation: float 25s ease-in-out infinite alternate-reverse;
}

@keyframes float {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(100px, 50px) scale(1.1); }
}

/* CARD */
.card {
  display: flex;
  width: 900px;
  height: 550px;
  border-radius: 28px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px) saturate(200%);
  -webkit-backdrop-filter: blur(40px) saturate(200%);
  box-shadow: 0 40px 80px -15px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  animation: cardEntrance 1s cubic-bezier(0.2, 0.8, 0.2, 1);
  z-index: 10;
}

/* LEFT PANEL */
.left {
  flex: 0 0 400px;
  background: linear-gradient(165deg, rgba(202, 87, 40, 0.85), rgba(166, 72, 33, 0.85));
  backdrop-filter: blur(10px);
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  text-align: center;
  position: relative;
  overflow: hidden;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.left::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  animation: rotate 20s linear infinite;
}

.logo-container {
  width: 180px;
  height: 180px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.logo-container:hover {
  transform: scale(1.05) rotate(2deg);
}

.logo {
  width: 140px;
  height: auto;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.left h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.5px;
  z-index: 1;
}

.left p {
  opacity: 0.8;
  font-size: 16px;
  margin-top: 8px;
  z-index: 1;
}

.left-footer {
  position: absolute;
  bottom: 24px;
  opacity: 0.7;
  font-size: 12px;
  letter-spacing: 1px;
}

/* RIGHT PANEL */
.right {
  flex: 1;
  padding: 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}

.header {
  margin-bottom: 32px;
}

.header h2 {
  font-size: 28px;
  color: #111827;
  margin: 0;
  font-weight: 700;
}

.header p {
  color: #6b7280;
  margin: 8px 0 0;
  font-size: 15px;
}

.error-banner {
  background: rgba(254, 242, 242, 0.8);
  border-left: 4px solid #ef4444;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  color: #991b1b;
  font-size: 14px;
  animation: shake 0.4s ease;
  backdrop-filter: blur(5px);
}

.inline-error {
  color: #ef4444;
  font-size: 12px;
  margin: 4px 0 0 4px;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Forgot-password inline flash */
.forgot-flash {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 15px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 600;
  animation: shake 0.4s ease;
}
.forgot-flash.success {
  background: rgba(220, 252, 231, 0.85);
  color: #15803d;
  border: 1px solid #86efac;
  animation: fadeIn 0.3s ease;
}
.forgot-flash.error {
  background: rgba(254, 242, 242, 0.85);
  color: #991b1b;
  border-left: 4px solid #ef4444;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-group label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.forgot-link {
  font-size: 13px;
  color: #CA5728;
  text-decoration: none;
  font-weight: 500;
}

.forgot-link:hover {
  text-decoration: underline;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  transition: transform 0.1s;
}

.input-wrapper:has(input:active) {
  transform: scale(0.995);
}

.input-wrapper i {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #CA5728;
  font-size: 16px;
  transition: all 0.3s;
  pointer-events: none;
  z-index: 10;
}

.input-wrapper input {
  width: 100%;
  padding: 14px 50px 14px 50px;
  border-radius: 14px;
  border: 1.5px solid rgba(202, 87, 40, 0.15);
  font-family: "Inter", sans-serif;
  font-weight: 500;
  font-size: 16px;
  color: #111827;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.65);
  caret-color: #CA5728;
  letter-spacing: 0.5px;
  position: relative;
  z-index: 1;
}

.input-wrapper input:focus {
  border-color: #CA5728;
  background: rgba(255, 255, 255, 0.9);
  outline: none;
  box-shadow: 0 0 0 4px rgba(202, 87, 40, 0.1);
}

/* TYPEWRITER CURSOR EFFECT */
.input-wrapper input:focus::placeholder {
  color: transparent;
}

.input-wrapper input:focus + i,
.input-wrapper input:not(:placeholder-shown) + i {
  color: #CA5728;
}

.toggle-pass {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: #CA5728;
  cursor: pointer;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 100; /* Extremely high to stay on top */
  margin: 0;
  line-height: 1;
  pointer-events: auto; /* Explicitly allow pointer events */
}

.toggle-pass:hover {
  color: #A64821;
}

.submit-btn {
  margin-top: 10px;
  padding: 14px;
  border-radius: 12px;
  border: none;
  background: #CA5728;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 12px rgba(202, 87, 40, 0.2);
}

.submit-btn:hover:not(:disabled) {
  background: #A64821;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(202, 87, 40, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.footer {
  margin-top: 32px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.footer a {
  color: #CA5728;
  font-weight: 600;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}

/* LOADER */
.loader {
  width: 22px;
  height: 22px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ANIMATIONS */
@keyframes cardEntrance {
  from { 
    opacity: 0; 
    transform: translateY(30px) scale(0.95);
    filter: blur(10px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

/* RESPONSIVE */
@media (max-width: 900px) {
  .card {
    width: 90%;
    flex-direction: column;
    height: auto;
  }
  .left {
    flex: none;
    padding: 30px;
  }
  .right {
    padding: 40px 30px;
  }
}

/* ── Forgot-link as button ──────────────────────────────────── */
.forgot-link {
  font-size: 13px;
  color: #CA5728;
  font-weight: 500;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-family: "Inter", sans-serif;
  transition: color 0.2s;
}
.forgot-link:hover { color: #A64821; text-decoration: underline; }

/* ── Modal Overlay ──────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-card {
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px 36px 32px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(202, 87, 40, 0.12);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.modal-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #CA5728, #A64821);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 22px;
  margin-bottom: 4px;
  box-shadow: 0 8px 20px rgba(202, 87, 40, 0.3);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.modal-header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

/* Flash message */
.flash-msg {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
}
.flash-msg.success {
  background: rgba(220, 252, 231, 0.9);
  color: #15803d;
  border: 1px solid #86efac;
}
.flash-msg.error {
  background: rgba(254, 242, 242, 0.9);
  color: #991b1b;
  border-left: 4px solid #ef4444;
  animation: shake 0.4s ease;
}

.modal-input-group .input-wrapper {
  width: 100%;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.modal-cancel {
  flex: 1;
  padding: 13px;
  border-radius: 12px;
  border: 1.5px solid rgba(202, 87, 40, 0.2);
  background: transparent;
  color: #374151;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: "Inter", sans-serif;
  transition: all 0.2s;
}
.modal-cancel:hover:not(:disabled) { background: #f9fafb; }
.modal-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-submit {
  flex: 2;
  padding: 13px;
  border-radius: 12px;
  border: none;
  background: #CA5728;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: "Inter", sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(202, 87, 40, 0.25);
}
.modal-submit:hover:not(:disabled) {
  background: #A64821;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(202, 87, 40, 0.35);
}
.modal-submit:disabled { opacity: 0.6; cursor: not-allowed; filter: grayscale(0.3); }

.loader.sm {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

/* ── Transitions ────────────────────────────────────────────── */
.modal-fade-enter-active { animation: modalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.modal-fade-leave-active { animation: modalOut 0.2s ease; }
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.88) translateY(20px); }
  to   { opacity: 1; transform: scale(1)   translateY(0); }
}
@keyframes modalOut {
  from { opacity: 1; transform: scale(1); }
  to   { opacity: 0; transform: scale(0.94) translateY(10px); }
}

.flash-enter-active { animation: flashIn 0.3s ease; }
.flash-leave-active { animation: flashOut 0.2s ease; }
@keyframes flashIn  { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
@keyframes flashOut { from { opacity: 1; } to { opacity: 0; } }
</style>