<template>
  <div v-if="!canViewUsers">
    <v-alert type="warning" prominent border="start" class="ma-4">
      <v-alert-title>Access Denied</v-alert-title>
      You do not have permission to view the user directory. Level 3 access or higher is required.
    </v-alert>
  </div>
  <v-card v-else rounded="xl" class="pa-4" color="white">
    <div class="d-flex flex-wrap align-center justify-space-between ga-4 mb-4">
      <div>
        <h2 class="text-h6 mb-1">User Directory</h2>
        <p class="text-body-2 text-medium-emphasis mb-0">Browse and manage users across the facility.</p>
      </div>
      <div class="d-flex ga-2 align-center">
        <v-btn v-if="canCreateUsers" color="primary" prepend-icon="mdi-account-plus" @click="openCreateDialog">New User</v-btn>
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
          hide-details
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="roleFilter"
          :items="roleOptions"
          label="Filter by role"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="institutionFilter"
          :items="institutions"
          item-title="name"
          item-value="id"
          label="Filter by 機関"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" md="2">
        <v-select
          v-model="departmentFilter"
          :items="filteredDepartmentsForFilter"
          item-title="name"
          item-value="id"
          label="Filter by 所属"
          density="comfortable"
          clearable
          hide-details
          :disabled="!institutionFilter"
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
      <template v-slot:[`item.role`]="{ item }">
        <v-chip size="small" color="primary" variant="tonal">{{ item.role }}</v-chip>
      </template>
      <template v-slot:[`item.institution_name`]="{ item }">
        <span class="text-body-2">{{ item.institution_name || '-' }}</span>
      </template>
      <template v-slot:[`item.department_name`]="{ item }">
        <span class="text-body-2">{{ item.department_name || '-' }}</span>
      </template>
      <template v-slot:[`item.actions`]="{ item }">
        <v-btn
          icon="mdi-pencil"
          variant="text"
          color="primary"
          @click.stop="openEditDialog(item.raw ?? item)"
        />
      </template>
      <template #loading>
        <v-skeleton-loader type="table-row@5" />
      </template>
      <template #no-data>
        <div class="text-center py-6 text-medium-emphasis">No users match the current filters.</div>
      </template>
    </v-data-table>

    <v-dialog v-model="showCreateDialog" max-width="720">
      <UserForm
        :key="'create'"
        @cancel="closeCreateDialog"
        @created="handleUserCreated"
      />
    </v-dialog>

    <v-dialog v-model="showEditDialog" max-width="720">
      <UserForm
        v-if="selectedUserId"
        :key="selectedUserId"
        :user-id="selectedUserId"
        @cancel="closeEditDialog"
        @updated="handleUserUpdated"
      />
    </v-dialog>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { get, post, getInstitutions, getDepartments, getRoles, getCurrentUser } from '../services/api';
import UserForm from '../components/UserForm.vue';

const emit = defineEmits(['refresh']);

const users = ref([]);
const institutions = ref([]);
const departments = ref([]);
const roles = ref([]);
const currentUser = ref(null);
const loading = ref(false);
const error = ref('');
const search = ref('');
const roleFilter = ref(null);
const institutionFilter = ref(null);
const departmentFilter = ref(null);
const showCreateDialog = ref(false);
const showEditDialog = ref(false);
const selectedUserId = ref(null);

const headers = [
  { title: 'Account Name', value: 'account_name' },
  { title: 'First Name', value: 'first_name' },
  { title: 'Middle Name', value: 'middle_name' },
  { title: 'Last Name', value: 'last_name' },
  { title: 'Email', value: 'email' },
  { title: 'Role', value: 'role' },
  { title: '機関', value: 'institution_name' },
  { title: '所属部門', value: 'department_name' },
  { title: 'Actions', value: 'actions', sortable: false, align: 'end' }
];

const roleOptions = computed(() => {
  const roles = users.value.map(user => user.role).filter(Boolean);
  return Array.from(new Set(roles)).sort();
});

const filteredDepartmentsForFilter = computed(() => {
  if (!institutionFilter.value) return [];
  return departments.value.filter(d => d.institution_id === institutionFilter.value);
});

const canViewUsers = computed(() => {
  if (!currentUser.value || !currentUser.value.role_id) return false;
  const userRole = roles.value.find(r => r.id === currentUser.value.role_id);
  return userRole && userRole.access_level >= 3;
});

const canCreateUsers = computed(() => {
  if (!currentUser.value || !currentUser.value.role_id) return false;
  const userRole = roles.value.find(r => r.id === currentUser.value.role_id);
  return userRole && userRole.access_level >= 4;
});

const roleChoices = ['PI', 'PROJECT_MANAGER', 'ALLOCATOR', 'APPROVER'];

const filteredUsers = computed(() =>
  users.value
    .filter(user => {
      const matchesSearch = [user.name, user.email]
        .filter(Boolean)
        .some(field => field.toLowerCase().includes(search.value.trim().toLowerCase()));
      const matchesRole = !roleFilter.value || user.role === roleFilter.value;
      const matchesInstitution = !institutionFilter.value || (() => {
        const dept = departments.value.find(d => d.id === user.department_id);
        return dept && dept.institution_id === institutionFilter.value;
      })();
      const matchesDepartment = !departmentFilter.value || user.department_id === departmentFilter.value;
      return matchesSearch && matchesRole && matchesInstitution && matchesDepartment;
    })
    .map(user => {
      const dept = departments.value.find(d => d.id === user.department_id);
      const inst = dept ? institutions.value.find(i => i.id === dept.institution_id) : null;
      return {
        ...user,
        department_name: dept?.name || null,
        institution_name: inst?.name || null
      };
    })
);

const loadInstitutionsAndDepartments = async () => {
  try {
    const [institutionsRes, departmentsRes, rolesRes] = await Promise.all([
      getInstitutions(),
      getDepartments(),
      getRoles()
    ]);
    institutions.value = institutionsRes.data;
    departments.value = departmentsRes.data;
    roles.value = rolesRes.data;
  } catch (err) {
    console.error('Failed to load institutions/departments/roles:', err);
  }
};

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

const openCreateDialog = () => {
  showCreateDialog.value = true;
};

const closeCreateDialog = () => {
  showCreateDialog.value = false;
};

const openEditDialog = user => {
  selectedUserId.value = user.id;
  showEditDialog.value = true;
};

const closeEditDialog = () => {
  showEditDialog.value = false;
  selectedUserId.value = null;
};

const handleUserCreated = async () => {
  await refreshDirectory();
  closeCreateDialog();
};

const handleUserUpdated = async () => {
  await refreshDirectory();
  closeEditDialog();
};

watch(institutionFilter, () => {
  departmentFilter.value = null;
});

watch(showEditDialog, value => {
  if (!value) {
    selectedUserId.value = null;
  }
});

onMounted(async () => {
  try {
    const [userResponse, rolesResponse] = await Promise.all([
      getCurrentUser(),
      getRoles()
    ]);
    currentUser.value = userResponse.data;
    roles.value = rolesResponse.data;
  } catch (error) {
    console.error('Failed to load user/roles:', error);
  }
  await loadInstitutionsAndDepartments();
  if (canViewUsers.value) {
    await loadUsers();
  }
});
</script>
