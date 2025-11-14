<template>
  <v-row class="ga-6" align="stretch">
    <v-col cols="12" md="4">
      <v-card rounded="xl" class="pa-4" color="white">
        <div class="d-flex align-center justify-space-between mb-4">
          <h3 class="text-h6 mb-0">PI Profile</h3>
          <v-chip size="small" color="blue-grey-lighten-1">{{ profile.status }}</v-chip>
        </div>
        <v-form @submit.prevent="updateProfile">
          <v-text-field v-model="profile.name" label="Name" density="comfortable" />
          <v-text-field v-model="profile.email" label="Email" type="email" density="comfortable" />
          <v-text-field v-model="profile.phone" label="Phone" density="comfortable" />
          <v-btn block color="primary" type="submit" :loading="savingProfile">Save profile</v-btn>
        </v-form>
      </v-card>

      <v-card rounded="xl" class="pa-4 mt-6" color="white">
        <div class="d-flex align-center justify-space-between mb-4">
          <h3 class="text-h6 mb-0">Monthly Listings</h3>
          <v-select
            v-model="selectedMonth"
            :items="months"
            label="Month"
            density="comfortable"
            hide-details
            variant="outlined"
            class="w-50"
          />
        </div>
        <v-list lines="two" density="compact">
          <v-skeleton-loader v-if="loadingListing" type="list-item" :loading="true" />
          <template v-else>
            <v-list-item
              v-for="item in listings"
              :key="item.id"
              :title="item.project"
              :subtitle="`${item.hours} h on ${item.instrument}`"
            />
          </template>
        </v-list>
      </v-card>
    </v-col>

    <v-col cols="12" md="8" class="d-flex flex-column ga-6">
      <v-card rounded="xl" class="pa-4" color="white">
        <div class="d-flex align-center justify-space-between mb-4 flex-wrap">
          <h3 class="text-h6 mb-0">Projects</h3>
          <v-btn prepend-icon="mdi-plus" variant="tonal" @click="resetProject">New project</v-btn>
        </div>
        <v-form @submit.prevent="saveProject">
          <v-row class="ga-2">
            <v-col cols="12" md="6"><v-text-field v-model="projectForm.title" label="Title" /></v-col>
            <v-col cols="12" md="6"><v-text-field v-model="projectForm.code" label="Code" /></v-col>
            <v-col cols="12"><v-textarea v-model="projectForm.description" label="Description" rows="2" /></v-col>
          </v-row>
          <div class="d-flex ga-2">
            <v-btn color="primary" type="submit" :loading="savingProject">Save</v-btn>
            <v-btn variant="text" @click="resetProject">Reset</v-btn>
          </div>
        </v-form>
        <v-divider class="my-4" />
        <v-chip-group column>
          <v-chip
            v-for="project in projects"
            :key="project.id"
            class="ma-1"
            closable
            @click="projectForm = { ...project }"
            @click:close="removeProject(project)"
          >
            {{ project.title }}
          </v-chip>
        </v-chip-group>
      </v-card>

      <v-card rounded="xl" class="pa-4" color="white">
        <h3 class="text-h6 mb-4">Allocations & Approvals</h3>
        <v-row class="ga-4">
          <v-col cols="12" md="6">
            <v-form @submit.prevent="saveAllocation">
              <v-select v-model="allocation.projectId" :items="projects" item-title="title" item-value="id" label="Project" />
              <v-text-field v-model.number="allocation.hours" type="number" label="Hours" />
              <v-text-field v-model="allocation.instrument" label="Instrument" />
              <v-btn color="primary" block type="submit" :loading="savingAllocation">Allocate</v-btn>
            </v-form>
          </v-col>
          <v-col cols="12" md="6">
            <v-list lines="two" class="border rounded-lg">
              <v-list-item
                v-for="request in approvals"
                :key="request.id"
                :title="request.project"
                :subtitle="`${request.hours} h awaiting approval`"
              >
                <template #append>
                  <v-btn icon="mdi-check" size="small" variant="text" @click="approveRequest(request)" />
                </template>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-card>
    </v-col>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.message }}
      <template #actions>
        <v-btn text="Close" @click="snackbar.show = false" />
      </template>
    </v-snackbar>
  </v-row>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { get, post, patch, del } from '../services/api';

