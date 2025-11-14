<template>
  <v-card flat rounded="xl" class="pa-4" color="white">
    <div class="d-flex align-center justify-space-between flex-wrap mb-4">
      <div>
        <h3 class="text-h5 mb-1">Beamtime Calendar</h3>
        <div class="text-body-2 text-medium-emphasis">Track weekly allocations and quickly edit</div>
      </div>
      <div class="d-flex ga-2 align-center">
        <v-btn icon="mdi-chevron-left" variant="text" @click="prev" />
        <v-btn icon="mdi-chevron-right" variant="text" @click="next" />
        <v-btn variant="tonal" @click="view = view === 'week' ? 'month' : 'week'">
          {{ view === 'week' ? 'Month' : 'Week' }} view
        </v-btn>
      </div>
    </div>

    <v-sheet height="580">
      <v-calendar
        v-model="focus"
        :events="events"
        :event-overlap-mode="'stack'"
        :weekdays="weekdays"
        :view="view"
        :loading="loading"
        @click:event="openDialog"
      />
    </v-sheet>

    <v-dialog v-model="dialog" max-width="480">
      <v-card>
        <v-card-title class="text-h6">Update schedule</v-card-title>
        <v-card-text>
          <v-text-field v-model="editable.title" label="Title" />
          <v-text-field v-model="editable.instrument" label="Instrument" />
          <v-textarea v-model="editable.notes" label="Notes" rows="2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Save & Go Back</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { get, patch } from '../services/api';

const props = defineProps({
  schedules: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
});

const emits = defineEmits(['refresh']);

const router = useRouter();
const focus = ref('');
const view = ref('week');
const dialog = ref(false);
const saving = ref(false);
const editable = ref({});

const weekdays = computed(() => (view.value === 'week' ? [1, 2, 3, 4, 5, 6, 0] : undefined));

watch(
  () => props.schedules,
  value => {
    if (value?.length && !focus.value) {
      focus.value = value[0].start;
    }
  },
  { immediate: true }
);

const events = computed(() =>
  props.schedules.map(item => ({
    title: item.title,
    start: item.start,
    end: item.end,
    color: item.status === 'approved' ? 'green' : 'orange',
    instrument: item.instrument,
    requestId: item.id
  }))
);

const prev = () => (focus.value = new Date(focus.value || new Date()).toISOString());
const next = () => (focus.value = new Date(focus.value || new Date()).toISOString());

const openDialog = ({ event }) => {
  editable.value = { ...event, notes: '', instrument: event.instrument };
  dialog.value = true;
};

const save = async () => {
  saving.value = true;
  try {
    await patch(`/beamtimes/${editable.value.requestId}`, editable.value);
    emits('refresh');
    router.back();
  } catch (error) {
    console.error(error);
  } finally {
    saving.value = false;
    dialog.value = false;
  }
};
</script>
