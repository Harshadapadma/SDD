<template>
  <div class="custom-datepicker-wrap" ref="containerRef">
    <!-- Trigger Input Box -->
    <div
      :class="['datepicker-input-box', { open: isOpen, disabled: disabled, has_val: !!modelValue }]"
      @click="togglePicker"
    >
      <i class="fas fa-calendar-alt calendar-icon"></i>
      <span class="date-display">{{ formattedDisplayDate }}</span>
      <i v-if="modelValue && !disabled" class="fas fa-times clear-btn" @click.stop="clearDate" title="Clear Date"></i>
      <i v-else class="fas fa-chevron-down dropdown-arrow" :class="{ rotate: isOpen }"></i>
    </div>

    <!-- Calendar Popover Overlay -->
    <transition name="popover-fade">
      <div v-if="isOpen" class="datepicker-popover" @click.stop>
        <!-- Calendar Header: Month & Year Selector -->
        <div class="popover-header">
          <button type="button" class="nav-btn" @click="prevMonth" title="Previous Month">
            <i class="fas fa-chevron-left"></i>
          </button>
          
          <div class="month-year-selectors">
            <select v-model="viewMonth" class="month-select" @change="onViewChange">
              <option v-for="(m, idx) in monthNames" :key="idx" :value="idx">
                {{ m }}
              </option>
            </select>

            <select v-model="viewYear" class="year-select" @change="onViewChange">
              <option v-for="y in yearOptions" :key="y" :value="y">
                {{ y }}
              </option>
            </select>
          </div>

          <button type="button" class="nav-btn" @click="nextMonth" title="Next Month">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>

        <!-- Days of Week Row -->
        <div class="weekdays-grid">
          <span v-for="d in shortWeekdays" :key="d" class="weekday-name">{{ d }}</span>
        </div>

        <!-- Calendar Days Grid (6 rows x 7 cols = 42 cells) -->
        <div class="days-grid">
          <button
            type="button"
            v-for="(cell, idx) in calendarCells"
            :key="idx"
            :class="[
              'day-cell',
              {
                'out-month': !cell.isCurrentMonth,
                'is-today': cell.isToday,
                'is-selected': cell.isSelected,
                'is-disabled': cell.isDisabled
              }
            ]"
            :disabled="cell.isDisabled"
            @click="selectCell(cell)"
          >
            <span>{{ cell.dayNumber }}</span>
          </button>
        </div>

        <!-- Popover Footer Quick Actions -->
        <div class="popover-footer">
          <button type="button" class="footer-btn today-btn" @click="selectToday">
            <i class="fas fa-calendar-check"></i> Today
          </button>
          <button type="button" class="footer-btn clear-btn-footer" @click="clearDate">
            Clear
          </button>
          <button type="button" class="footer-btn done-btn" @click="isOpen = false">
            Done
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  max: {
    type: String,
    default: ''
  },
  min: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'dd / mm / yyyy'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const containerRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)

const monthNames = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]
const shortWeekdays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

// Viewing Month & Year
const now = new Date()
const viewMonth = ref(now.getMonth())
const viewYear = ref(now.getFullYear())

// Year Options Dropdown Range (e.g. 1950 to Current Year + 5)
const yearOptions = computed(() => {
  const currentY = new Date().getFullYear()
  const years: number[] = []
  for (let y = currentY + 5; y >= 1950; y--) {
    years.push(y)
  }
  return years
})

// Sync View Month/Year when modelValue changes or popover opens
function syncViewFromValue() {
  if (props.modelValue && /^\d{4}-\d{2}-\d{2}$/.test(props.modelValue)) {
    const parts = props.modelValue.split('-')
    viewYear.value = parseInt(parts[0], 10)
    viewMonth.value = parseInt(parts[1], 10) - 1
  } else {
    const today = new Date()
    viewYear.value = today.getFullYear()
    viewMonth.value = today.getMonth()
  }
}

watch(() => props.modelValue, () => {
  syncViewFromValue()
}, { immediate: true })

function togglePicker() {
  if (props.disabled) return
  if (!isOpen.value) {
    syncViewFromValue()
  }
  isOpen.value = !isOpen.value
}

