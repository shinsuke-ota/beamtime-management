<template>
  <v-row class="ga-6" align="stretch">
    <v-col cols="12" md="7">
      <schedule-calendar
        :schedules="schedules"
        :loading="loading"
        @refresh="loadSchedules"
      />
    </v-col>
    <v-col cols="12" md="5">
      <schedule-list
        :schedules="schedules"
        :loading="loading"
        @refresh="loadSchedules"
      />
      <v-alert
        v-if="error"
        type="error"
        class="mt-4"
        border="start"
        prominent
        :text="error"
      />
    </v-col>
  </v-row>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import ScheduleCalendar from '../components/ScheduleCalendar.vue';
import ScheduleList from '../components/ScheduleList.vue';
import { get } from '../services/api';

const schedules = ref([]);
const loading = ref(false);
const error = ref('');

const loadSchedules = async () => {
  loading.value = true;
  error.value = '';
  try {
    const { data } = await get('/beamtimes');
    schedules.value = data;
  } catch (err) {
    error.value = 'Unable to load schedules right now.';
    console.error(err);
  } finally {
    loading.value = false;
  }
};

onMounted(loadSchedules);
</script>
