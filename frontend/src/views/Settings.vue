<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Settings</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8" lg="6">
        <v-card>
          <v-card-title>
            <span class="text-h6">プロファイル</span>
          </v-card-title>
          <v-card-text>
            <v-alert v-if="error" type="error" class="mb-4" dismissible @click:close="error = ''">
              {{ error }}
            </v-alert>
            <v-alert v-if="success" type="success" class="mb-4" dismissible @click:close="success = ''">
              {{ success }}
            </v-alert>

            <v-form ref="formRef" @submit.prevent="saveProfile">
              <v-text-field
                v-model="form.account_name"
                label="Account Name"
                hint="小文字英数字、ハイフン、アンダースコアのみ（3-32文字）"
                persistent-hint
                :rules="accountNameRules"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                readonly
                disabled
              />

              <v-text-field
                v-model="form.first_name"
                label="First Name *"
                :rules="[v => !!v || 'First name is required']"
                variant="outlined"
                density="comfortable"
                class="mb-4"
              />

              <v-text-field
                v-model="form.middle_name"
                label="Middle Name"
                variant="outlined"
                density="comfortable"
                class="mb-4"
              />

              <v-text-field
                v-model="form.last_name"
                label="Last Name *"
                :rules="[v => !!v || 'Last name is required']"
                variant="outlined"
                density="comfortable"
                class="mb-4"
              />

              <v-text-field
                v-model="form.email"
                label="Email *"
                type="email"
                :rules="emailRules"
                variant="outlined"
                density="comfortable"
                class="mb-4"
              />

              <v-select
                v-model="form.institution_id"
                :items="institutions"
                item-title="name"
                item-value="id"
                label="機関"
                variant="outlined"
                density="comfortable"
                clearable
                class="mb-4"
                @update:model-value="onInstitutionChange"
              />

              <v-select
                v-model="form.department_id"
                :items="filteredDepartments"
                item-title="name"
                item-value="id"
                label="所属部門"
                variant="outlined"
                density="comfortable"
                clearable
                class="mb-4"
                :disabled="!form.institution_id"
              />

              <v-text-field
                v-model="form.role"
                label="Role"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                readonly
                disabled
              />

              <v-divider class="my-6" />

              <div class="d-flex justify-end">
                <v-btn
                  type="submit"
                  color="primary"
                  :loading="loading"
                  prepend-icon="mdi-content-save"
                >
                  保存
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getCurrentUser, put, getInstitutions, getDepartments } from '../services/api';

const formRef = ref(null);
const loading = ref(false);
const error = ref('');
const success = ref('');
const currentUser = ref(null);
const institutions = ref([]);
const departments = ref([]);

const form = ref({
  account_name: '',
  first_name: '',
  middle_name: '',
  last_name: '',
  email: '',
  institution_id: null,
  department_id: null,
  role: ''
});

const accountNameRules = [
  v => !!v || 'Account name is required',
  v => /^[a-z][a-z0-9_-]{2,31}$/.test(v) || 'Must start with lowercase letter, 3-32 characters, lowercase letters, numbers, hyphens, underscores only'
];

const emailRules = [
  v => !!v || 'Email is required',
  v => /.+@.+\..+/.test(v) || 'Email must be valid'
];

const filteredDepartments = computed(() => {
  if (!form.value.institution_id) return [];
  return departments.value.filter(d => d.institution_id === form.value.institution_id);
});

const onInstitutionChange = () => {
  // Clear department when institution changes
  const dept = departments.value.find(d => d.id === form.value.department_id);
  if (!dept || dept.institution_id !== form.value.institution_id) {
    form.value.department_id = null;
  }
};

const loadUserData = async () => {
  try {
    const response = await getCurrentUser();
    currentUser.value = response.data;
    
    // Populate form with current user data
    form.value = {
      account_name: currentUser.value.account_name || '',
      first_name: currentUser.value.first_name || '',
      middle_name: currentUser.value.middle_name || '',
      last_name: currentUser.value.last_name || '',
      email: currentUser.value.email || '',
      institution_id: null,
      department_id: currentUser.value.department_id || null,
      role: currentUser.value.role || ''
    };

    // Find institution_id from department
    if (form.value.department_id) {
      const dept = departments.value.find(d => d.id === form.value.department_id);
      if (dept) {
        form.value.institution_id = dept.institution_id;
      }
    }
  } catch (err) {
    console.error('Failed to load user data:', err);
    error.value = 'ユーザー情報の読み込みに失敗しました';
  }
};

const loadInstitutionsAndDepartments = async () => {
  try {
    const [institutionsRes, departmentsRes] = await Promise.all([
      getInstitutions(),
      getDepartments()
    ]);
    institutions.value = institutionsRes.data;
    departments.value = departmentsRes.data;
  } catch (err) {
    console.error('Failed to load institutions/departments:', err);
  }
};

const saveProfile = async () => {
  const { valid } = await formRef.value.validate();
  if (!valid) return;

  loading.value = true;
  error.value = '';
  success.value = '';

  try {
    const updateData = {
      first_name: form.value.first_name,
      middle_name: form.value.middle_name || '',
      last_name: form.value.last_name,
      email: form.value.email,
      department_id: form.value.department_id
    };

    await put(`/users/${currentUser.value.id}`, updateData);
    success.value = 'プロファイルを更新しました';
    
    // Reload user data to reflect changes
    await loadUserData();
  } catch (err) {
    console.error('Failed to update profile:', err);
    error.value = err.response?.data?.detail || 'プロファイルの更新に失敗しました';
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadInstitutionsAndDepartments();
  await loadUserData();
});
</script>
