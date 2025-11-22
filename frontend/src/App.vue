<template>
  <v-app>
    <v-app-bar v-if="showNavigation" app color="indigo-darken-3" prominent>
      <v-app-bar-nav-icon @click="drawer = !drawer" class="d-md-none" />
      <v-toolbar-title>Beamtime Management</v-toolbar-title>
      <v-spacer />
      <v-btn icon="mdi-refresh" :loading="refreshing" @click="refresh" />
      <v-btn icon="mdi-logout" @click="handleLogout" title="Logout" />
    </v-app-bar>

    <v-navigation-drawer v-if="showNavigation" v-model="drawer" app :permanent="$vuetify.display.mdAndUp">
      <v-list density="compact">
        <v-list-item
          v-for="link in links"
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
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { logout } from './services/api';

const drawer = ref(true);
const snackbar = ref(false);
const refreshing = ref(false);
const router = useRouter();
const route = useRoute();

const showNavigation = computed(() => route.name !== 'login' && route.name !== 'setup');

const onNavItemClick = () => {
  // モバイル画面でのみドロワーを閉じる
  if (!window.matchMedia('(min-width: 960px)').matches) {
    drawer.value = false;
  }
};

const links = [
  { title: 'Schedules', to: '/', icon: 'mdi-calendar-clock' },
  { title: 'Management', to: '/management', icon: 'mdi-clipboard-list-outline' },
  { title: 'Users', to: '/users', icon: 'mdi-account-group' },
  { title: 'Institutions', to: '/institutions', icon: 'mdi-domain' },
  { title: 'Approver Setup', to: '/approver-setup', icon: 'mdi-shield-account' }
];

const refresh = async () => {
  refreshing.value = true;
  await router.push(router.currentRoute.value.fullPath);
  refreshing.value = false;
  snackbar.value = true;
};

const handleLogout = async () => {
  await logout();
  router.push('/login');
};
</script>
