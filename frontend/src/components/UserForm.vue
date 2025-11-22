<template>
  <v-card rounded="lg">
    <v-card-title class="pb-0">Edit User</v-card-title>
    <v-card-subtitle class="pt-1">Update contact details and affiliation.</v-card-subtitle>

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
          v-model="form.name"
          label="Name"
          density="comfortable"
          :rules="[requiredRule]"
          :disabled="saving"
        />

        <v-text-field
          v-model="form.email"
          label="Email"
          type="email"
          density="comfortable"
          :rules="[requiredRule]"
          :disabled="saving"
        />

        <v-text-field
          v-model="form.affiliation"
          label="Affiliation"
          density="comfortable"
          :disabled="saving"
        />

        <v-select
          v-model="form.role"
          :items="roleChoices"
          label="Role"
          density="comfortable"
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
        prepend-icon="mdi-content-save"
        :loading="saving"
        :disabled="saving || loadingUser"
        @click="submit"
      >
        Save Changes
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { get, put } from '../services/api';

const props = defineProps({
  userId: {
    type: Number,
    required: true
  }
});

const emit = defineEmits(['updated', 'cancel']);

const formRef = ref(null);
const formValid = ref(false);
const form = ref({
  name: '',
  email: '',
  affiliation: '',
  role: ''
});
const loadingUser = ref(false);
const saving = ref(false);
const loadError = ref('');
const submitError = ref('');

const roleChoices = ['PI', 'PROJECT_MANAGER', 'ALLOCATOR', 'APPROVER'];

const requiredRule = value => !!value || 'This field is required';

const fetchUser = async () => {
  if (!props.userId) return;

  loadingUser.value = true;
  loadError.value = '';
  submitError.value = '';
  try {
    const { data } = await get(`/users/${props.userId}`);
    form.value = {
      name: data.name ?? '',
      email: data.email ?? '',
      affiliation: data.affiliation ?? '',
      role: data.role ?? ''
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
    await put(`/users/${props.userId}`, form.value);
    emit('updated');
  } catch (err) {
    console.error(err);
    submitError.value = 'Unable to update user right now. Please try again later.';
  } finally {
    saving.value = false;
  }
};

watch(
  () => props.userId,
  () => {
    fetchUser();
  }
);

onMounted(fetchUser);
</script>
