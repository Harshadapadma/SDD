<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const isOpen = ref(false);

const toggleMenu = () => {
  isOpen.value = !isOpen.value;
};

const logout = () => {
  localStorage.clear();
  router.push("/login");
};
</script>

<template>
  <div class="layout">

    <!-- HEADER -->
    <header class="header">
      <button class="menu-btn" @click="toggleMenu">☰</button>
      <h2>Negen Vault</h2>
    </header>

    <!-- OVERLAY -->
    <div v-if="isOpen" class="overlay" @click="toggleMenu"></div>

    <!-- DRAWER -->
    <aside :class="['drawer', { open: isOpen }]">
      <h3 class="menu-title">Menu</h3>

      <button @click="$router.push('/')">Dashboard</button>
      <button @click="$router.push('/records')">Records</button>
      <button @click="$router.push('/notifications')">Notifications</button>

      <button class="logout" @click="logout">Logout</button>
    </aside>

    <!-- CONTENT -->
    <main class="content">
      <router-view />
    </main>

  </div>
</template>

<style scoped>

/* Layout */
.layout {
  min-height: 100vh;
  background: #f9fafb;
}

/* Header */
.header {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid #e5e7eb;
  background: white;
  position: sticky;
  top: 0;
  z-index: 10;
}

.menu-btn {
  font-size: 20px;
  background: none;
  border: none;
  cursor: pointer;
}

/* Drawer (hidden by default) */
.drawer {
  position: fixed;
  top: 0;
  left: 0;
  transform: translateX(-100%);
  width: 260px;
  height: 100%;
  background: #1f2937;
  color: white;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 20;
}

.drawer.open {
  transform: translateX(0);
}

.menu-title {
  margin-bottom: 20px;
  font-size: 18px;
}

.drawer button {
  margin: 8px 0;
  padding: 10px;
  border: none;
  background: transparent;
  color: white;
  text-align: left;
  cursor: pointer;
  border-radius: 6px;
}

.drawer button:hover {
  background: rgba(255,255,255,0.1);
}

.logout {
  margin-top: auto;
  background: #dc2626;
}

/* Overlay */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 15;
}

/* Content */
.content {
  padding: 24px;
}

</style>