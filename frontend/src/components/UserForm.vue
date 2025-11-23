<template>
  <v-card rounded="lg">
    <v-card-title class="pb-0">{{ isCreateMode ? 'Create User' : 'Edit User' }}</v-card-title>
    <v-card-subtitle class="pt-1">{{ isCreateMode ? 'Add a new user to the system.' : 'Update contact details and affiliation.' }}</v-card-subtitle>

    <v-divider class="my-2" />

    <v-card-text>
      <v-alert
        v-if="loadError"
        type="error"
        border="start"
        density="compact"
        class="mb-4"
        :text="loadError"
      />

      <v-skeleton-loader v-if="loadingUser" type="text, text, text, list-item-two-line@2" />

      <v-form
        v-else
        ref="formRef"
        v-model="formValid"
        validate-on="submit lazy"
        class="d-flex flex-column ga-3"
        @submit.prevent="submit"
      >
        <v-text-field
          v-model="form.account_name"
          label="Account Name"
          density="comfortable"
          :rules="[requiredRule]"
          :disabled="saving"
          hint="Lowercase letters, numbers, hyphens, and underscores (3-32 chars)"
        />

        <v-row dense>
          <v-col cols="12" md="5">
            <v-text-field
              v-model="form.first_name"
              label="First Name"
              density="comfortable"
              :rules="[requiredRule]"
              :disabled="saving"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.middle_name"
              label="Middle Name"
              density="comfortable"
              :disabled="saving"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.last_name"
              label="Last Name"
              density="comfortable"
              :rules="[requiredRule]"
              :disabled="saving"
            />
          </v-col>
        </v-row>

        <v-text-field
          v-model="form.email"
          label="Email"
          type="email"
          density="comfortable"
          :rules="[requiredRule]"
          :disabled="saving"
        />

        <v-text-field
          v-if="isCreateMode"
          v-model="form.password"
          label="Password"
          type="password"
          density="comfortable"
          :rules="[requiredRule]"
          :disabled="saving"
        />

        <v-select
          v-model="form.institution_id"
          :items="institutions"
          item-title="name"
          item-value="id"
          label="機関"
          density="comfortable"
          :disabled="saving"
          clearable
          @update:model-value="onInstitutionChange"
        />

        <v-select
          v-model="form.department_id"
          :items="filteredDepartments"
          item-title="name"
          item-value="id"
          label="所属"
          density="comfortable"
          :disabled="saving || !form.institution_id"
          clearable
        />

        <v-select
          v-model="form.role_id"
          :items="roles"
          item-title="display_name"
          item-value="id"
          label="Role"
          density="comfortable"
          :rules="[requiredRule]"
          :disabled="saving"
        />

        <v-alert
          v-if="submitError"
          type="error"
          border="start"
          density="compact"
          class="mt-2"
          :text="submitError"
        />
      </v-form>
    </v-card-text>

    <v-card-actions class="justify-end">
      <v-btn variant="text" :disabled="saving" @click="emit('cancel')">Cancel</v-btn>
      <v-btn
        color="primary"
        :prepend-icon="isCreateMode ? 'mdi-account-plus' : 'mdi-content-save'"
        :loading="saving"
        :disabled="saving || loadingUser"
        @click="submit"
      >
        {{ isCreateMode ? 'Create' : 'Save Changes' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { onMounted, ref, watch, computed } from 'vue';
import { get, put, post, getInstitutions, getDepartments, getRoles } from '../services/api';

const props = defineProps({
  userId: {
    type: Number,
    default: null
  }
});

const emit = defineEmits(['created', 'updated', 'cancel']);

const formRef = ref(null);
const formValid = ref(false);
const form = ref({
  account_name: '',
  first_name: '',
  middle_name: '',
  last_name: '',
  email: '',
  password: '',
  institution_id: null,
  department_id: null,
  role_id: null
});
const institutions = ref([]);
const departments = ref([]);
const roles = ref([]);
const loadingUser = ref(false);
const saving = ref(false);
const loadError = ref('');
const submitError = ref('');

const isCreateMode = computed(() => !props.userId);

const filteredDepartments = computed(() => {
  if (!form.value.institution_id) return [];
  return departments.value.filter(d => d.institution_id === form.value.institution_id);
});

const onInstitutionChange = () => {
  // 機関が変更されたら所属をクリア
  form.value.department_id = null;
};

const requiredRule = value => !!value || 'This field is required';

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

const fetchUser = async () => {
  if (!props.userId) return;

  loadingUser.value = true;
  loadError.value = '';
  submitError.value = '';
  try {
    const { data } = await get(`/users/${props.userId}`);
    
    // 所属から機関IDを取得
    let institutionId = null;
    if (data.department_id) {
      const dept = departments.value.find(d => d.id === data.department_id);
      if (dept) {
        institutionId = dept.institution_id;
      }
    }
    
    form.value = {
      account_name: data.account_name ?? '',
      first_name: data.first_name ?? '',
      middle_name: data.middle_name ?? '',
      last_name: data.last_name ?? '',
      email: data.email ?? '',
      password: '',
      institution_id: institutionId,
      department_id: data.department_id ?? null,
      role_id: data.role_id ?? null
    };
    formRef.value?.resetValidation?.();
  } catch (err) {
    console.error(err);
    loadError.value = 'Unable to load user details. Please try again later.';
  } finally {
    loadingUser.value = false;
  }
};

const submit = async () => {
  const { valid } = (await formRef.value?.validate?.()) ?? { valid: true };
  if (!valid) return;

  saving.value = true;
  submitError.value = '';
  try {
    if (isCreateMode.value) {
      // Create new user
      await post('/users/', form.value);
      emit('created');
    } else {
      // Update existing user (exclude password if empty)
      const updateData = { ...form.value };
      if (!updateData.password) {
        delete updateData.password;
      }
      await put(`/users/${props.userId}`, updateData);
      emit('updated');
    }
  } catch (err) {
    console.error(err);
    submitError.value = err.response?.data?.detail
      ?? `Unable to ${isCreateMode.value ? 'create' : 'update'} user right now. Please try again later.`;
  } finally {
    saving.value = false;
  }
};

watch(
  () => props.userId,
  () => {
    if (props.userId) {
      fetchUser();
    } else {
      // Reset form for create mode
      form.value = {
        account_name: '',
        first_name: '',
        middle_name: '',
        last_name: '',
        email: '',
        password: '',
        institution_id: null,
        department_id: null,
        role_id: null
      };
    }
  }
);

onMounted(async () => {
  await loadInstitutionsAndDepartments();
  if (props.userId) {
    await fetchUser();
  }
});
</script>
