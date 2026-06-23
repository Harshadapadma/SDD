<template>
  <div class="dashboard-page">
    
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Admin Dashboard</h1>
        <p class="page-sub">System-wide overview and performance analytics</p>
      </div>
      <div class="date-chip">
        <i class="fas fa-calendar"></i>
        {{ currentDateTime }}
      </div>
    </div>

    <!-- OVERVIEW STATS -->
    <div class="stats-grid" v-if="stats">
      <div class="stat-card" v-for="item in overviewStats" :key="item.label">
        <div :class="['stat-icon-wrap', item.color]">
          <i :class="['fas', item.icon]"></i>
        </div>
        <div class="stat-content">
          <div class="stat-val">{{ item.val }}</div>
          <div class="stat-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- CHARTS SECTION -->
    <div class="charts-grid" v-if="stats">
      
      <!-- LINE CHART: RECORD GROWTH -->
      <div class="chart-card large">
        <div class="chart-header">
          <h3>Record Inflow (Last 14 Days)</h3>
          <p>Daily growth trend of newly added records</p>
        </div>
        <div class="chart-body">
          <Bar v-if="growthChartData" :data="growthChartData" :options="barOptions" />
        </div>
      </div>

      <!-- PIE CHART: USER ROLES -->
      <div class="chart-card">
        <div class="chart-header">
          <h3>User Distribution</h3>
          <p>Ratio of Admins, Collaborators and Viewers</p>
        </div>
        <div class="chart-body compact">
          <Doughnut v-if="roleChartData" :data="roleChartData" :options="doughnutOptions" />
        </div>
      </div>

      <!-- STATUS CHART: WORKFLOWS -->
      <div class="chart-card">
        <div class="chart-header">
          <h3>Workflow Status</h3>
          <p>Summary of all processed & pending requests</p>
        </div>
        <div class="chart-body compact">
          <Doughnut v-if="statusChartData" :data="statusChartData" :options="doughnutOptions" />
        </div>
      </div>

    </div>

    <!-- LOADING STATE -->
    <div v-else-if="loading" class="loading-full">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Aggregating system statistics...</p>
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
  LinearScale,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js'
import { Bar, Doughnut } from 'vue-chartjs'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement
)

const stats = ref<any>(null)
const loading = ref(true)
const currentDateTime = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })

async function fetchStats() {
  try {
    const res = await api.get('auth/dashboard-stats/')
    stats.value = res.data
  } catch (e) {
    console.error('Failed to fetch dashboard stats', e)
  } finally {
    loading.value = false
  }
}

const overviewStats = computed(() => {
  if (!stats.value) return []
  return [
    { label: 'Total Users', val: stats.value.overview.total_users, icon: 'fa-users', color: 'green' },
    { label: 'Total Records', val: stats.value.overview.total_records, icon: 'fa-database', color: 'blue' },
    { label: 'Pending Requests', val: stats.value.overview.total_pending, icon: 'fa-clock', color: 'orange' },
  ]
})

// ─── Chart Data Preparations ──────────────────────────────────

const growthChartData = computed(() => {
  if (!stats.value) return null
  return {
    labels: stats.value.record_growth.map((d: any) => d.date),
    datasets: [{
      label: 'New Records',
      data: stats.value.record_growth.map((d: any) => d.count),
      backgroundColor: '#3d5a80',
      borderRadius: 6,
      barThickness: 16,
    }]
  }
})

const roleChartData = computed(() => {
  if (!stats.value) return null
  return {
    labels: ['Admins', 'Collaborators', 'Viewers'],
    datasets: [{
      data: [
        stats.value.role_distribution.ADMIN,
        stats.value.role_distribution.COLLABORATOR,
        stats.value.role_distribution.VIEWER
      ],
      backgroundColor: ['#ee6c4d', '#3d5a80', '#98c1d9'],
      borderWidth: 0,
      hoverOffset: 10
    }]
  }
})