// Formatted Display Date for Input Box (e.g. 24 / 07 / 2026)
const formattedDisplayDate = computed(() => {
  if (!props.modelValue || !/^\d{4}-\d{2}-\d{2}$/.test(props.modelValue)) {
    return props.placeholder
  }
  const parts = props.modelValue.split('-')
  return `${parts[2]} / ${parts[1]} / ${parts[0]}`
})

// Today's YYYY-MM-DD string
const todayStr = computed(() => {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
})

// Calendar Cells Calculation
const calendarCells = computed(() => {
  const cells: Array<{
    dateStr: string
    dayNumber: number
    isCurrentMonth: boolean
    isToday: boolean
    isSelected: boolean
    isDisabled: boolean
  }> = []

  const year = viewYear.value
  const month = viewMonth.value

  const firstDayOfMonth = new Date(year, month, 1)
  const startingDayOfWeek = firstDayOfMonth.getDay() // 0 = Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const prevMonthDays = new Date(year, month, 0).getDate()

  // 1. Prev Month Days
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    const dayNum = prevMonthDays - i
    const prevDate = new Date(year, month - 1, dayNum)
    const dateStr = formatDateToStr(prevDate)
    cells.push({
      dateStr,
      dayNumber: dayNum,
      isCurrentMonth: false,
      isToday: dateStr === todayStr.value,
      isSelected: dateStr === props.modelValue,
      isDisabled: checkIsDisabled(dateStr)
    })
  }

  // 2. Current Month Days
  for (let d = 1; d <= daysInMonth; d++) {
    const currDate = new Date(year, month, d)
    const dateStr = formatDateToStr(currDate)
    cells.push({
      dateStr,
      dayNumber: d,
      isCurrentMonth: true,
      isToday: dateStr === todayStr.value,
      isSelected: dateStr === props.modelValue,
      isDisabled: checkIsDisabled(dateStr)
    })
  }

  // 3. Next Month Days to fill grid up to 42 cells (6 rows)
  const remaining = 42 - cells.length
  for (let d = 1; d <= remaining; d++) {
    const nextDate = new Date(year, month + 1, d)
    const dateStr = formatDateToStr(nextDate)
    cells.push({
      dateStr,
      dayNumber: d,
      isCurrentMonth: false,
      isToday: dateStr === todayStr.value,
      isSelected: dateStr === props.modelValue,
      isDisabled: checkIsDisabled(dateStr)
    })
  }

  return cells
})

function formatDateToStr(d: Date): string {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function checkIsDisabled(dateStr: string): boolean {
  if (props.max && dateStr > props.max) return true
  if (props.min && dateStr < props.min) return true
  return false
}

function selectCell(cell: any) {
  if (cell.isDisabled) return
  emit('update:modelValue', cell.dateStr)
  emit('change', cell.dateStr)
  isOpen.value = false
}

function selectToday() {
  if (checkIsDisabled(todayStr.value)) return
  emit('update:modelValue', todayStr.value)
  emit('change', todayStr.value)
  isOpen.value = false
}

function clearDate() {
  if (props.disabled) return
  emit('update:modelValue', '')
  emit('change', '')
}

function prevMonth() {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value--
  } else {
    viewMonth.value--
  }
}

function nextMonth() {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value++
  } else {
    viewMonth.value++
  }
}

function onViewChange() {
  // Keep viewMonth & viewYear in sync
}

// Close on Click Outside
function handleClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

// Close on Escape Key
function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.custom-datepicker-wrap {
  position: relative;
  width: 100%;
  user-select: none;
}

