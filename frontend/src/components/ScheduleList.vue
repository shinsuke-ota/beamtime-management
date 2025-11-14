<template>
  <v-card flat rounded="xl" color="white" class="pa-4">
    <div class="d-flex align-center justify-space-between flex-wrap mb-4">
      <div>
        <h3 class="text-h5 mb-1">Upcoming Beamtime</h3>
        <div class="text-body-2 text-medium-emphasis">List view with inline approvals</div>
      </div>
      <v-btn prepend-icon="mdi-plus" color="primary" @click="showCreate = true">New request</v-btn>
    </div>

    <v-data-table
      :items="schedules"
      :headers="headers"
      :loading="loading"
      item-value="id"
      density="comfortable"
      class="text-body-2"
    >
      <template #item.status="{ item }">
        <v-chip :color="item.status === 'approved' ? 'green' : 'orange'" size="small" label>
          {{ item.status }}
        </v-chip>
      </template>
      <template #item.actions="{ item }">
        <v-btn icon="mdi-check" variant="text" @click="approve(item)"></v-btn>
        <v-btn icon="mdi-pencil" variant="text" @click="edit(item)"></v-btn>
      </template>
    </v-data-table>

    <v-dialog v-model="showCreate" max-width="520">
      <v-card>
        <v-card-title class="text-h6">Create Beamtime Request</v-card-title>
        <v-card-text class="d-flex flex-column ga-3">
          <v-text-field v-model="draft.title" label="Title" />
          <v-text-field v-model="draft.instrument" label="Instrument" />
          <v-text-field v-model="draft.start" label="Start" type="date" />
          <v-text-field v-model="draft.end" label="End" type="date" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCreate = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="submit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref } from 'vue';
import { post, patch } from '../services/api';

const props = defineProps({
  schedules: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
});

const emits = defineEmits(['refresh']);

const headers = [
  { title: 'Title', key: 'title' },
  { title: 'Instrument', key: 'instrument' },
  { title: 'Start', key: 'start' },
  { title: 'End', key: 'end' },
  { title: 'Status', key: 'status' },
  { title: '', key: 'actions', sortable: false }
];

const showCreate = ref(false);
const saving = ref(false);
const draft = ref({ title: '', instrument: '', start: '', end: '' });

const submit = async () => {
  saving.value = true;
  try {
    await post('/beamtimes', draft.value);
    showCreate.value = false;
    draft.value = { title: '', instrument: '', start: '', end: '' };
    emits('refresh');
  } catch (error) {
    console.error(error);
  } finally {
    saving.value = false;
  }
};

const approve = async item => {
  const optimistic = [...props.schedules];
  const index = optimistic.findIndex(entry => entry.id === item.id);
  if (index > -1) {
    optimistic[index] = { ...optimistic[index], status: 'approved' };
  }
  emits('refresh');
  try {
    await patch(`/beamtimes/${item.id}/approve`);
  } catch (error) {
    console.error(error);
  }
};

const edit = item => {
  draft.value = { title: item.title, instrument: item.instrument, start: item.start, end: item.end };
  showCreate.value = true;
};
</script>
