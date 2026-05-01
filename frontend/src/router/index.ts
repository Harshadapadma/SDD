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

// User pages
import UserDashboard      from "../views/user/UserDashboard.vue";
import UserRecords        from "../views/user/UserRecords.vue";
import UserRequests       from "../views/user/UserRequests.vue";
import UserProfile        from "../views/user/UserProfile.vue";
import RecordDetailView   from "../views/RecordDetailView.vue";

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
        return user?.role === "ADMIN" ? h(AdminLayout) : h(UserLayout);
      },
    },
    meta: { requiresAuth: true },
    children: [
      { 
        path: "",          
        component: {
          render() {
            const u = getUser();
            return u?.role === "ADMIN" ? h(AdminDashboard) : h(UserDashboard);
          }
        } 
      },
      { 
        path: "records",   
        component: {
          render() {
            const u = getUser();
            return u?.role === "ADMIN" ? h(AdminRecords) : h(UserRecords);
          }
        } 
      },
      {
        path: "requests",
        component: {
          render() {
            const u = getUser();
            return u?.role === "ADMIN" ? h(AdminRequests) : h(UserRequests);
          }
        } 
      },
      {
        path: "profile",
        component: UserProfile
      },
      {
        path: "records/:id",
        component: RecordDetailView
      },
      { 
        path: "users",     
        component: {
          render() {
            const u = getUser();
            return u?.role === "ADMIN" ? h(AdminUsers) : h('div', 'Unauthorized');
          }
        }
      },
      { 
        path: "requests",  
        component: {
          render() {
            const u = getUser();
            return u?.role === "ADMIN" ? h(AdminRequests) : h('div', 'Unauthorized');
          }
        }
      },
      { 
        path: "notifications", 
        component: AdminNotifications // Shared for now, or adapt later
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