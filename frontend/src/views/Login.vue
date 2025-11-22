<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card elevation="8">
          <v-card-title class="text-h5 bg-indigo-darken-3 text-white">
            Login
          </v-card-title>
          <v-card-text class="pt-6">
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="Email"
                type="email"
                prepend-inner-icon="mdi-email"
                variant="outlined"
                :error-messages="errors.email"
                required
              />
              <v-text-field
                v-model="password"
                label="Password"
                type="password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
                :error-messages="errors.password"
                required
                class="mt-2"
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
                Login
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
import { login } from '../services/api';

const router = useRouter();
const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');
const errors = ref({});

const handleLogin = async () => {
  errors.value = {};
  errorMessage.value = '';

  if (!email.value) {
    errors.value.email = 'Email is required';
    return;
  }
  if (!password.value) {
    errors.value.password = 'Password is required';
    return;
  }

  loading.value = true;
  try {
    await login({ email: email.value, password: password.value });
    // Redirect to the originally requested page or home
    const redirect = router.currentRoute.value.query.redirect || '/';
    router.replace(redirect);
  } catch (error) {
    if (error.response?.status === 401) {
      errorMessage.value = 'Invalid email or password';
    } else {
      errorMessage.value = error.response?.data?.detail || 'Login failed. Please try again.';
    }
  } finally {
    loading.value = false;
  }
};
</script>
