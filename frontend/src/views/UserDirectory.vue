<template>
  <v-card rounded="xl" class="pa-4" color="white">
    <div class="d-flex flex-wrap align-center justify-space-between ga-4 mb-4">
      <div>
        <h2 class="text-h6 mb-1">User Directory</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">Browse and manage users across the facility.</p>
      </div>
      <div class="d-flex ga-2 align-center">
        <v-btn icon="mdi-refresh" :loading="loading" variant="tonal" @click="refreshDirectory" />
      </div>
    </div>

    <v-row class="ga-4 mb-2">
      <v-col cols="12" md="4">
        <v-text-field
          v-model="search"
          density="comfortable"
          label="Search by name or email"
          prepend-inner-icon="mdi-magnify"
          clearable
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-select
          v-model="roleFilter"
          :items="roleOptions"
          label="Filter by role"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-select
          v-model="affiliationFilter"
          :items="affiliationOptions"
          label="Filter by affiliation"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
    </v-row>

    <v-alert
      v-if="error"
      type="error"
      border="start"
      prominent
      class="mb-4"
      :text="error"
    />

    <v-data-table
      :items="filteredUsers"
      :headers="headers"
      :loading="loading"
      class="rounded-lg"
      hover
      item-key="id"
    >
      <template #item.role="{ item }">
        <v-chip size="small" color="primary" variant="tonal">{{ item.role }}</v-chip>
      </template>
      <template #item.affiliation="{ item }">
        <v-chip size="small" color="teal-lighten-3" variant="tonal">{{ item.affiliation }}</v-chip>
      </template>
      <template #loading>
        <v-skeleton-loader type="table-row@5" />
      </template>
      <template #no-data>
        <div class="text-center py-6 text-medium-emphasis">No users match the current filters.</div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { get } from '../services/api';

const emit = defineEmits(['refresh']);

const users = ref([]);
const loading = ref(false);
const error = ref('');
const search = ref('');
const roleFilter = ref(null);
const affiliationFilter = ref(null);

const headers = [
  { title: 'Name', value: 'name' },
  { title: 'Email', value: 'email' },
  { title: 'Role', value: 'role' },
  { title: 'Affiliation', value: 'affiliation' },
  { title: 'Status', value: 'status' }
];

const roleOptions = computed(() => {
  const roles = users.value.map(user => user.role).filter(Boolean);
  return Array.from(new Set(roles)).sort();
});

const affiliationOptions = computed(() => {
  const affiliations = users.value.map(user => user.affiliation).filter(Boolean);
  return Array.from(new Set(affiliations)).sort();
});

const filteredUsers = computed(() =>
  users.value.filter(user => {
    const matchesSearch = [user.name, user.email]
      .filter(Boolean)
      .some(field => field.toLowerCase().includes(search.value.trim().toLowerCase()));
    const matchesRole = !roleFilter.value || user.role === roleFilter.value;
    const matchesAffiliation = !affiliationFilter.value || user.affiliation === affiliationFilter.value;
    return matchesSearch && matchesRole && matchesAffiliation;
  })
);

const loadUsers = async () => {
  loading.value = true;
  error.value = '';
  try {
    const { data } = await get('/users/');
    users.value = data;
  } catch (err) {
    console.error(err);
    users.value = [];
    error.value = 'Unable to load users right now. Please try again later.';
  } finally {
    loading.value = false;
  }
};

const refreshDirectory = async () => {
  await loadUsers();
  emit('refresh');
};

onMounted(loadUsers);
</script>
