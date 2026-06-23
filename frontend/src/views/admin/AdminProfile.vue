<template>
  <div class="page">
    
    <!-- HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Admin Profile</h1>
        <p class="page-sub">Manage your administrative identity and security</p>
      </div>
      <div class="header-badges">
        <span class="status-badge complete">
          <i class="fas fa-user-shield"></i>
          Administrator
        </span>
      </div>
    </div>

    <div class="profile-grid">
      
      <!-- LEFT: AVATAR & BASIC INFO -->
      <div class="profile-card basic-info">
        <div class="avatar-large">
          <i class="fas fa-user-shield"></i>
        </div>
        <div class="user-meta">
          <h2>{{ user?.name }}</h2>
          <p class="email">{{ user?.email }}</p>
          <span class="role-pill">{{ user?.role }}</span>
          <div class="public-id">
            <span class="label">Public ID:</span>
            <span class="value">{{ user?.public_id }}</span>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="right-column">
        <!-- RIGHT: EDITABLE FORM -->
        <div class="profile-card form-info">
        <div class="card-header">
          <i class="fas fa-edit"></i>
          <h3>Administrative Details</h3>
        </div>
        
        <div class="form-body">
          <div class="grid-2">
            <div class="form-group">
              <label>Full Name</label>
              <input v-model="form.name" placeholder="Admin Name" />
            </div>
            <div class="form-group">
              <label>Designation</label>
              <input v-model="form.designation" placeholder="e.g. Super Admin" />
            </div>
            <div class="form-group">
              <label>Company Name</label>
              <input v-model="form.company_name" placeholder="e.g. Negen SDD" />
            </div>
            <div class="form-group">
              <label>Mobile Number</label>
              <input v-model="form.mobile_number" placeholder="e.g. 9876543210" maxlength="10" @input="form.mobile_number = form.mobile_number.replace(/\D/g, '')" />
              <small v-if="form.mobile_number && form.mobile_number.replace(/\D/g, '').length !== 10" class="req err">Must be exactly 10 digits</small>
            </div>
          </div>

          <div class="form-footer">
            <button class="btn-outline" @click="showPasswordForm = !showPasswordForm" type="button">
              <i class="fas fa-key"></i> {{ showPasswordForm ? 'Hide Password Form' : 'Change Password' }}
            </button>
            <button class="save-btn" @click="saveProfile" :disabled="saving">
              <i class="fas fa-spinner fa-spin" v-if="saving"></i>
              {{ saving ? 'Saving Changes...' : 'Update Profile' }}
            </button>
          </div>
        </div>
      </div>

      <!-- NEW: SECURITY CARD -->
      <div class="profile-card form-info security-card" v-if="showPasswordForm">
        <div class="card-header">
          <i class="fas fa-shield-alt"></i>
          <h3>Account Security</h3>
        </div>
        <div class="form-body">
          <p class="section-hint">Update your admin account password. Ensure it's strong and unique.</p>
          <div class="grid-2">
            <div class="form-group">
              <label>Current Password</label>
              <div class="pass-wrap">
                <input :type="showOld ? 'text' : 'password'" v-model="passForm.old_password" placeholder="••••••••" />
                <button class="peek-btn" @click="showOld = !showOld">
                  <i :class="['fas', showOld ? 'fa-eye-slash' : 'fa-eye']"></i>
                </button>
              </div>
            </div>
            <div class="form-group">
              <label>New Password</label>
              <div class="pass-wrap">
                <input :type="showNew ? 'text' : 'password'" v-model="passForm.new_password" placeholder="••••••••" />
                <button class="peek-btn" @click="showNew = !showNew">
                  <i :class="['fas', showNew ? 'fa-eye-slash' : 'fa-eye']"></i>
                </button>
              </div>
              <!-- PASSWORD RULES -->
              <ul class="pass-rules" v-if="passForm.new_password">
                <li v-for="(rule, i) in passRules" :key="i" :class="{ met: rule.met }">
                  <i :class="['fas', rule.met ? 'fa-check-circle' : 'fa-times-circle']"></i>
                  {{ rule.label }}
                </li>
              </ul>
            </div>
          </div>
          <div class="form-footer">
            <button class="btn-security" @click="changePassword" :disabled="changing">
              <i class="fas fa-spinner fa-spin" v-if="changing"></i>
              {{ changing ? 'Updating Password...' : 'Change Password' }}
            </button>
          </div>
        </div>
      </div>

      </div> <!-- END RIGHT COLUMN -->
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const user = ref<any>(null)
const form = ref({
  name: '',
  designation: '',
  company_name: '',
  mobile_number: ''
})
const passForm = ref({
  old_password: '',
  new_password: ''
})
const saving = ref(false)
const changing = ref(false)
const showOld = ref(false)
const showNew = ref(false)
const showPasswordForm = ref(false)
const { notify } = useNotifications()

