<script setup lang="ts">
import { ref, computed } from "vue";
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

const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
const isEmailValid = computed(() => emailRegex.test(email.value));

// ── Forgot Password ──────────────────────────────────────────
const forgotLoading = ref(false);
const forgotFlash = ref<{ type: 'success' | 'error'; msg: string } | null>(null);

const handleForgotPassword = async () => {
  forgotFlash.value = null;
  if (!email.value || !emailRegex.test(email.value)) {
    forgotFlash.value = { type: 'error', msg: 'Enter a valid email address above first.' };
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

  if (!emailRegex.test(email.value)) {
    errorMessage.value = "Please enter a valid email address.";
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  localStorage.removeItem("access");
  localStorage.removeItem("user");

  try {
    const res = await api.post("auth/login/", {
      email: email.value,
      password: password.value,
    });

    localStorage.setItem("access", res.data.access);
    localStorage.setItem("user", JSON.stringify(res.data.user));

    notify("Login Successful", "Welcome back to Negen SDD!", "SUCCESS");
    router.push("/");
  } catch (err: any) {
    errorMessage.value =
      err?.response?.data?.non_field_errors?.[0] ||
      err?.response?.data?.error ||
      err?.response?.data?.detail ||
      "Invalid credentials. Please try again.";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="login-page">
    <!-- Animated Ambient Light Spheres & Architectural Grid -->
    <div class="bg-grid"></div>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <!-- Main Authentication Container -->
    <main class="login-container">
      <div class="login-card">
        <!-- Floating 3D Logo Pedestal & Display Title -->
        <div class="brand-showcase">
          <div class="logo-pedestal">
            <div class="logo-ring"></div>
            <img :src="logo" alt="Negen SDD Logo" class="hero-logo" />
          </div>
          <h1 class="brand-title">
            Negen SDD<span class="accent-dot">.</span>
          </h1>
        </div>

        <!-- ─── STANDARD LOGIN FORM ───────────────────────────────── -->
        <form @submit.prevent="handleLogin" class="login-form">
          <!-- Error Banner -->
          <Transition name="slide-fade">
            <div v-if="errorMessage" class="error-banner">
              <i class="fas fa-circle-exclamation"></i>
              <span>{{ errorMessage }}</span>
            </div>
          </Transition>

          <!-- Forgot Password Flash Banner -->
          <Transition name="slide-fade">
            <div v-if="forgotFlash" :class="['forgot-banner', forgotFlash.type]">
              <i :class="forgotFlash.type === 'success' ? 'fas fa-circle-check' : 'fas fa-circle-exclamation'"></i>
              <span>{{ forgotFlash.msg }}</span>
            </div>
          </Transition>

          <!-- Email Input -->
          <div class="form-group">
            <label for="email">Email Address</label>
            <div class="input-wrap">
              <i class="fas fa-envelope input-icon"></i>
              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="name@company.com"
                required
                maxlength="255"
                autocomplete="email"
              />
              <div class="input-glow"></div>
            </div>
            <p v-if="email && !isEmailValid" class="inline-error">
              Please enter a valid email address
            </p>
          </div>

          <!-- Password Input -->
          <div class="form-group">
            <div class="label-row">
              <label for="password">Password</label>
              <button
                type="button"
                class="forgot-link"
                :disabled="forgotLoading"
                @click="handleForgotPassword"
              >
                <span v-if="!forgotLoading">Forgot Password?</span>
                <span v-else><i class="fas fa-spinner fa-spin"></i> Sending…</span>
              </button>
            </div>
            <div class="input-wrap">
              <i class="fas fa-lock input-icon"></i>
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••••••"
                required
                maxlength="100"
                autocomplete="current-password"
              />
              <button
                type="button"
                class="toggle-pass-btn"
                @click="showPassword = !showPassword"
                title="Toggle password visibility"
              >
                <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
              <div class="input-glow"></div>
            </div>
          </div>

          <!-- 3D Tactile Primary Button with Shimmer Effect -->
          <button type="submit" class="submit-pill-btn" :disabled="loading">
            <div class="btn-shimmer"></div>
            <span v-if="!loading" class="btn-text">
              <span>Sign In</span>
              <i class="fas fa-arrow-right-long"></i>
            </span>
            <span v-else class="btn-text">
              <span class="loader"></span>
              <span>Authenticating…</span>
            </span>
          </button>
        </form>
      </div>
    </main>

    <!-- Bottom Copyright Footnote -->
    <footer class="page-footer">
      <span>&copy; Negen Capitals</span>
    </footer>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   ANIMATED AMBIENT LAYER & ARCHITECTURAL GRID
   ═══════════════════════════════════════════════════════════════ */
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-app);
  color: var(--text-primary);
  font-family: 'Outfit', 'Plus Jakarta Sans', var(--font-family), sans-serif;
  position: relative;
  overflow: hidden;
  padding: 30px 20px;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(160, 164, 168, 0.32) 1px, transparent 1px);
  background-size: 28px 28px;
  pointer-events: none;
  z-index: 0;
}

/* Floating Ambient Light Spheres */
.orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(90px);
  z-index: 0;
  animation: floatOrb 14s ease-in-out infinite alternate;
}

