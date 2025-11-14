<template>
  <v-app>
    <v-app-bar app color="indigo-darken-3" prominent>
      <v-app-bar-nav-icon @click="drawer = !drawer" class="d-sm-none" />
      <v-toolbar-title>Beamtime Management</v-toolbar-title>
      <v-spacer />
      <v-btn icon="mdi-refresh" :loading="refreshing" @click="refresh" />
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" app :permanent="$vuetify.display.mdAndUp">
      <v-list density="compact">
        <v-list-item
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          router
          @click="drawer = $vuetify.display.mdAndUp"
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
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const drawer = ref(false);
const snackbar = ref(false);
const refreshing = ref(false);
const router = useRouter();

const links = [
  { title: 'Schedules', to: '/', icon: 'mdi-calendar-clock' },
  { title: 'Management', to: '/management', icon: 'mdi-clipboard-list-outline' }
];

const refresh = async () => {
  refreshing.value = true;
  await router.push(router.currentRoute.value.fullPath);
  refreshing.value = false;
  snackbar.value = true;
};
</script>