const profile = ref({ name: '', email: '', phone: '', status: 'draft' });
const savingProfile = ref(false);
const projects = ref([]);
const projectForm = ref({ title: '', code: '', description: '' });
const savingProject = ref(false);
const approvals = ref([]);
const allocation = ref({ projectId: null, hours: 8, instrument: '' });
const savingAllocation = ref(false);
const listings = ref([]);
const loadingListing = ref(false);
const selectedMonth = ref(new Date().toISOString().slice(0, 7));
const months = Array.from({ length: 6 }, (_, index) => {
  const date = new Date();
  date.setMonth(date.getMonth() - index);
  return date.toISOString().slice(0, 7);
});

const snackbar = ref({ show: false, message: '', color: 'success' });

const notify = (message, color = 'success') => {
  snackbar.value = { show: true, message, color };
};

const updateProfile = async () => {
  savingProfile.value = true;
  try {
    await patch('/pi/profile', profile.value);
    notify('Profile updated');
  } catch (error) {
    notify('Unable to update profile', 'error');
  } finally {
    savingProfile.value = false;
  }
};

const loadProfile = async () => {
  try {
    const { data } = await get('/pi/profile');
    profile.value = data;
  } catch (error) {
    console.error(error);
  }
};

const loadProjects = async () => {
  try {
    const { data } = await get('/projects');
    projects.value = data;
  } catch (error) {
    console.error(error);
  }
};

const saveProject = async () => {
  savingProject.value = true;
  try {
    if (projectForm.value.id) {
      await patch(`/projects/${projectForm.value.id}`, projectForm.value);
    } else {
      await post('/projects', projectForm.value);
    }
    notify('Project saved');
    projectForm.value = { title: '', code: '', description: '' };
    loadProjects();
  } catch (error) {
    notify('Unable to save project', 'error');
  } finally {
    savingProject.value = false;
  }
};

const resetProject = () => {
  projectForm.value = { title: '', code: '', description: '' };
};

const removeProject = async project => {
  try {
    await del(`/projects/${project.id}`);
    projects.value = projects.value.filter(item => item.id !== project.id);
    notify('Project removed');
  } catch (error) {
    notify('Unable to remove project', 'error');
  }
};

const loadApprovals = async () => {
  try {
    const { data } = await get('/approvals/pending');
    approvals.value = data;
  } catch (error) {
    console.error(error);
  }
};

const saveAllocation = async () => {
  savingAllocation.value = true;
  const optimistic = [...listings.value];
  try {
    await post('/allocations', allocation.value);
    notify('Allocation saved');
    allocation.value = { projectId: null, hours: 8, instrument: '' };
    loadListings();
  } catch (error) {
    notify('Unable to allocate', 'error');
    listings.value = optimistic;
  } finally {
    savingAllocation.value = false;
  }
};

const approveRequest = async request => {
  const previous = approvals.value;
  approvals.value = approvals.value.filter(item => item.id !== request.id);
  try {
    await patch(`/approvals/${request.id}`, { status: 'approved' });
    notify('Request approved');
  } catch (error) {
    approvals.value = previous;
    notify('Unable to approve request', 'error');
  }
};

const loadListings = async () => {
  loadingListing.value = true;
  try {
    const { data } = await get(`/allocations/monthly?month=${selectedMonth.value}`);
    listings.value = data;
  } catch (error) {
    listings.value = [];
  } finally {
    loadingListing.value = false;
  }
};

watch(selectedMonth, loadListings);

onMounted(() => {
  loadProfile();
  loadProjects();
  loadApprovals();
  loadListings();
});
</script>
