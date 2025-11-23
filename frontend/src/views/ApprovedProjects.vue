<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>採択実験課題</span>
            <v-btn
              v-if="canManageProjects"
              color="primary"
              @click="openCreateDialog"
            >
              <v-icon left>mdi-plus</v-icon>
              新規課題登録
            </v-btn>
          </v-card-title>

          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="projects"
              :loading="loading"
              class="elevation-1"
            >
              <template v-slot:item.principal_investigators="{ item }">
                <v-chip-group>
                  <v-chip
                    v-for="pi in item.principal_investigators"
                    :key="pi.id"
                    size="small"
                    :color="pi.is_primary ? 'primary' : 'default'"
                  >
                    {{ pi.user ? `${pi.user.last_name} ${pi.user.first_name}` : 'N/A' }}
                  </v-chip>
                </v-chip-group>
              </template>

              <template v-slot:item.beam_requests="{ item }">
                <span>{{ item.beam_requests.length }}件</span>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon
                  size="small"
                  @click="viewProject(item)"
                >
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
                <v-btn
                  v-if="canManageProjects"
                  icon
                  size="small"
                  @click="editProject(item)"
                >
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn
                  v-if="canManageProjects"
                  icon
                  size="small"
                  color="error"
                  @click="confirmDelete(item)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="900px" persistent>
      <v-card>
        <v-card-title>
          {{ editMode ? '課題編集' : '新規課題登録' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form">
            <v-text-field
              v-model="formData.project_number"
              label="課題番号*"
              required
              :rules="[v => !!v || '課題番号は必須です']"
            />
            <v-text-field
              v-model="formData.title"
              label="課題名*"
              required
              :rules="[v => !!v || '課題名は必須です']"
            />
            <v-textarea
              v-model="formData.summary"
              label="課題概要"
              rows="3"
            />

            <v-divider class="my-4" />
            <h3 class="mb-3">課題責任者</h3>
            <v-autocomplete
              v-model="formData.principal_investigator_ids"
              :items="users"
              :item-title="user => `${user.last_name} ${user.first_name} (${user.email})`"
              item-value="id"
              label="課題責任者を選択*"
              multiple
              chips
              closable-chips
              required
              :rules="[v => v && v.length > 0 || '少なくとも1名の課題責任者が必要です']"
            />
            <v-alert type="info" density="compact" class="mb-4">
              最初に選択された方が主責任者となります
            </v-alert>

            <v-divider class="my-4" />
            <h3 class="mb-3">ビーム要求</h3>
            <v-btn
              color="primary"
              variant="outlined"
              size="small"
              @click="addBeamRequest"
              class="mb-3"
            >
              <v-icon left>mdi-plus</v-icon>
              ビーム要求追加
            </v-btn>

            <v-card
              v-for="(beam, index) in formData.beam_requests"
              :key="index"
              class="mb-3"
              variant="outlined"
            >
              <v-card-text>
                <v-row>
                  <v-col cols="12" class="d-flex justify-space-between align-center">
                    <h4>ビーム要求 {{ index + 1 }}</h4>
                    <v-btn
                      icon
                      size="small"
                      color="error"
                      @click="removeBeamRequest(index)"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="beam.beam_species"
                      label="ビーム核種*"
                      required
                      :rules="[v => !!v || 'ビーム核種は必須です']"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="beam.course_id"
                      :items="courses"
                      item-title="name"
                      item-value="id"
                      label="実験コース*"
                      required
                      :rules="[v => !!v || '実験コースは必須です']"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="beam.max_intensity"
                      label="最大ビーム強度"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="beam.required_resolution"
                      label="要求分解能"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="beam.planned_irradiation_hours"
                      label="照射予定時間（時間）*"
                      type="number"
                      min="0"
                      required
                      :rules="[v => v >= 0 || '0以上の値を入力してください']"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="beam.completed_irradiation_hours"
                      label="照射済み時間（時間）"
                      type="number"
                      min="0"
                      :rules="[v => v >= 0 || '0以上の値を入力してください']"
                    />
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="closeDialog">キャンセル</v-btn>
          <v-btn color="primary" @click="saveProject">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- View Dialog -->
    <v-dialog v-model="viewDialog" max-width="800px">
      <v-card v-if="selectedProject">
        <v-card-title>課題詳細</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <strong>課題番号:</strong> {{ selectedProject.project_number }}
            </v-col>
            <v-col cols="12">
              <strong>課題名:</strong> {{ selectedProject.title }}
            </v-col>
            <v-col cols="12">
              <strong>課題概要:</strong>
              <p class="mt-2">{{ selectedProject.summary || 'なし' }}</p>
            </v-col>
            <v-col cols="12">
              <strong>課題責任者:</strong>
              <v-chip-group class="mt-2">
                <v-chip
                  v-for="pi in selectedProject.principal_investigators"
                  :key="pi.id"
                  :color="pi.is_primary ? 'primary' : 'default'"
                >
                  {{ pi.user ? `${pi.user.last_name} ${pi.user.first_name}` : 'N/A' }}
                  {{ pi.is_primary ? '（主責任者）' : '' }}
                </v-chip>
              </v-chip-group>
            </v-col>
            <v-col cols="12">
              <strong>ビーム要求:</strong>
              <v-list>
                <v-list-item
                  v-for="(beam, index) in selectedProject.beam_requests"
                  :key="index"
                >
                  <v-list-item-title>
                    {{ beam.beam_species }} - {{ beam.course?.name || 'N/A' }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    照射予定: {{ beam.planned_irradiation_hours }}時間
                    / 照射済み: {{ beam.completed_irradiation_hours }}時間
                    <span v-if="beam.max_intensity">
                      / 最大強度: {{ beam.max_intensity }}
                    </span>
                    <span v-if="beam.required_resolution">
                      / 要求分解能: {{ beam.required_resolution }}
                    </span>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="viewDialog = false">閉じる</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title>削除確認</v-card-title>
        <v-card-text>
          本当にこの課題を削除しますか？
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="deleteDialog = false">キャンセル</v-btn>
          <v-btn color="error" @click="deleteProject">削除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getCurrentUser } from '../services/api';
import * as api from '../services/api';

const loading = ref(false);
const projects = ref([]);
const users = ref([]);
const courses = ref([]);
const dialog = ref(false);
const viewDialog = ref(false);
const deleteDialog = ref(false);
const editMode = ref(false);
const selectedProject = ref(null);
const projectToDelete = ref(null);
const currentUser = ref(null);

const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
});

