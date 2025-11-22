<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card elevation="8">
          <v-card-title class="text-h5 bg-indigo-darken-3 text-white">
            Initial Setup - Application Manager Registration
          </v-card-title>
          <v-card-subtitle class="pa-4 text-body-2">
            Welcome! To get started, please register the first Application Manager account.
            This account will have full administrative privileges.
          </v-card-subtitle>
          <v-card-text class="pt-4">
            <v-form @submit.prevent="handleSubmit">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.first_name"
                    label="First Name"
                    variant="outlined"
                    :error-messages="errors.first_name"
                    required
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.middle_name"
                    label="Middle Name (Optional)"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
              </v-row>
              
              <v-text-field
                v-model="formData.last_name"
                label="Last Name"
                variant="outlined"
                :error-messages="errors.last_name"
                required
                density="comfortable"
              />
              
              <v-text-field
                v-model="formData.account_name"
                label="Account Name"
                variant="outlined"
                :error-messages="errors.account_name"
                hint="Lowercase letters, numbers, hyphens, and underscores. 3-32 characters."
                persistent-hint
                required
                density="comfortable"
              />
              
              <v-text-field
                v-model="formData.email"
                label="Email"
                type="email"
                variant="outlined"
                :error-messages="errors.email"
                required
                density="comfortable"
              />
              
              <v-text-field
                v-model="formData.affiliation"
                label="Affiliation (Optional)"
                variant="outlined"
                density="comfortable"
              />
              
              <v-text-field
                v-model="formData.password"
                label="Password"
                :type="showPassword ? 'text' : 'password'"
                variant="outlined"
                :error-messages="errors.password"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                required
                density="comfortable"
              />
              
              <v-text-field
                v-model="confirmPassword"
                label="Confirm Password"
                :type="showConfirmPassword ? 'text' : 'password'"
                variant="outlined"
                :error-messages="errors.confirmPassword"
                :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showConfirmPassword = !showConfirmPassword"
                required
                density="comfortable"
              />
              
              <v-alert v-if="errorMessage" type="error" class="mt-3">
                {{ errorMessage }}
              </v-alert>
              
              <v-btn
                type="submit"
                color="indigo-darken-3"
                block
                size="large"
                class="mt-4"
                :loading="loading"
              >
                Complete Setup
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { setupApplicationManager } from '../services/api';

const router = useRouter();
const loading = ref(false);
const errorMessage = ref('');
const errors = ref({});
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const confirmPassword = ref('');

const formData = ref({
  first_name: '',
  middle_name: '',
  last_name: '',
  account_name: '',
  email: '',
  affiliation: '',
  password: ''
});

const validateForm = () => {
  errors.value = {};
  let isValid = true;

  if (!formData.value.first_name) {
    errors.value.first_name = 'First name is required';
    isValid = false;
  }

  if (!formData.value.last_name) {
    errors.value.last_name = 'Last name is required';
    isValid = false;
  }

  if (!formData.value.account_name) {
    errors.value.account_name = 'Account name is required';
    isValid = false;
  } else if (!/^[a-z][a-z0-9_-]{2,31}$/.test(formData.value.account_name)) {
    errors.value.account_name = 'Invalid format. Must start with a lowercase letter, 3-32 characters.';
    isValid = false;
  }

  if (!formData.value.email) {
    errors.value.email = 'Email is required';
    isValid = false;
  }

  if (!formData.value.password) {
    errors.value.password = 'Password is required';
    isValid = false;
  } else if (formData.value.password.length < 8) {
    errors.value.password = 'Password must be at least 8 characters';
    isValid = false;
  }

  if (formData.value.password !== confirmPassword.value) {
    errors.value.confirmPassword = 'Passwords do not match';
    isValid = false;
  }

  return isValid;
};

const handleSubmit = async () => {
  errorMessage.value = '';
  
  if (!validateForm()) {
    return;
  }

  loading.value = true;
  try {
    await setupApplicationManager(formData.value);
    router.push('/');
  } catch (error) {
    console.error('Setup error:', error);
    if (error.response?.data?.detail) {
      errorMessage.value = error.response.data.detail;
    } else if (error.response?.status === 400) {
      errorMessage.value = 'Setup failed. Please check your information.';
    } else if (error.message) {
      errorMessage.value = `Setup failed: ${error.message}`;
    } else {
      errorMessage.value = 'Setup failed. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};
</script>
