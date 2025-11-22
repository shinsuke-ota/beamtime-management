import { createRouter, createWebHistory } from 'vue-router';
import BeamtimeSchedules from '../views/BeamtimeSchedules.vue';
import ManagementDashboard from '../views/ManagementDashboard.vue';
import UserDirectory from '../views/UserDirectory.vue';
import ApproverSetup from '../views/ApproverSetup.vue';

const routes = [
  { path: '/', name: 'schedules', component: BeamtimeSchedules },
  { path: '/management', name: 'management', component: ManagementDashboard },
  { path: '/users', name: 'users', component: UserDirectory },
  { path: '/approver-setup', name: 'approver-setup', component: ApproverSetup }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
