<template>
  <v-app>
    <v-app-bar v-if="showNavigation" app color="indigo-darken-3" prominent>
      <v-app-bar-nav-icon @click="drawer = !drawer" class="d-md-none" />
      <v-toolbar-title>Beamtime Management</v-toolbar-title>
      <v-spacer />
      <v-chip v-if="currentUser" prepend-icon="mdi-account" color="white" variant="outlined" class="mr-2">
        {{ displayName }}
        <template v-if="userRole">
          <v-divider vertical class="mx-2" />
          <span class="text-caption">{{ userRole.display_name }}</span>
        </template>
      </v-chip>
      <v-btn icon="mdi-refresh" :loading="refreshing" @click="refresh" />
      <v-btn icon="mdi-logout" @click="handleLogout" title="Logout" />
    </v-app-bar>

    <v-navigation-drawer v-if="showNavigation" v-model="drawer" app :permanent="$vuetify.display.mdAndUp">
      <v-list density="compact">
        <v-list-item
          v-for="link in filteredLinks"
          :key="link.to"
          :to="link.to"
          router
          @click="onNavItemClick"
        >
          <template #prepend>
            <v-icon :icon="link.icon" />
          </template>
          <v-list-item-title>{{ link.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid class="py-6">
        <router-view @refresh="refresh" />
      </v-container>
    </v-main>

    <v-snackbar v-model="snackbar" :timeout="4000" color="success">
      Data refreshed
      <template #actions>
        <v-btn color="white" text="Close" @click="snackbar = false" />
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { logout, getCurrentUser, getRoles } from './services/api';

const drawer = ref(true);
const snackbar = ref(false);
const refreshing = ref(false);
const currentUser = ref(null);
const roles = ref([]);
const router = useRouter();
const route = useRoute();

const showNavigation = computed(() => route.name !== 'login' && route.name !== 'setup');

const userRole = computed(() => {
  if (!currentUser.value || !currentUser.value.role_id) return null;
  return roles.value.find(r => r.id === currentUser.value.role_id);
});

const displayName = computed(() => {
  if (!currentUser.value) return '';
  const { last_name, middle_name, first_name } = currentUser.value;
  if (last_name && first_name) {
    return middle_name 
      ? `${last_name}, ${middle_name} ${first_name}`
      : `${last_name}, ${first_name}`;
  }
  return currentUser.value.name || currentUser.value.email;
});

const userAccessLevel = computed(() => {
  if (!currentUser.value || !currentUser.value.role_id) return 0;
  const role = roles.value.find(r => r.id === currentUser.value.role_id);
  return role ? role.access_level : 0;
});

const allLinks = [
  { title: 'Schedules', to: '/', icon: 'mdi-calendar-clock', minLevel: 0 },
  { title: 'Management', to: '/management', icon: 'mdi-clipboard-list-outline', minLevel: 0 },
  { title: 'Users', to: '/users', icon: 'mdi-account-group', minLevel: 3 },
  { title: 'Institutions', to: '/institutions', icon: 'mdi-domain', minLevel: 0 },
  { title: 'Approver Setup', to: '/approver-setup', icon: 'mdi-shield-account', minLevel: 0 },
  { title: 'Settings', to: '/settings', icon: 'mdi-cog', minLevel: 0 }
];

const filteredLinks = computed(() => {
  return allLinks.filter(link => userAccessLevel.value >= link.minLevel);
});

const loadUserData = async () => {
  try {
    const [userResponse, rolesResponse] = await Promise.all([
      getCurrentUser(),
      getRoles()
    ]);
    currentUser.value = userResponse.data;
    roles.value = rolesResponse.data;
  } catch (error) {
    console.error('Failed to load user data:', error);
  }
};

const onNavItemClick = () => {
  // モバイル画面でのみドロワーを閉じる
  if (!window.matchMedia('(min-width: 960px)').matches) {
    drawer.value = false;
  }
};

const refresh = async () => {
  refreshing.value = true;
  await router.push(router.currentRoute.value.fullPath);
  refreshing.value = false;
  snackbar.value = true;
};

const handleLogout = async () => {
  await logout();
  currentUser.value = null;
  router.push('/login');
};

onMounted(() => {
  if (showNavigation.value) {
    loadUserData();
  }
});

watch(showNavigation, (newValue) => {
  if (newValue) {
    loadUserData();
  }
});
</script>
