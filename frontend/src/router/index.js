import { createRouter, createWebHistory } from 'vue-router';
import BeamtimeSchedules from '../views/BeamtimeSchedules.vue';
import ManagementDashboard from '../views/ManagementDashboard.vue';

const routes = [
  { path: '/', name: 'schedules', component: BeamtimeSchedules },
  { path: '/management', name: 'management', component: ManagementDashboard }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