// Password strength rules
const passRules = computed(() => [
  { label: 'At least 8 characters', met: passForm.value.new_password.length >= 8 },
  { label: 'One uppercase letter', met: /[A-Z]/.test(passForm.value.new_password) },
  { label: 'One number', met: /[0-9]/.test(passForm.value.new_password) },
  { label: 'One special character', met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(passForm.value.new_password) },
])
const allRulesMet = computed(() => passRules.value.every(r => r.met))

async function fetchProfile() {
  try {
    const res = await api.get('auth/profile/')
    user.value = res.data
    form.value = {
      name: res.data.name || '',
      designation: res.data.designation || '',
      company_name: res.data.company_name || '',
      mobile_number: res.data.mobile_number || ''
    }
  } catch (err) {
    console.error(err)
  }
}

async function saveProfile() {
  if (form.value.mobile_number && form.value.mobile_number.replace(/\D/g, '').length !== 10) {
    notify('Invalid Mobile Number', 'Mobile number must be exactly 10 digits.', 'WARNING')
    return
  }
  saving.value = true
  try {
    const res = await api.put('auth/profile/', form.value)
    user.value = res.data
    notify('Profile Updated', 'Your details have been successfully saved.', 'SUCCESS')
    // Update local storage user if needed
    const local = JSON.parse(localStorage.getItem('user') || '{}')
    localStorage.setItem('user', JSON.stringify({ ...local, name: res.data.name }))
  } catch (err: any) {
    console.error(err)
    notify('Update Failed', err.response?.data?.error || 'Could not save profile.', 'ERROR')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!passForm.value.old_password || !passForm.value.new_password) {
    notify('Missing Fields', 'Please enter both current and new passwords.', 'WARNING')
    return
  }
  if (!allRulesMet.value) {
    notify('Weak Password', 'Password does not meet all strength requirements.', 'WARNING')
    return
  }
  changing.value = true
  try {
    await api.post('auth/change-password/', passForm.value)
    notify('Password Changed', 'Your account security has been updated.', 'SUCCESS')
    passForm.value = { old_password: '', new_password: '' }
    showOld.value = false
    showNew.value = false
  } catch (err: any) {
    console.error(err)
    const errorMsg = err.response?.data?.old_password?.[0] || 'Failed to update password.'
    notify('Update Failed', errorMsg, 'ERROR')
  } finally {
    changing.value = false
  }
}

