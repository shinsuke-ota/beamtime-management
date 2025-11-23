import { createRouter, createWebHistory } from 'vue-router';
import BeamtimeSchedules from '../views/BeamtimeSchedules.vue';
import ManagementDashboard from '../views/ManagementDashboard.vue';
import UserDirectory from '../views/UserDirectory.vue';
import ApproverSetup from '../views/ApproverSetup.vue';
import Login from '../views/Login.vue';
import ApplicationManagerSetup from '../views/ApplicationManagerSetup.vue';
import InstitutionManagement from '../views/InstitutionManagement.vue';
import Settings from '../views/Settings.vue';
import ApprovedProjects from '../views/ApprovedProjects.vue';
import { getCurrentUser, getSetupStatus } from '../services/api';

const routes = [
  { path: '/setup', name: 'setup', component: ApplicationManagerSetup, meta: { requiresAuth: false, requiresSetup: false } },
  { path: '/login', name: 'login', component: Login, meta: { requiresAuth: false } },
  { path: '/', name: 'schedules', component: BeamtimeSchedules, meta: { requiresAuth: true } },
  { path: '/management', name: 'management', component: ManagementDashboard, meta: { requiresAuth: true } },
  { path: '/users', name: 'users', component: UserDirectory, meta: { requiresAuth: true } },
  { path: '/approver-setup', name: 'approver-setup', component: ApproverSetup, meta: { requiresAuth: true } },
  { path: '/institutions', name: 'institutions', component: InstitutionManagement, meta: { requiresAuth: true } },
  { path: '/settings', name: 'settings', component: Settings, meta: { requiresAuth: true } },
  { path: '/approved-projects', name: 'approved-projects', component: ApprovedProjects, meta: { requiresAuth: true } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard to check setup status and authentication
router.beforeEach(async (to, from, next) => {
  // Check setup status
  try {
    const setupStatus = await getSetupStatus();
    
    // If setup is required and not going to setup page, redirect to setup
    if (setupStatus.requires_setup && to.name !== 'setup') {
      next({ name: 'setup' });
      return;
    }
    
    // If setup is complete and trying to access setup page, redirect to home
    if (!setupStatus.requires_setup && to.name === 'setup') {
      next({ name: 'schedules' });
      return;
    }
  } catch (error) {
    console.error('Setup status check failed:', error);
  }

  const requiresAuth = to.meta.requiresAuth !== false;
  
  if (requiresAuth) {
    try {
      await getCurrentUser();
      next();
    } catch (error) {
      if (error.response?.status === 401) {
        next({ name: 'login', query: { redirect: to.fullPath } });
      } else {
        console.error('Auth check failed:', error);
        next({ name: 'login' });
      }
    }
  } else {
    next();
  }
});

export default router;
