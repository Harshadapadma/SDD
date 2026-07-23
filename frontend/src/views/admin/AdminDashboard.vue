<template>
  <div class="dashboard-page">
    
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div class="header-titles">
        <h1 class="page-title">{{ isComplianceOfficer ? 'Compliance Officer Dashboard' : 'Admin Dashboard' }}</h1>
        <p class="page-sub">Minimal system overview, core website metrics, and monthly record entries</p>
      </div>
      <div class="date-chip">
        <i class="fas fa-calendar-day"></i>
        <span>{{ currentDateTime }}</span>
      </div>
    </div>

    <!-- MAIN MINIMAL CONTENT (No scrolling required) -->
    <div class="dashboard-content" v-if="stats && stats.overview">
      
      <!-- 6 KEY WEBSITE METRICS TILES -->
      <div class="minimal-stats-grid">
        <div class="stat-tile" v-for="item in websiteMetrics" :key="item.label">
          <div :class="['tile-icon', item.colorClass]">
            <i :class="['fas', item.icon]"></i>
          </div>
          <div class="tile-info">
            <span class="tile-val">{{ item.val }}</span>
            <span class="tile-label">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <!-- BOTTOM SPLIT: SMALL MONTHLY GRAPH + ROLE METRICS -->
      <div class="bottom-minimal-split">
        
        <!-- SMALL GRAPH: MONTHLY RECORD ENTRIES -->
        <div class="minimal-card chart-section">
          <div class="card-header-compact">
            <div class="header-icon-sm orange"><i class="fas fa-calendar-days"></i></div>
            <div>
              <h3>Monthly Record Entries</h3>
              <p>Disclosure inflow over recent months</p>
            </div>
          </div>
          <div class="chart-container-compact">
            <Bar v-if="monthlyChartData" :data="monthlyChartData" :options="barOptions" />
          </div>
        </div>

        <!-- USER ROLES SUMMARY NUMBERS -->
        <div class="minimal-card roles-section">
          <div class="card-header-compact">
            <div class="header-icon-sm blue"><i class="fas fa-user-shield"></i></div>
            <div>
              <h3>Platform Role Breakdown</h3>
              <p>Active accounts across permission tiers</p>
            </div>
          </div>
          <div class="roles-list-compact">
            <div class="role-card">
              <div class="role-card-left">
                <div class="role-icon orange"><i class="fas fa-shield-halved"></i></div>
                <span class="role-name">Administrators</span>
              </div>
              <span class="role-count">{{ stats.role_distribution?.ADMIN || 0 }}</span>
            </div>
            <div class="role-card">
              <div class="role-card-left">
                <div class="role-icon blue"><i class="fas fa-scale-balanced"></i></div>
                <span class="role-name">Compliance Officers</span>
              </div>
              <span class="role-count">{{ stats.role_distribution?.COMPLIANCE_OFFICER || 0 }}</span>
            </div>
            <div class="role-card">
              <div class="role-card-left">
                <div class="role-icon green"><i class="fas fa-users-viewfinder"></i></div>
                <span class="role-name">Collaborators</span>
              </div>
              <span class="role-count">{{ stats.role_distribution?.COLLABORATOR || 0 }}</span>
            </div>
            <div class="role-card">
              <div class="role-card-left">
                <div class="role-icon purple"><i class="fas fa-eye"></i></div>
                <span class="role-name">Viewers</span>
              </div>
              <span class="role-count">{{ stats.role_distribution?.VIEWER || 0 }}</span>
            </div>
          </div>
        </div>

      </div>

    </div>

    <!-- LOADING STATE -->
    <div v-else-if="loading" class="loading-full">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Aggregating minimal dashboard metrics...</p>
    </div>

    <!-- FALLBACK/ERROR STATE -->
    <div v-else class="loading-full">
      <i class="fas fa-chart-pie" style="font-size: 32px; color: var(--text-muted); margin-bottom: 12px;"></i>
      <p>No dashboard statistics available at this moment.</p>
      <button class="btn btn-primary" style="margin-top: 16px; padding: 8px 18px; border-radius: 12px;" @click="loading = true; fetchStats()">Retry Fetching</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../../api/client'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
)

const stats = ref<any>(null)
const loading = ref(true)
const currentDateTime = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const isComplianceOfficer = computed(() => user.value?.role === 'COMPLIANCE_OFFICER')

async function fetchStats() {
  try {
    const res = await api.get('auth/dashboard-stats/')
    stats.value = res.data || {}
  } catch (e) {
    console.error('Failed to fetch dashboard stats', e)
    stats.value = null
  } finally {
    loading.value = false
  }
}

// 6 Exact website metric numbers
const websiteMetrics = computed(() => {
  if (!stats.value || !stats.value.overview) return []
  
  const totalUsers = stats.value.overview?.total_users ?? 0
  const totalRecords = stats.value.overview?.total_records ?? 0
  const totalPending = stats.value.overview?.total_pending ?? 0
  const approved = stats.value.request_status?.APPROVED ?? 0
  const rejected = stats.value.request_status?.REJECTED ?? 0
  const totalRequests = totalPending + approved + rejected

  return [
    { label: 'Total Users', val: totalUsers, icon: 'fa-users', colorClass: 'blue' },
    { label: 'Total Records', val: totalRecords, icon: 'fa-database', colorClass: 'green' },
    { label: 'Workflow Requests', val: totalRequests, icon: 'fa-diagram-project', colorClass: 'purple' },
    { label: 'Pending Requests', val: totalPending, icon: 'fa-clock', colorClass: 'orange' },
    { label: 'Approved Requests', val: approved, icon: 'fa-circle-check', colorClass: 'success' },
    { label: 'Rejected Requests', val: rejected, icon: 'fa-circle-xmark', colorClass: 'danger' },
  ]
})