onMounted(fetchProfile)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px; animation: fadeIn 0.4s ease both; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 24px; font-weight: 800; color: #1e293b; margin: 0; }
.page-sub { font-size: 14px; color: #64748b; margin-top: 4px; }

.status-badge {
  padding: 6px 14px; border-radius: 999px; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; gap: 8px;
}
.status-badge.complete { background: #dcfce7; color: #15803d; }

/* ─── Profile Grid ───────────────────────────────────────────── */
.profile-grid {
  display: grid; grid-template-columns: 320px 1fr; gap: 24px; align-items: stretch;
}

.right-column {
  display: flex; flex-direction: column; gap: 24px;
}

.profile-card {
  background: white; border-radius: 20px; border: 1px solid rgba(47, 125, 101, 0.1);
  overflow: hidden; box-shadow: 0 4px 20px rgba(47, 125, 101, 0.04);
}

/* ─── Basic Info ────────────────────────────────────────────── */
.basic-info {
  display: flex; flex-direction: column; align-items: center; padding: 40px 24px; text-align: center;
  background: linear-gradient(180deg, #f0faf5 0%, #ffffff 100%);
}
.avatar-large {
  width: 100px; height: 100px; border-radius: 50%;
  background: linear-gradient(135deg, #e6f5ee, #d6ede3);
  color: #2f7d65; display: flex; align-items: center; justify-content: center;
  font-size: 40px; margin-bottom: 24px; border: 4px solid #fff;
  box-shadow: 0 4px 16px rgba(47, 125, 101, 0.12);
}
.user-meta h2 { font-size: 20px; font-weight: 800; color: #1e293b; margin: 0; }
.user-meta .email { font-size: 14px; color: #64748b; margin: 4px 0 16px; }
.role-pill {
  display: inline-block; padding: 4px 12px; background: rgba(47, 125, 101, 0.1); color: #2f7d65;
  border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase;
  margin-bottom: 24px; border: 1px solid rgba(47, 125, 101, 0.15);
}
.public-id {
  background: rgba(47, 125, 101, 0.04); padding: 10px 16px; border-radius: 12px;
  border: 1px solid rgba(47, 125, 101, 0.08);
}
.public-id .label { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; display: block; margin-bottom: 2px; }
.public-id .value { font-family: monospace; font-size: 14px; font-weight: 700; color: #2f7d65; }

/* ─── Form Info ─────────────────────────────────────────────── */
.form-info {
  display: flex; flex-direction: column; flex: 1 0 auto;
}
.form-info .card-header {
  padding: 16px 24px; background: linear-gradient(135deg, #f5fbf7, #edf7f2);
  border-bottom: 1px solid rgba(47, 125, 101, 0.08);
  display: flex; align-items: center; gap: 12px;
}
.form-info .card-header i { color: #2f7d65; }
.form-info .card-header h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }

.form-body { padding: 24px; display: flex; flex-direction: column; flex: 1; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px 24px; }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 600; color: #475569; }
.form-group input {
  padding: 12px 16px; border: 1.5px solid #e2e8f0; border-radius: 10px;
  font-size: 14px; outline: none; transition: border-color 0.2s, box-shadow 0.2s;
}
.form-group input:focus { border-color: #2f7d65; box-shadow: 0 0 0 3px rgba(47, 125, 101, 0.08); }
.form-group .req { font-size: 11px; color: #f59e0b; font-weight: 500; }
.form-group .req.err { color: #ef4444; }

.form-footer { margin-top: auto; padding-top: 24px; border-top: 1px solid #f1f5f9; display: flex; justify-content: flex-end; gap: 12px; }
.save-btn {
  padding: 12px 24px; background: #2f7d65; color: white; border: none;
  border-radius: 10px; font-weight: 700; cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  display: inline-flex; align-items: center; gap: 10px;
}
.save-btn:hover:not(:disabled) { background: #235c4a; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(47, 125, 101, 0.25); }
.save-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.btn-outline {
  padding: 12px 24px; background: white; color: #2f7d65; border: 1.5px solid rgba(47, 125, 101, 0.15);
  border-radius: 10px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 10px;
}
.btn-outline:hover { border-color: #2f7d65; background: rgba(47, 125, 101, 0.04); }

/* ─── Security Card ─────────────────────────────────────────── */
.security-card { margin-top: 0; }
.section-hint { font-size: 13px; color: #64748b; margin: -10px 0 20px; }

.pass-wrap { position: relative; display: flex; align-items: center; }
.pass-wrap input { width: 100%; padding-right: 46px; }
.peek-btn {
  position: absolute; right: 12px; background: none; border: none;
  color: #94a3b8; cursor: pointer; padding: 4px; transition: color 0.2s;
}
.peek-btn:hover { color: #2f7d65; }

.btn-security {
  padding: 12px 24px; background: #ef4444; color: white; border: none;
  border-radius: 10px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 10px;
}
.btn-security:hover:not(:disabled) { background: #dc2626; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2); }
.btn-security:disabled { opacity: 0.7; cursor: not-allowed; }

@media (max-width: 900px) {
  .profile-grid { grid-template-columns: 1fr; }
}

/* ─── Password Rules Checklist ──────────────────────────────── */
.pass-rules {
  list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 6px;
}
.pass-rules li {
  font-size: 12px; font-weight: 600; color: #e11d48;
  display: flex; align-items: center; gap: 8px;
  transition: color 0.25s ease;
}
.pass-rules li.met { color: #16a34a; }
.pass-rules li i { font-size: 13px; width: 16px; text-align: center; }
</style>