.orb-1 {
  width: 500px;
  height: 500px;
  top: -120px;
  right: -100px;
  background: radial-gradient(circle, rgba(234, 108, 0, 0.16) 0%, transparent 70%);
}

.orb-2 {
  width: 450px;
  height: 450px;
  bottom: -150px;
  left: -100px;
  background: radial-gradient(circle, rgba(234, 108, 0, 0.12) 0%, transparent 70%);
  animation-delay: -5s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  top: 40%;
  left: 55%;
  background: radial-gradient(circle, rgba(180, 170, 160, 0.25) 0%, transparent 70%);
  animation-delay: -9s;
}

@keyframes floatOrb {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-30px, 40px) scale(1.08); }
  100% { transform: translate(20px, -20px) scale(0.95); }
}

/* ═══════════════════════════════════════════════════════════════
   MAIN AUTHENTICATION CONTAINER & GLASS CARD
   ═══════════════════════════════════════════════════════════════ */
.login-container {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.login-card {
  width: 100%;
  max-width: 460px;
  background: rgba(255, 255, 255, 0.88);
  border-radius: 38px;
  padding: 52px 46px 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 36px;
  box-shadow:
    0 32px 64px -16px rgba(0, 0, 0, 0.12),
    0 12px 24px -8px rgba(234, 108, 0, 0.08),
    inset 0 1px 2px rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  animation: cardRise 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes cardRise {
  from {
    opacity: 0;
    transform: translateY(28px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ── Brand Showcase & Floating Logo Pedestal ───────────────── */
.brand-showcase {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.logo-pedestal {
  position: relative;
  width: 140px;
  height: 140px;
  border-radius: 40px;
  background: linear-gradient(145deg, #ffffff 0%, #f0ede8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 20px 40px -10px rgba(0, 0, 0, 0.15),
    0 8px 16px -6px rgba(234, 108, 0, 0.22),
    inset 0 2px 4px rgba(255, 255, 255, 1);
  animation: logoFloat 4s ease-in-out infinite;
  padding: 18px;
}

.logo-ring {
  position: absolute;
  inset: -4px;
  border-radius: 44px;
  background: linear-gradient(135deg, rgba(234, 108, 0, 0.45) 0%, transparent 60%, rgba(234, 108, 0, 0.15) 100%);
  z-index: -1;
  opacity: 0.7;
  animation: pulseRing 3s ease-in-out infinite alternate;
}

@keyframes pulseRing {
  0% { transform: scale(0.98); opacity: 0.5; }
  100% { transform: scale(1.03); opacity: 0.85; }
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

.hero-logo {
  width: 110px;
  height: auto;
  filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.18));
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.logo-pedestal:hover .hero-logo {
  transform: scale(1.06) rotate(-2deg);
}

.brand-title {
  font-size: 38px;
  font-weight: 850;
  letter-spacing: -1.2px;
  color: #1a1e26;
  margin: 0;
  line-height: 1;
  display: flex;
  align-items: baseline;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.accent-dot {
  color: var(--orange-accent);
  font-size: 44px;
  line-height: 0;
}

/* ── Form Inputs & Neumorphic Tactile Controls ─────────────── */
.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.error-banner, .forgot-banner {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  display: flex;
  align-items: center;
  gap: 10px;
  line-height: 1.4;
}

.error-banner {
  background: var(--error-bg);
  color: var(--error-700);
}

.forgot-banner.success {
  background: var(--success-bg);
  color: var(--success-700);
}

.forgot-banner.error {
  background: var(--error-bg);
  color: var(--error-700);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-group label {
  font-size: 13px;
  font-weight: 750;
  color: #2c323e;
  letter-spacing: 0.3px;
}

.forgot-link {
  font-size: 12px;
  color: var(--orange-accent);
  font-weight: 700;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: all var(--duration-fast);
}

.forgot-link:hover {
  color: var(--orange-hover);
  text-decoration: underline;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 18px;
  color: #8b929e;
  font-size: 15px;
  pointer-events: none;
  z-index: 2;
  transition: color var(--duration-fast);
}

.input-wrap input {
  width: 100%;
  padding: 15px 46px 15px 46px;
  border-radius: 18px;
  border: 1px solid rgba(166, 169, 173, 0.55);
  font-size: 14px;
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
  background: var(--bg-input);
  box-shadow: var(--neu-inset);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  font-family: inherit;
}

.input-wrap input:focus {
  outline: none;
  border-color: var(--orange-accent);
  background: var(--bg-input-focus);
  box-shadow: inset 0 2px 4px rgba(35, 28, 20, 0.08), 0 0 0 3px var(--orange-glow), 0 1px 0 rgba(255, 255, 255, 0.8);
}

.input-wrap input:focus + .input-icon,
.input-wrap input:not(:placeholder-shown) ~ .input-icon {
  color: var(--orange-accent);
}

.toggle-pass-btn {
  position: absolute;
  right: 14px;
  background: transparent;
  border: none;
  color: #8b929e;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--duration-fast);
  z-index: 2;
}

.toggle-pass-btn:hover {
  color: var(--orange-accent);
}

.inline-error {
  color: var(--error-600);
  font-size: 11px;
  font-weight: 700;
  margin: 2px 0 0 4px;
}

/* ── 3D Tactile Primary Button with Shimmer Effect ─────────── */
.submit-pill-btn {
  position: relative;
  margin-top: 8px;
  padding: 16px 28px;
  border-radius: 50px;
  border: none;
  background: linear-gradient(135deg, #FF7B00 0%, #E05300 100%);
  color: white;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.4px;
  cursor: pointer;
  box-shadow:
    0 12px 24px -6px rgba(234, 108, 0, 0.45),
    inset 0 2px 1px rgba(255, 255, 255, 0.4),
    inset 0 -2px 1px rgba(0, 0, 0, 0.2);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-pill-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow:
    0 16px 32px -6px rgba(234, 108, 0, 0.55),
    inset 0 2px 1px rgba(255, 255, 255, 0.5),
    inset 0 -2px 1px rgba(0, 0, 0, 0.25);
}

.submit-pill-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow:
    0 6px 14px -4px rgba(234, 108, 0, 0.4),
    inset 0 1px 1px rgba(255, 255, 255, 0.3),
    inset 0 -1px 1px rgba(0, 0, 0, 0.3);
}

.submit-pill-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.btn-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transform: skewX(-25deg);
  transition: left 0.7s ease;
}

.submit-pill-btn:hover:not(:disabled) .btn-shimmer {
  left: 150%;
}

.btn-text {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 12px;
}

.loader {
  width: 18px;
  height: 18px;
  border: 2px.6px solid rgba(255, 255, 255, 0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ═══════════════════════════════════════════════════════════════
   BOTTOM COPYRIGHT FOOTNOTE
   ═══════════════════════════════════════════════════════════════ */
.page-footer {
  position: relative;
  z-index: 10;
  font-size: 13px;
  font-weight: 750;
  color: #646b77;
  letter-spacing: 0.4px;
  padding-bottom: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.25s ease;
}
.slide-fade-enter-from, .slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Responsive adjustments */
@media (max-width: 520px) {
  .login-card {
    padding: 38px 26px 34px;
    border-radius: 30px;
    gap: 28px;
  }
  .logo-pedestal {
    width: 120px;
    height: 120px;
    border-radius: 34px;
  }
  .hero-logo {
    width: 94px;
  }
  .brand-title {
    font-size: 32px;
  }
}

/* ═══════════════════════════════════════════════════════════════
   MFA OTP VERIFICATION STYLES
   ═══════════════════════════════════════════════════════════════ */
.mfa-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.mfa-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(234, 108, 0, 0.12) 0%, rgba(234, 108, 0, 0.05) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--orange-accent);
}

.mfa-title {
  font-size: 20px;
  font-weight: 800;
  color: #1a1e26;
  margin: 0;
}

.mfa-subtitle {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0;
  max-width: 340px;
}

.otp-input {
  text-align: center;
  font-size: 28px !important;
  font-weight: 800 !important;
  letter-spacing: 12px !important;
  font-family: 'Outfit', monospace !important;
}

.back-to-login-btn {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all var(--duration-fast);
}

.back-to-login-btn:hover {
  color: var(--orange-accent);
}
</style>