const formData = ref({
  project_number: '',
  title: '',
  summary: '',
  principal_investigator_ids: [],
  beam_requests: []
});

const headers = [
  { title: '課題番号', key: 'project_number' },
  { title: '課題名', key: 'title' },
  { title: '課題責任者', key: 'principal_investigators' },
  { title: 'ビーム要求', key: 'beam_requests' },
  { title: '操作', key: 'actions', sortable: false }
];

const canManageProjects = computed(() => {
  if (!currentUser.value || !currentUser.value.role) return false;
  const level = currentUser.value.role.access_level;
  return level >= 4; // ALLOCATOR以上
});

onMounted(async () => {
  await loadCurrentUser();
  await loadProjects();
  await loadUsers();
  await loadCourses();
});

async function loadCurrentUser() {
  try {
    const response = await getCurrentUser();
    currentUser.value = response.data;
  } catch (error) {
    console.error('Failed to load current user:', error);
  }
}

async function loadProjects() {
  loading.value = true;
  try {
    const response = await api.getApprovedProjects();
    projects.value = response.data;
  } catch (error) {
    showSnackbar('課題一覧の取得に失敗しました', 'error');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

async function loadUsers() {
  try {
    const response = await api.get('/users/');
    users.value = response.data;
  } catch (error) {
    console.error('Failed to load users:', error);
  }
}

async function loadCourses() {
  try {
    const response = await api.getExperimentalCourses();
    courses.value = response.data;
  } catch (error) {
    console.error('Failed to load courses:', error);
  }
}

function openCreateDialog() {
  editMode.value = false;
  formData.value = {
    project_number: '',
    title: '',
    summary: '',
    principal_investigator_ids: [],
    beam_requests: []
  };
  dialog.value = true;
}

function editProject(project) {
  editMode.value = true;
  selectedProject.value = project;
  formData.value = {
    project_number: project.project_number,
    title: project.title,
    summary: project.summary,
    principal_investigator_ids: project.principal_investigators.map(pi => pi.user_id),
    beam_requests: project.beam_requests.map(br => ({
      beam_species: br.beam_species,
      max_intensity: br.max_intensity,
      required_resolution: br.required_resolution,
      course_id: br.course_id,
      planned_irradiation_hours: br.planned_irradiation_hours,
      completed_irradiation_hours: br.completed_irradiation_hours
    }))
  };
  dialog.value = true;
}

function viewProject(project) {
  selectedProject.value = project;
  viewDialog.value = true;
}

function closeDialog() {
  dialog.value = false;
  editMode.value = false;
  selectedProject.value = null;
}

function addBeamRequest() {
  formData.value.beam_requests.push({
    beam_species: '',
    max_intensity: '',
    required_resolution: '',
    course_id: null,
    planned_irradiation_hours: 0,
    completed_irradiation_hours: 0
  });
}

function removeBeamRequest(index) {
  formData.value.beam_requests.splice(index, 1);
}

async function saveProject() {
  try {
    if (editMode.value) {
      await api.updateApprovedProject(selectedProject.value.id, formData.value);
      showSnackbar('課題を更新しました', 'success');
    } else {
      await api.createApprovedProject(formData.value);
      showSnackbar('課題を登録しました', 'success');
    }
    closeDialog();
    await loadProjects();
  } catch (error) {
    showSnackbar(
      error.response?.data?.detail || '保存に失敗しました',
      'error'
    );
    console.error(error);
  }
}

function confirmDelete(project) {
  projectToDelete.value = project;
  deleteDialog.value = true;
}

async function deleteProject() {
  try {
    await api.deleteApprovedProject(projectToDelete.value.id);
    showSnackbar('課題を削除しました', 'success');
    deleteDialog.value = false;
    projectToDelete.value = null;
    await loadProjects();
  } catch (error) {
    showSnackbar('削除に失敗しました', 'error');
    console.error(error);
  }
}

function showSnackbar(message, color = 'success') {
  snackbar.value = { show: true, message, color };
}
</script>
