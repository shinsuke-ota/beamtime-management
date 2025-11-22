<template>
  <v-container class="py-8" max-width="760">
    <v-card class="pa-6" rounded="xl">
      <div class="d-flex justify-space-between align-center flex-wrap ga-4 mb-4">
        <div>
          <h1 class="text-h5 mb-1">Approver Registration</h1>
          <p class="text-body-2 text-medium-emphasis mb-0">
            Register the first approver by providing their full information and confirming the email address.
          </p>
        </div>
        <v-chip color="indigo-darken-3" variant="tonal" prepend-icon="mdi-shield-account">Initial setup</v-chip>
      </div>

      <v-alert
        v-if="error"
        type="error"
        border="start"
        prominent
        class="mb-4"
        density="comfortable"
        :text="error"
      />

      <v-alert
        v-if="success"
        type="success"
        border="start"
        prominent
        class="mb-4"
        density="comfortable"
      >
        <div class="d-flex align-center ga-2">
          <v-icon icon="mdi-check-circle" color="success" />
          <div>
            <div class="text-subtitle-1">Approver registered successfully.</div>
            <div class="text-body-2">A one-hour access token has been issued for onboarding.</div>
          </div>
        </div>
      </v-alert>

      <v-form ref="formRef" v-model="formValid" validate-on="submit lazy" @submit.prevent="submit">
        <v-row class="ga-4">
          <v-col cols="12" md="6">
            <v-text-field
              v-model="approver.name"
              label="Full name"
              density="comfortable"
              :rules="[requiredRule]"
              :disabled="submitting || success"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="approver.email"
              label="Email"
              type="email"
              density="comfortable"
              :rules="[requiredRule, emailRule]"
              :disabled="submitting || success"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="approver.affiliation"
              label="Affiliation"
              density="comfortable"
              :rules="[requiredRule]"
              :disabled="submitting || success"
            />
          </v-col>
        </v-row>

        <div class="d-flex justify-end ga-2 mt-2">
          <v-btn
            color="primary"
            prepend-icon="mdi-shield-plus"
            :loading="submitting"
            :disabled="success"
            @click="submit"
          >
            Register approver
          </v-btn>
          <v-btn
            variant="tonal"
            prepend-icon="mdi-view-dashboard"
            :disabled="!success"
            @click="goToDashboard"
          >
            Go to dashboard
          </v-btn>
        </div>
      </v-form>

      <v-expand-transition>
        <v-sheet v-if="success" color="grey-lighten-4" class="pa-4 mt-6 rounded-lg">
          <h2 class="text-subtitle-1 mb-2">Issued access token</h2>
          <p class="text-body-2 text-medium-emphasis mb-3">
            Copy this token to authenticate subsequent requests while configuring the system.
          </p>
          <v-textarea
            v-model="token"
            variant="solo-filled"
            readonly
            rows="3"
            prepend-inner-icon="mdi-key-variant"
          />
        </v-sheet>
      </v-expand-transition>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { post } from '../services/api';

const router = useRouter();

const approver = ref({
  name: '',
  email: '',
  affiliation: ''
});
const error = ref('');
const success = ref(false);
const submitting = ref(false);
const formValid = ref(false);
const token = ref('');
const formRef = ref(null);

const requiredRule = value => !!value || 'This field is required';
const emailRule = value => /.+@.+\..+/.test(value) || 'Enter a valid email address';

const submit = async () => {
  const form = formRef.value;
  if (!form) return;

  const { valid } = await form.validate();
  if (!valid) return;

  submitting.value = true;
  error.value = '';
  try {
    const { data } = await post('/auth/approver-setup', approver.value);
    token.value = data?.token?.access_token || '';
    success.value = true;
  } catch (err) {
    const detail = err?.response?.data?.detail || 'Unable to register approver right now.';
    error.value = Array.isArray(detail) ? detail.join(' ') : detail;
  } finally {
    submitting.value = false;
  }
};

const goToDashboard = () => {
  router.push('/management');
};
</script>