const statusChartData = computed(() => {
  if (!stats.value) return null
  return {
    labels: ['Pending', 'Approved', 'Rejected'],
    datasets: [{
      data: [
        stats.value.request_status.PENDING,
        stats.value.request_status.APPROVED,
        stats.value.request_status.REJECTED
      ],
      backgroundColor: ['#f59e0b', '#22c55e', '#ef4444'],
      borderWidth: 0,
      hoverOffset: 10
    }]
  }
})

// ─── Chart Options ───────────────────────────────────────────

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { 
      beginAtZero: true, 
      grid: { display: false },
      ticks: {
        stepSize: 1,
        precision: 0
      }
    },
    x: { grid: { display: false } }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const, labels: { usePointStyle: true, boxWidth: 6, padding: 20 } }
  },
  cutout: '70%'
}

onMounted(fetchStats)
</script>

<style scoped>
.dashboard-page {
  display: flex; flex-direction: column; gap: 24px;
  animation: fadeIn 0.4s ease both;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ─── Header ─────────────────────────────────────────────────── */
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 24px; font-weight: 800; color: #1e293b; margin: 0; }
.page-sub { font-size: 14px; color: #64748b; margin-top: 4px; }

.date-chip {
  background: linear-gradient(135deg, #f0faf5, #e6f5ee);
  border: 1.5px solid rgba(47, 125, 101, 0.15); border-radius: 999px;
  padding: 8px 16px; font-size: 13px; font-weight: 600; color: #2f7d65;
  display: flex; align-items: center; gap: 8px;
}

/* ─── Stats Grid ────────────────────────────────────────────── */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.stat-card {
  background: linear-gradient(135deg, #f5fbf7 0%, #ecf5ef 100%);
  border-radius: 20px; padding: 24px;
  border: 1px solid rgba(47, 125, 101, 0.12); display: flex; align-items: center; gap: 20px;
  box-shadow: 0 4px 20px rgba(47, 125, 101, 0.04);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease;
  position: relative; overflow: hidden;
}
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
}
.stat-card:nth-child(1) { animation: fadeInUp 0.4s ease 0.05s both; }
.stat-card:nth-child(2) { animation: fadeInUp 0.4s ease 0.12s both; }
.stat-card:nth-child(3) { animation: fadeInUp 0.4s ease 0.19s both; }
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(47, 125, 101, 0.1); }

.stat-icon-wrap {
  width: 54px; height: 54px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center; font-size: 22px;
  transition: transform 0.2s ease;
}
.stat-card:hover .stat-icon-wrap { transform: scale(1.1); }
.stat-icon-wrap.green  { background: #dcfce7; color: #15803d; }
.stat-icon-wrap.blue   { background: #e0f2fe; color: #0369a1; }
.stat-icon-wrap.orange { background: #fef3c7; color: #b45309; }

.stat-val { font-size: 26px; font-weight: 800; color: #1e293b; }
.stat-label { font-size: 13px; color: #64748b; font-weight: 500; }

/* ─── Charts Grid ───────────────────────────────────────────── */
.charts-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;
}
.chart-card {
  background: white; border-radius: 24px; border: 1px solid rgba(47, 125, 101, 0.1);
  padding: 24px; display: flex; flex-direction: column; gap: 20px;
  box-shadow: 0 4px 25px rgba(47, 125, 101, 0.04);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease;
  animation: fadeInUp 0.4s ease 0.25s both;
}
.chart-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(47, 125, 101, 0.08); }
.chart-card.large { grid-column: span 2; }

.chart-header h3 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0; }
.chart-header p { font-size: 12px; color: #94a3b8; margin-top: 4px; }

.chart-body { height: 300px; position: relative; }
.chart-body.compact { height: 240px; }

/* ─── Loading ────────────────────────────────────────────────── */
.loading-full {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 100px 0; color: #64748b; gap: 16px;
}
.loading-full i { font-size: 40px; color: #2f7d65; }

@media (max-width: 1100px) {
  .charts-grid { grid-template-columns: 1fr; }
  .chart-card.large { grid-column: span 1; }
  .stats-grid { grid-template-columns: 1fr; }
}
</style>