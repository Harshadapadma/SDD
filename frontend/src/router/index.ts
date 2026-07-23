import { createRouter, createWebHistory } from "vue-router";
import { h } from "vue";

import LoginView from "../views/LoginView.vue";
import SetPasswordView from "../views/SetPasswordView.vue";
import AdminDashboard from "../views/admin/AdminDashboard.vue";

import AdminLayout from "../Layouts/AdminLayout.vue";
import UserLayout from "../Layouts/UserLayout.vue";

// Admin pages
import AdminRecords      from "../views/admin/AdminRecords.vue";
import AdminUsers        from "../views/admin/AdminUsers.vue";
import AdminRequests     from "../views/admin/AdminRequests.vue";
import AdminNotifications from "../views/admin/AdminNotifications.vue";
import AuditLog          from "../views/admin/AuditLog.vue";

// User pages
import UserDashboard      from "../views/user/UserDashboard.vue";
import UserRecords        from "../views/user/UserRecords.vue";
import UserRequests       from "../views/user/UserRequests.vue";
import UserProfile        from "../views/user/UserProfile.vue";
import AdminProfile       from "../views/admin/AdminProfile.vue";
import RecordDetailView   from "../views/RecordDetailView.vue";
import UserClarifications from "../views/user/UserClarifications.vue";

const getUser = () => {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
};

const routes = [
  {
    path: "/login",
    component: LoginView,
  },
  {
    path: "/set-password",
    component: SetPasswordView,
  },
  {
    // Root layout — switches between admin and user layout based on role
    path: "/",
    component: {
      render() {
        const user = getUser();
        return (user?.role === "ADMIN" || user?.role === "COMPLIANCE_OFFICER") ? h(AdminLayout) : h(UserLayout);
      },
    },
    meta: { requiresAuth: true },
    children: [
      { 
        path: "",          
        component: {
          render() {
            const u = getUser();
            if (u?.role === "ADMIN") return h(AdminUsers);
            return u?.role === "COMPLIANCE_OFFICER" ? h(AdminDashboard) : h(UserDashboard);
          }
        } 
      },
      { 
        path: "records",   
        component: {
          render() {
            const u = getUser();
            if (u?.role === "ADMIN") return h('div', { style: 'padding: 24px; text-align: center; color: #ef4444; font-weight: bold;' }, 'Unauthorized: Admin role cannot access records');
            return u?.role === "COMPLIANCE_OFFICER" ? h(AdminRecords) : h(UserRecords);
          }
        } 
      },
      {
        path: "requests",
        component: {
          render() {
            const u = getUser();
            if (u?.role === "ADMIN") return h('div', { style: 'padding: 24px; text-align: center; color: #ef4444; font-weight: bold;' }, 'Unauthorized: Admin role cannot access requests');
            return u?.role === "COMPLIANCE_OFFICER" ? h(AdminRequests) : h(UserRequests);
          }
        } 
      },
      {
        path: "profile",
        component: {
          render() {
            const u = getUser();
            return (u?.role === "ADMIN" || u?.role === "COMPLIANCE_OFFICER") ? h(AdminProfile) : h(UserProfile);
          }
        }
      },
      {
        path: "records/:id",
        component: {
          render() {
            const u = getUser();
            if (u?.role === "ADMIN") return h('div', { style: 'padding: 24px; text-align: center; color: #ef4444; font-weight: bold;' }, 'Unauthorized: Admin role cannot access records');
            return h(RecordDetailView);
          }
        }
      },
      { 
        path: "users",     
        component: {
          render() {
            const u = getUser();
            return (u?.role === "ADMIN" || u?.role === "COMPLIANCE_OFFICER") ? h(AdminUsers) : h('div', { style: 'padding: 24px; text-align: center; color: #ef4444; font-weight: bold;' }, 'Unauthorized: Only Admin or Compliance Officer can access users');
          }
        }
      },
      { 
        path: "notifications", 
        component: AdminNotifications // Shared for now, or adapt later
      },
      {
        path: "audit-log",
        component: {
          render() {
            const u = getUser();
            return u?.role === "COMPLIANCE_OFFICER" ? h(AuditLog) : h('div', { style: 'padding: 24px; text-align: center; color: #ef4444; font-weight: bold;' }, 'Unauthorized');
          }
        }
      },
      {
        path: "clarifications",
        component: {
          render() {
            const u = getUser();
            if (u?.role === "ADMIN") return h('div', { style: 'padding: 24px; text-align: center; color: #ef4444; font-weight: bold;' }, 'Unauthorized');
            return h(UserClarifications);
          }
        }
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("access");
  if (to.meta.requiresAuth && !token) {
    next("/login");
  } else {
    next();
  }
});

export default router;