import { ref, computed } from 'vue'
import api from '../api/client'

// ─── Shared singleton state ───────────────────────────────────
const notifications  = ref<any[]>([])
const hasPendingRequests   = ref(false)
const pendingRequestsCount = ref(0)
const hasUnreadClarifications   = ref(false)
const unreadClarificationsCount = ref(0)
const isMuted        = ref(localStorage.getItem('notif_muted')       === 'true')
const isSoundMuted   = ref(localStorage.getItem('notif_sound_muted') === 'true')
const toasts         = ref<any[]>([])   // active toast popups
const seenIds        = new Set<number>() // IDs already shown as toast
let   pollTimer: ReturnType<typeof setInterval> | null = null

// ─── Universal chime (one simple two-note ding for everything) ─
function playChime() {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const gain = ctx.createGain()
    gain.connect(ctx.destination)
    gain.gain.setValueAtTime(0.15, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.55)

    // Two sine tones staggered slightly: A5 then C#6 — clean, neutral ding
    const frequencies = [880, 1108]
    frequencies.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      osc.type = 'sine'
      osc.frequency.value = freq
      osc.connect(gain)
      osc.start(ctx.currentTime + i * 0.07)
      osc.stop(ctx.currentTime + 0.55)
    })

    setTimeout(() => ctx.close(), 700)
  } catch (_) {}
}

export type NotificationType = 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR'

export function useNotifications() {

  // ─── Derived ─────────────────────────────────────────────────
  const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

  // ─── Fetch Pending Requests & Unread Clarifications ─────────
  async function fetchPendingRequestsCount() {
    try {
      const res = await api.get('workflows/pending-count/')
      pendingRequestsCount.value = res.data.pending_count || 0
      hasPendingRequests.value   = Boolean(res.data.has_pending)
      unreadClarificationsCount.value = res.data.unread_clarifications_count || 0
      hasUnreadClarifications.value   = Boolean(res.data.has_unread_clarifications)
    } catch (_) {
      hasPendingRequests.value   = false
      pendingRequestsCount.value = 0
      hasUnreadClarifications.value   = false
      unreadClarificationsCount.value = 0
    }
  }

  // ─── Fetch & detect new ──────────────────────────────────────
  async function fetchNotifications() {
    fetchPendingRequestsCount()
    try {
      const res = await api.get('notifications/', { params: { page_size: 50 } })
      const fetched: any[] = res.data.results || res.data

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

  // ─── Mute toggles ─────────────────────────────────────────────
  function toggleMute() {
    isMuted.value = !isMuted.value
    localStorage.setItem('notif_muted', String(isMuted.value))
  }

  function toggleSoundMute() {
    isSoundMuted.value = !isSoundMuted.value
    localStorage.setItem('notif_sound_muted', String(isSoundMuted.value))
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

    // Play chime unless sound is muted
    if (!isSoundMuted.value) {
      playChime()
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
    notifications, unreadCount, isMuted, isSoundMuted, toasts,
    hasPendingRequests, pendingRequestsCount,
    hasUnreadClarifications, unreadClarificationsCount,
    fetchPendingRequestsCount,
    fetchNotifications, startPolling, stopPolling,
    markRead, markAllRead, toggleMute, toggleSoundMute, dismissToast,
    notify,
    typeIcon, typeColor, formatTime,
  }
}

