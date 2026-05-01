import { ref, computed } from 'vue'
import api from '../api/client'

// ─── Shared singleton state ───────────────────────────────────
const notifications  = ref<any[]>([])
const isMuted        = ref(localStorage.getItem('notif_muted') === 'true')
const toasts         = ref<any[]>([])   // active toast popups
const seenIds        = new Set<number>() // IDs already shown as toast
let   pollTimer: ReturnType<typeof setInterval> | null = null

// A soft, very short beep base64 (tiny wav file)
const CHIME_AUDIO = 'data:audio/wav;base64,UklGRjIAAABXQVZFZm10IBIAAAABAAEAQB8AAEAfAAABAAgAAABmYWN0BAAAAAAAAABkYXRhAAAAAA==';

export type NotificationType = 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR'

export function useNotifications() {

  // ─── Derived ─────────────────────────────────────────────────
  const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

  // ─── Fetch & detect new ──────────────────────────────────────
  async function fetchNotifications() {
    try {
      const res = await api.get('notifications/')
      const fetched: any[] = res.data

      // Detect brand-new notifications (not seen before)
      if (seenIds.size > 0 && !isMuted.value) {
        fetched.forEach(n => {
          if (!seenIds.has(n.id) && !n.is_read) {
            pushToast(n)
          }
        })
      }

      // Mark all current IDs as seen
      fetched.forEach(n => seenIds.add(n.id))
      notifications.value = fetched
    } catch (_) {
      // silently ignore (user may not be logged in)
    }
  }

  // ─── Poll every 12 seconds ───────────────────────────────────
  function startPolling() {
    if (pollTimer) return
    fetchNotifications()
    pollTimer = setInterval(fetchNotifications, 12_000)
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  }

  // ─── Mark read ───────────────────────────────────────────────
  async function markRead(id: number) {
    const n = notifications.value.find(x => x.id === id)
    if (!n || n.is_read) return
    try {
      await api.post(`notifications/${id}/read/`)
      n.is_read = true
    } catch (_) {}
  }

  async function markAllRead() {
    const unread = notifications.value.filter(n => !n.is_read)
    await Promise.all(unread.map(n => api.post(`notifications/${n.id}/read/`)))
    notifications.value.forEach(n => (n.is_read = true))
  }

  // ─── Mute toggle ─────────────────────────────────────────────
  function toggleMute() {
    isMuted.value = !isMuted.value
    localStorage.setItem('notif_muted', String(isMuted.value))
  }

  // ─── Toast queue ─────────────────────────────────────────────
  let toastCounter = 0

  function pushToast(n: any) {
    const id = ++toastCounter
    toasts.value.push({
      title: n.title || 'Notification',
      message: n.message || '',
      type: n.type || 'INFO',
      _tid: id,
      leaving: false
    })

    // Play chime if not muted
    if (!isMuted.value) {
      try {
        const audio = new Audio(CHIME_AUDIO)
        audio.volume = 0.5
        audio.play().catch(() => {})
      } catch (e) {}
    }

    // After 5.0 s start the "fly to bell" exit animation
    setTimeout(() => {
      const t = toasts.value.find(x => x._tid === id)
      if (t) t.leaving = true
      // Remove from DOM 500ms after animation starts
      setTimeout(() => {
        toasts.value = toasts.value.filter(x => x._tid !== id)
      }, 500)
    }, 5000)
  }

  function dismissToast(tid: number) {
    const t = toasts.value.find(x => x._tid === tid)
    if (t) t.leaving = true
    setTimeout(() => { toasts.value = toasts.value.filter(x => x._tid !== tid) }, 500)
  }

  /**
   * Manually trigger a flash message (toast)
   */
  function notify(title: string, message: string, type: NotificationType = 'INFO') {
    pushToast({ title, message, type })
  }

  // ─── Helpers ─────────────────────────────────────────────────
  function typeIcon(type: string) {
    return { INFO: 'fa-circle-info', SUCCESS: 'fa-circle-check', WARNING: 'fa-triangle-exclamation', ERROR: 'fa-circle-xmark' }[type] ?? 'fa-bell'
  }

  function typeColor(type: string) {
    return { INFO: '#3b82f6', SUCCESS: '#22c55e', WARNING: '#f59e0b', ERROR: '#ef4444' }[type] ?? '#2f7d65'
  }

  function formatTime(d: string) {
    if (!d) return ''
    const diff = Math.floor((Date.now() - new Date(d).getTime()) / 1000)
    if (diff < 60)   return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400)return `${Math.floor(diff / 3600)}h ago`
    return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
  }

  return {
    notifications, unreadCount, isMuted, toasts,
    fetchNotifications, startPolling, stopPolling,
    markRead, markAllRead, toggleMute, dismissToast,
    notify,
    typeIcon, typeColor, formatTime,
  }
}

