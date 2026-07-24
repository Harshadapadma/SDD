import { ref } from 'vue'

// 15 Minutes Inactivity Limit (15 * 60 * 1000 ms)
const INACTIVITY_LIMIT_MS = 15 * 60 * 1000
const LAST_ACTIVITY_KEY = 'sdd_last_activity'
const isLocked = ref(false)
let timer: any = null

export function useInactivityLock() {

  function getStoredLastActivity(): number {
    const val = localStorage.getItem(LAST_ACTIVITY_KEY)
    return val ? parseInt(val, 10) : 0
  }

  function setStoredLastActivity(ts: number = Date.now()) {
    localStorage.setItem(LAST_ACTIVITY_KEY, String(ts))
  }

  function checkInactivityExpired(): boolean {
    const userRaw = localStorage.getItem('user')
    const token = localStorage.getItem('access')
    if (!userRaw || !token) return false

    const last = getStoredLastActivity()
    if (!last) return false

    const elapsed = Date.now() - last
    return elapsed >= INACTIVITY_LIMIT_MS
  }

  function lockSession() {
    const userRaw = localStorage.getItem('user')
    if (!userRaw) return
    isLocked.value = true
  }

  function unlockSession() {
    isLocked.value = false
    setStoredLastActivity(Date.now())
    resetTimer()
  }

  function resetTimer() {
    const userRaw = localStorage.getItem('user')
    const token = localStorage.getItem('access')
    if (!userRaw || !token) {
      isLocked.value = false
      if (timer) clearTimeout(timer)
      return
    }

    if (checkInactivityExpired()) {
      lockSession()
      return
    }

    if (timer) clearTimeout(timer)

    const last = getStoredLastActivity() || Date.now()
    const elapsed = Date.now() - last
    const remaining = Math.max(INACTIVITY_LIMIT_MS - elapsed, 1000)

    timer = setTimeout(() => {
      if (checkInactivityExpired()) {
        lockSession()
      } else {
        resetTimer()
      }
    }, remaining)
  }

  function handleUserActivity() {
    if (isLocked.value) return

    const userRaw = localStorage.getItem('user')
    const token = localStorage.getItem('access')
    if (!userRaw || !token) return

    // CRITICAL: Check if inactivity limit expired before updating activity time!
    if (checkInactivityExpired()) {
      lockSession()
      return
    }

    // Throttle writing to localStorage (update if > 2 seconds since last recorded activity)
    const now = Date.now()
    const last = getStoredLastActivity()
    if (!last || now - last > 2000) {
      setStoredLastActivity(now)
      resetTimer()
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible' && !isLocked.value) {
      if (checkInactivityExpired()) {
        lockSession()
      } else {
        resetTimer()
      }
    }
  }

  function setupListeners() {
    const userRaw = localStorage.getItem('user')
    const token = localStorage.getItem('access')
    if (userRaw && token && !getStoredLastActivity()) {
      setStoredLastActivity(Date.now())
    }

    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
    events.forEach(ev => window.addEventListener(ev, handleUserActivity, { passive: true }))
    document.addEventListener('visibilitychange', handleVisibilityChange)

    if (checkInactivityExpired()) {
      lockSession()
    } else {
      resetTimer()
    }
  }

  function removeListeners() {
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
    events.forEach(ev => window.removeEventListener(ev, handleUserActivity))
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    if (timer) clearTimeout(timer)
  }

  return {
    isLocked,
    lockSession,
    unlockSession,
    setupListeners,
    removeListeners,
    checkInactivityExpired
  }
}
