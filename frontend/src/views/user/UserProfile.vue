<template>
  <div class="page">
    
    <!-- HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">My Profile</h1>
        <p class="page-sub">Manage your professional identity and contact details</p>
      </div>
      <div class="header-badges">
        <span :class="['status-badge', user?.is_profile_complete ? 'complete' : 'incomplete']">
          <i :class="['fas', user?.is_profile_complete ? 'fa-circle-check' : 'fa-triangle-exclamation']"></i>
          {{ user?.is_profile_complete ? 'Profile Complete' : 'Profile Incomplete' }}
        </span>
      </div>
    </div>

    <div class="profile-grid">
      
      <!-- LEFT: AVATAR & BASIC INFO (Neomorphism) -->
      <div class="profile-card basic-info">
        <div class="avatar-large">
          <i class="fas fa-user"></i>
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
        <!-- EDITABLE FORM -->
        <div class="profile-card form-info">
          <div class="card-header">
            <div class="header-icon"><i class="fas fa-id-card"></i></div>
            <h3>Professional Details</h3>
          </div>
          
          <div class="form-body">
            <div class="grid-2">
              <div class="form-group">
                <label>Full Name *</label>
                <input v-model="form.name" placeholder="Your Name" :disabled="isFormDisabled" maxlength="255" @input="form.name = form.name.replace(/[^a-zA-Z\s\.\-']/g, '')" />
              </div>
              <div class="form-group">
                <label>Designation</label>
                <input v-model="form.designation" placeholder="e.g. Senior Manager" :disabled="isFormDisabled" maxlength="255" />
                <small v-if="!form.designation" class="req">Required for completion</small>
              </div>
              <div class="form-group">
                <label>Company Name</label>
                <input v-model="form.company_name" placeholder="e.g. Negen SDD" :disabled="isFormDisabled" maxlength="255" />
                <small v-if="!form.company_name" class="req">Required for completion</small>
              </div>
              <div class="form-group">
                <label>Mobile Number</label>
                <input v-model="form.mobile_number" placeholder="e.g. 9876543210" :disabled="isFormDisabled" maxlength="10" @input="form.mobile_number = form.mobile_number.replace(/\D/g, '')" />
                <small v-if="!form.mobile_number" class="req">Required for completion</small>
                <small v-else-if="form.mobile_number.replace(/\D/g, '').length !== 10" class="req err">Must be exactly 10 digits</small>
              </div>
            </div>

            <div class="form-footer">
              <button class="btn-ghost" @click="showPasswordForm = !showPasswordForm" type="button">
                <i class="fas fa-key"></i> {{ showPasswordForm ? 'Hide Security' : 'Change Password' }}
              </button>
              
              <template v-if="user?.is_profile_complete">
                <button v-if="!isEditing" class="btn-ghost" @click="isEditing = true" type="button">
                  <i class="fas fa-pen"></i> Edit Details
                </button>
                <button v-if="isEditing" class="btn-ghost" @click="cancelEdit" type="button">
                  <i class="fas fa-xmark"></i> Cancel
                </button>
              </template>

              <button v-if="!user?.is_profile_complete || isEditing" class="btn-primary" @click="saveProfile" :disabled="saving">
                <i class="fas fa-spinner fa-spin" v-if="saving"></i>
                <span>{{ saving ? 'Saving...' : (!user?.is_profile_complete ? 'Complete Profile' : 'Save Changes') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- SECURITY CARD -->
        <div class="profile-card form-info security-card" v-if="showPasswordForm">
          <div class="card-header">
            <div class="header-icon"><i class="fas fa-lock"></i></div>
            <h3>Account Security</h3>
          </div>
          <div class="form-body">
            <p class="section-hint">Update your account password. Ensure it's strong and unique.</p>
            <div class="grid-2">
              <div class="form-group">
                <label>Current Password</label>
                <div class="pass-wrap">
                  <input :type="showOld ? 'text' : 'password'" v-model="passForm.old_password" placeholder="••••••••" />
                  <button class="peek-btn" @click="showOld = !showOld" type="button">
                    <i :class="['fas', showOld ? 'fa-eye-slash' : 'fa-eye']"></i>
                  </button>
                </div>
              </div>
              <div class="form-group">
                <label>New Password</label>
                <div class="pass-wrap">
                  <input :type="showNew ? 'text' : 'password'" v-model="passForm.new_password" placeholder="••••••••" />
                  <button class="peek-btn" @click="showNew = !showNew" type="button">
                    <i :class="['fas', showNew ? 'fa-eye-slash' : 'fa-eye']"></i>
                  </button>
                </div>
                <ul class="pass-rules" v-if="passForm.new_password">
                  <li v-for="(rule, i) in passRules" :key="i" :class="{ met: rule.met }">
                    <i :class="['fas', rule.met ? 'fa-circle-check' : 'fa-circle-xmark']"></i>
                    {{ rule.label }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="form-footer">
              <button class="btn-primary" @click="changePassword" :disabled="changing || !allRulesMet">
                <i class="fas fa-spinner fa-spin" v-if="changing"></i>
                <span>{{ changing ? 'Updating Password...' : 'Change Password' }}</span>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../../api/client'
import { useNotifications } from '../../composables/useNotifications'

const user = ref<any>(null)
const isEditing = ref(false)
const isFormDisabled = computed(() => user.value?.is_profile_complete && !isEditing.value)

function cancelEdit() {
  isEditing.value = false
  if (user.value) {
    form.value = {
      name: user.value.name || '',
      designation: user.value.designation || '',
      company_name: user.value.company_name || '',
      mobile_number: user.value.mobile_number || ''
    }
  }
}

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
  if (!form.value.name || form.value.name.trim().length < 2) {
    notify('Invalid Name', 'Name must be at least 2 characters long.', 'WARNING')
    return
  }
  if (!/^[a-zA-Z\s\.\-']+$/.test(form.value.name)) {
    notify('Invalid Name', 'Name must contain only letters, spaces, dots, hyphens, and single quotes.', 'WARNING')
    return
  }
  if (form.value.designation && form.value.designation.trim().length < 2) {
    notify('Invalid Designation', 'Designation must be at least 2 characters long.', 'WARNING')
    return
  }
  if (form.value.company_name && form.value.company_name.trim().length < 2) {
    notify('Invalid Company Name', 'Company name must be at least 2 characters long.', 'WARNING')
    return
  }
  if (form.value.mobile_number && form.value.mobile_number.replace(/\D/g, '').length !== 10) {
    notify('Invalid Mobile Number', 'Mobile number must be exactly 10 digits.', 'WARNING')
    return
  }
  saving.value = true
  try {
    const res = await api.put('auth/profile/', form.value)
    user.value = res.data
    notify('Profile Updated', 'Your details have been successfully saved.', 'SUCCESS')
    const local = JSON.parse(localStorage.getItem('user') || '{}')
    localStorage.setItem('user', JSON.stringify({ ...local, name: res.data.name }))
    isEditing.value = false
  } catch (err: any) {
    console.error(err)
    const errData = err.response?.data
    let errMsg = 'Could not save profile.'
    if (errData && typeof errData === 'object') {
      errMsg = Object.entries(errData).map(([k, v]) => `${k.charAt(0).toUpperCase() + k.slice(1)}: ${Array.isArray(v) ? v[0] : v}`).join(', ')
    }
    notify('Update Failed', errMsg, 'ERROR')
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
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; }
.page-title { font-size: var(--text-2xl); font-weight: var(--weight-extrabold); color: var(--text-primary); }
.page-sub { font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }

.status-badge {
  padding: 6px 14px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold);
  display: flex; align-items: center; gap: 6px;
}
.status-badge.complete {
  background: var(--success-bg); color: var(--success-700); border: 1px solid var(--success-border);
}
.status-badge.incomplete {
  background: var(--warning-bg); color: var(--warning-700); border: 1px solid var(--warning-border);
}

.profile-grid { display: grid; grid-template-columns: 300px 1fr; gap: 20px; }
.right-column { display: flex; flex-direction: column; gap: 20px; }

/* Neomorphic Cards */
.profile-card {
  background: var(--bg-base); border-radius: var(--radius-2xl); box-shadow: var(--neu-card);
  overflow: hidden; transition: transform var(--duration-base) var(--ease-out);
}
.profile-card:hover { transform: translateY(-2px); box-shadow: var(--neu-card-hover); }

.basic-info {
  display: flex; flex-direction: column; align-items: center; padding: 32px 24px; text-align: center; gap: 16px;
}

.avatar-large {
  width: 90px; height: 90px; border-radius: 50%; background: var(--orange-gradient);
  color: white; display: flex; align-items: center; justify-content: center; font-size: 36px;
  box-shadow: var(--sku-btn-primary-shadow);
}

.user-meta h2 { font-size: var(--text-xl); font-weight: var(--weight-extrabold); color: var(--text-primary); margin: 0; }
.user-meta .email { font-size: var(--text-xs); color: var(--text-secondary); margin: 2px 0 10px; }
.role-pill {
  display: inline-block; background: var(--orange-bg-subtle); border: 1px solid var(--orange-border);
  color: var(--orange-accent); padding: 3px 12px; border-radius: var(--radius-pill);
  font-size: 11px; font-weight: var(--weight-bold);
}
.public-id { margin-top: 14px; font-size: 11px; display: flex; align-items: center; justify-content: center; gap: 6px; }
.public-id .label { color: var(--neutral-700); font-weight: var(--weight-bold); }
.public-id .value { font-family: monospace; font-weight: var(--weight-bold); color: var(--orange-accent); }

.card-header {
  padding: 16px 20px; background: var(--bg-base); border-bottom: 1px solid var(--card-divider);
  display: flex; align-items: center; gap: 10px;
}
.header-icon {
  width: 32px; height: 32px; border-radius: var(--radius-md); background: var(--orange-bg-subtle);
  color: var(--orange-accent); display: flex; align-items: center; justify-content: center; font-size: var(--text-sm);
}
.card-header h3 { font-size: var(--text-base); font-weight: var(--weight-bold); color: var(--text-primary); margin: 0; }

.form-body { padding: 20px; }
.section-hint { font-size: var(--text-xs); color: var(--text-secondary); margin-bottom: 16px; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--text-primary); }
.form-group input {
  padding: 10px 14px; border-radius: var(--radius-md); border: 1px solid rgba(166, 169, 173, 0.55);
  background: var(--bg-input); box-shadow: var(--neu-inset); font-size: var(--text-xs); font-weight: var(--weight-semibold);
  outline: none; transition: all var(--duration-fast); color: var(--text-primary);
}
.form-group input:focus { border-color: var(--orange-accent); background: var(--bg-input-focus); box-shadow: inset 0 2px 4px rgba(35, 28, 20, 0.08), 0 0 0 3px var(--orange-glow), 0 1px 0 rgba(255, 255, 255, 0.8); }
.form-group input:disabled { opacity: 0.65; cursor: not-allowed; background: rgba(224, 216, 204, 0.6) !important; }

.pass-wrap { position: relative; display: flex; align-items: center; }
.pass-wrap input { width: 100%; padding-right: 36px; }
.peek-btn {
  position: absolute; right: 8px; background: none; border: none; color: var(--neutral-400);
  cursor: pointer; padding: 4px; font-size: var(--text-xs); transition: color var(--duration-fast);
}
.peek-btn:hover { color: var(--orange-accent); }

.pass-rules { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-direction: column; gap: 4px; }
.pass-rules li { font-size: 11px; color: var(--neutral-400); display: flex; align-items: center; gap: 6px; }
.pass-rules li.met { color: var(--success-600); }

.req { font-size: 11px; color: var(--orange-accent); font-weight: var(--weight-semibold); margin-top: 2px; }
.req.err { color: var(--error-600); }

.form-footer { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--card-divider); }

/* Buttons */
.btn-primary {
  background: var(--orange-gradient); color: white; border: none; padding: 10px 18px;
  border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  box-shadow: var(--sku-btn-primary-shadow); transition: all var(--duration-base);
}
.btn-primary:hover:not(:disabled) { box-shadow: var(--sku-btn-primary-shadow-hover); transform: translateY(-1px); }

.btn-ghost {
  background: var(--bg-base); color: var(--text-secondary); border: none; padding: 8px 16px;
  border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: var(--weight-bold);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  box-shadow: var(--sku-btn-secondary-shadow); transition: all var(--duration-base);
}
.btn-ghost:hover { color: var(--orange-accent); box-shadow: var(--sku-btn-secondary-shadow-hover); }

@media (max-width: 850px) {
  .profile-grid { grid-template-columns: 1fr; }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
