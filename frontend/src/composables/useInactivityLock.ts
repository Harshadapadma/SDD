import { ref } from 'vue'

// 15 Minutes Inactivity Limit (15 * 60 * 1000 ms)
const INACTIVITY_LIMIT_MS = 15 * 60 * 1000
const isLocked = ref(false)

export function useInactivityLock() {
  let timer: any = null

  function resetTimer() {
    const userRaw = localStorage.getItem('user')
    const token = localStorage.getItem('access')
    if (!userRaw || !token) {
      isLocked.value = false
      if (timer) clearTimeout(timer)
      return
    }

    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      lockSession()
    }, INACTIVITY_LIMIT_MS)
  }

  function lockSession() {
    const userRaw = localStorage.getItem('user')
    if (!userRaw) return
    isLocked.value = true
  }

  function unlockSession() {
    isLocked.value = false
    resetTimer()
  }

  function handleUserActivity() {
    if (!isLocked.value) {
      resetTimer()
    }
  }

  function setupListeners() {
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
    events.forEach(ev => window.addEventListener(ev, handleUserActivity, { passive: true }))
    resetTimer()
  }

  function removeListeners() {
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
    events.forEach(ev => window.removeEventListener(ev, handleUserActivity))
    if (timer) clearTimeout(timer)
  }

  return {
    isLocked,
    lockSession,
    unlockSession,
    setupListeners,
    removeListeners
  }
}