/* Neumorphic Input Trigger Box */
.datepicker-input-box {
  width: 100%;
  height: 44px;
  background: var(--bg-base, #ffffff);
  border: 1px solid var(--card-divider, #E0D8CC);
  border-radius: var(--radius-xl, 14px);
  box-shadow: var(--neu-inset, inset 2px 2px 5px rgba(0,0,0,0.06), inset -2px -2px 5px rgba(255,255,255,0.8));
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.datepicker-input-box:hover {
  border-color: #ea6c00;
  box-shadow: 0 0 0 3px rgba(234, 108, 0, 0.12);
}

.datepicker-input-box.open {
  border-color: #ea6c00;
  box-shadow: 0 0 0 3px rgba(234, 108, 0, 0.2);
}

.datepicker-input-box.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.calendar-icon {
  color: #ea6c00;
  font-size: 15px;
  flex-shrink: 0;
}

.date-display {
  flex: 1;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  letter-spacing: 0.3px;
}

.datepicker-input-box:not(.has_val) .date-display {
  color: var(--text-muted, #9aa3b8);
  font-weight: 500;
}

.dropdown-arrow {
  font-size: 11px;
  color: #6b7585;
  transition: transform 0.2s ease;
}

.dropdown-arrow.rotate {
  transform: rotate(180deg);
}

.clear-btn {
  font-size: 12px;
  color: #9aa3b8;
  padding: 4px;
  border-radius: 50%;
  transition: all 0.15s ease;
}

.clear-btn:hover {
  color: #dc2626;
  background: #fef2f2;
}

/* Popover Overlay (Compact & Neat) */
.datepicker-popover {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 1050;
  width: 235px;
  background: #ffffff;
  border: 1px solid #E0D8CC;
  border-radius: 14px;
  box-shadow: 0 12px 28px rgba(30, 41, 55, 0.16), 0 3px 8px rgba(234, 108, 0, 0.06);
  padding: 10px 12px;
  backdrop-filter: blur(8px);
}

/* Header Month / Year Selectors */
.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.nav-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid #E0D8CC;
  background: #F9F8F5;
  color: #1f2937;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.nav-btn:hover {
  background: #ea6c00;
  color: #ffffff;
  border-color: #ea6c00;
  box-shadow: 0 2px 6px rgba(234, 108, 0, 0.3);
}

.month-year-selectors {
  display: flex;
  align-items: center;
  gap: 4px;
}

.month-select, .year-select {
  background: #F9F8F5;
  border: 1px solid #E0D8CC;
  border-radius: 6px;
  padding: 2px 5px;
  font-size: 11px;
  font-weight: 700;
  color: #1f2937;
  cursor: pointer;
  outline: none;
  font-family: inherit;
  transition: all 0.15s ease;
}

.month-select:hover, .year-select:hover,
.month-select:focus, .year-select:focus {
  border-color: #ea6c00;
  color: #ea6c00;
}

/* Weekdays Grid */
.weekdays-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  margin-bottom: 4px;
}

.weekday-name {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.5px;
  color: #ea6c00;
  padding: 2px 0;
}

/* Days Grid */
.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 6px;
}

.day-cell {
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #1f2937;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  font-family: inherit;
  padding: 0;
}

.day-cell:hover:not(.is-disabled):not(.is-selected) {
  background: #fff7ed;
  color: #ea6c00;
}

.day-cell.out-month {
  color: #cbd5e1;
  font-weight: 400;
}

.day-cell.is-today {
  border: 1.5px solid #ea6c00;
  color: #ea6c00;
  font-weight: 800;
}

.day-cell.is-selected {
  background: linear-gradient(135deg, #fb923c 0%, #ea6c00 100%) !important;
  color: #ffffff !important;
  font-weight: 800;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(234, 108, 0, 0.35);
}

.day-cell.is-disabled {
  opacity: 0.3;
  cursor: not-allowed;
  text-decoration: line-through;
}

/* Footer Quick Actions */
.popover-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 6px;
  border-top: 1px solid #E8EAED;
  gap: 4px;
}

.footer-btn {
  border: none;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.today-btn {
  background: #fff7ed;
  color: #ea6c00;
  border: 1px solid rgba(234, 108, 0, 0.2);
  display: flex;
  align-items: center;
  gap: 3px;
}

.today-btn:hover {
  background: #ea6c00;
  color: #ffffff;
}

.clear-btn-footer {
  background: #f8fafc;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.clear-btn-footer:hover {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.done-btn {
  background: linear-gradient(135deg, #ea6c00 0%, #c2570a 100%);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(234, 108, 0, 0.25);
  margin-left: auto;
}

.done-btn:hover {
  box-shadow: 0 3px 8px rgba(234, 108, 0, 0.4);
}

/* Transitions */
.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: all 0.15s ease;
}

.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}
</style>