// Small Monthly Chart Data
const monthlyChartData = computed(() => {
  const recordsList = stats.value?.monthly_records || stats.value?.record_growth
  if (!recordsList || !Array.isArray(recordsList)) return null
  
  return {
    labels: recordsList.map((d: any) => d?.month || d?.date || ''),
    datasets: [{
      label: 'New Records',
      data: recordsList.map((d: any) => d?.count || 0),
      backgroundColor: '#ea6c00',
      borderRadius: 6,
      barThickness: 22,
    }]
  }
})

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { 
      beginAtZero: true, 
      grid: { color: 'rgba(0,0,0,0.04)' },
      ticks: {
        stepSize: 1,
        precision: 0,
        font: { family: 'Inter', size: 10 }
      }
    },
    x: { 
      grid: { display: false },
      ticks: { font: { family: 'Inter', size: 10 } }
    }
  }
}

onMounted(fetchStats)
</script>

<style scoped>
/* Page container strictly sized to prevent unnecessary scrolling */
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100vh - 105px);
  max-height: 820px;
  overflow: hidden;
}

/* ── Page Header ────────────────────────────────────────────── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-shrink: 0;
}
.page-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-extrabold);
  color: var(--text-primary);
  margin: 0;
}
.page-sub {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.date-chip {
  background: var(--bg-base);
  box-shadow: var(--neu-btn);
  padding: 6px 14px;
  font-size: 11px;
  font-weight: var(--weight-bold);
  color: var(--orange-accent);
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: var(--radius-pill);
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

/* ── 6 Minimal Stat Tiles Grid ──────────────────────────────── */
.minimal-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  flex-shrink: 0;
}

.stat-tile {
  background: var(--bg-base);
  border-radius: var(--radius-xl);
  padding: 12px 16px;
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  transition: transform var(--duration-fast), box-shadow var(--duration-fast);
}
.stat-tile:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.tile-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
  box-shadow: var(--neu-inset);
}
.tile-icon.blue    { color: var(--info-600);    background: var(--info-bg); }
.tile-icon.green   { color: var(--success-600); background: var(--success-bg); }
.tile-icon.purple  { color: #8b5cf6;            background: rgba(139, 92, 246, 0.12); }
.tile-icon.orange  { color: var(--orange-accent); background: var(--orange-bg-subtle); }
.tile-icon.success { color: #16a34a;            background: rgba(22, 163, 74, 0.12); }
.tile-icon.danger  { color: #dc2626;            background: rgba(220, 38, 38, 0.12); }

.tile-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.tile-val {
  font-size: 20px;
  font-weight: var(--weight-extrabold);
  color: var(--text-primary);
  line-height: 1.15;
}
.tile-label {
  font-size: 11px;
  font-weight: var(--weight-semibold);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* ── Bottom Split: Chart + Role Breakdown ───────────────────── */
.bottom-minimal-split {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 14px;
  flex: 1;
  min-height: 0;
}

.minimal-card {
  background: var(--bg-base);
  border-radius: var(--radius-2xl);
  padding: 14px 18px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  min-height: 0;
  overflow: hidden;
}

.card-header-compact {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.header-icon-sm {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  box-shadow: var(--neu-inset);
  flex-shrink: 0;
}
.header-icon-sm.orange { background: var(--orange-bg-subtle); color: var(--orange-accent); }
.header-icon-sm.blue   { background: var(--info-bg);          color: var(--info-600); }

.card-header-compact h3 {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
  margin: 0;
}
.card-header-compact p {
  font-size: 10px;
  color: var(--text-secondary);
  margin: 2px 0 0;
}

.chart-container-compact {
  flex: 1;
  min-height: 120px;
  position: relative;
}

/* Role breakdown cards (styled exactly like raised 3D UI cards) */
.roles-list-compact {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
  gap: 6px;
  min-height: 0;
  overflow: hidden;
}
.role-card {
  background: var(--bg-base);
  padding: 6px 14px;
  border-radius: var(--radius-xl);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(255, 255, 255, 0.45);
  transition: transform var(--duration-fast), box-shadow var(--duration-fast);
  flex: 1;
  min-height: 0;
  max-height: 52px;
}
.role-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.role-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.role-icon {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
  box-shadow: var(--neu-inset);
}
.role-icon.orange { color: var(--orange-accent); background: var(--orange-bg-subtle); }
.role-icon.blue   { color: var(--info-600);    background: var(--info-bg); }
.role-icon.green  { color: var(--success-600); background: var(--success-bg); }
.role-icon.purple { color: #8b5cf6;            background: rgba(139, 92, 246, 0.12); }

.role-name {
  font-size: 11px;
  font-weight: var(--weight-bold);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.role-count {
  font-size: 14px;
  font-weight: var(--weight-extrabold);
  color: var(--orange-accent);
  background: var(--bg-input);
  padding: 3px 12px;
  border-radius: var(--radius-pill);
  box-shadow: var(--neu-inset);
  border: 1px solid rgba(166, 169, 173, 0.35);
  flex-shrink: 0;
}

/* ── Loading State ───────────────────────────────────────────── */
.loading-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-muted);
  gap: 12px;
}
.loading-full i {
  font-size: 36px;
  color: var(--orange-accent);
}

@media (max-width: 900px) {
  .minimal-stats-grid { grid-template-columns: repeat(2, 1fr); }
  .bottom-minimal-split { grid-template-columns: 1fr; }
  .dashboard-page { height: auto; max-height: none; overflow: auto; }
}

@media (max-width: 600px) {
  .minimal-stats-grid { grid-template-columns: 1fr; }
}
</style>