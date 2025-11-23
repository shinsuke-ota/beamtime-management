<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">機関・所属管理</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <span class="text-h6">機関一覧</span>
            <v-spacer></v-spacer>
            <v-btn v-if="canManageInstitutions" color="primary" @click="openInstitutionDialog()">
              <v-icon left>mdi-plus</v-icon>
              機関追加
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="institution in institutions"
                :key="institution.id"
                @click="selectInstitution(institution)"
                :class="{ 'bg-blue-grey-lighten-5': selectedInstitution?.id === institution.id }"
              >
                <v-list-item-title>{{ institution.name }}</v-list-item-title>
                <template v-slot:append>
                  <v-btn
                    v-if="canManageInstitutions"
                    icon="mdi-pencil"
                    size="small"
                    variant="text"
                    @click.stop="openInstitutionDialog(institution)"
                  ></v-btn>
                  <v-btn
                    v-if="canManageInstitutions"
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click.stop="deleteInstitution(institution)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <span class="text-h6">所属一覧</span>
            <v-spacer></v-spacer>
            <v-btn
              v-if="canManageInstitutions"
              color="primary"
              @click="openDepartmentDialog()"
              :disabled="!selectedInstitution"
            >
              <v-icon left>mdi-plus</v-icon>
              所属追加
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-alert v-if="!selectedInstitution" type="info" variant="tonal">
              機関を選択してください
            </v-alert>
            <v-list v-else>
              <v-list-item
                v-for="department in filteredDepartments"
                :key="department.id"
              >
                <v-list-item-title>{{ department.name }}</v-list-item-title>
                <template v-slot:append>
                  <v-btn
                    v-if="canManageInstitutions"
                    icon="mdi-pencil"
                    size="small"
                    variant="text"
                    @click="openDepartmentDialog(department)"
                  ></v-btn>
                  <v-btn
                    v-if="canManageInstitutions"
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click="deleteDepartment(department)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Institution Dialog -->
    <v-dialog v-model="institutionDialog" max-width="500px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h6">{{ editingInstitution ? '機関編集' : '機関追加' }}</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="institutionFormRef">
            <v-text-field
              v-model="institutionForm.name"
              label="機関名"
              :rules="[v => !!v || '機関名は必須です']"
              required
              variant="outlined"
              density="comfortable"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeInstitutionDialog">キャンセル</v-btn>
          <v-btn color="primary" @click="saveInstitution">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Department Dialog -->
    <v-dialog v-model="departmentDialog" max-width="500px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h6">{{ editingDepartment ? '所属編集' : '所属追加' }}</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="departmentFormRef">
            <v-text-field
              v-if="!editingDepartment"
              :model-value="selectedInstitution?.name"
              label="機関"
              readonly
              variant="outlined"
              density="comfortable"
              class="mb-2"
            ></v-text-field>
            <v-select
              v-else
              v-model="departmentForm.institution_id"
              :items="institutions"
              item-title="name"
              item-value="id"
              label="機関"
              :rules="[v => !!v || '機関は必須です']"
              required
              variant="outlined"
              density="comfortable"
              class="mb-2"
            ></v-select>
            <v-text-field
              v-model="departmentForm.name"
              label="所属名"
              :rules="[v => !!v || '所属名は必須です']"
              required
              variant="outlined"
              density="comfortable"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDepartmentDialog">キャンセル</v-btn>
          <v-btn color="primary" @click="saveDepartment">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getInstitutions,
  createInstitution,
  updateInstitution,
  deleteInstitution as deleteInstitutionApi,
  getDepartments,
  createDepartment,
  updateDepartment,
  deleteDepartment as deleteDepartmentApi,
  getCurrentUser,
  getRoles
} from '../services/api'

const institutions = ref([])
const departments = ref([])
const selectedInstitution = ref(null)
const currentUser = ref(null)
const roles = ref([])

const institutionDialog = ref(false)
const departmentDialog = ref(false)
const editingInstitution = ref(null)
const editingDepartment = ref(null)

const institutionForm = ref({
  name: ''
})

const departmentForm = ref({
  name: '',
  institution_id: null
})

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const filteredDepartments = computed(() => {
  if (!selectedInstitution.value) return []
  return departments.value.filter(
    d => d.institution_id === selectedInstitution.value.id
  )
})

const canManageInstitutions = computed(() => {
  if (!currentUser.value || !currentUser.value.role_id) return false
  const userRole = roles.value.find(r => r.id === currentUser.value.role_id)
  return userRole && userRole.access_level >= 4
})

const loadInstitutions = async () => {
  try {
    const response = await getInstitutions()
    institutions.value = response.data
  } catch (error) {
    showSnackbar('機関の読み込みに失敗しました', 'error')
  }
}

const loadDepartments = async () => {
  try {
    const response = await getDepartments()
    departments.value = response.data
  } catch (error) {
    showSnackbar('所属の読み込みに失敗しました', 'error')
  }
}

const selectInstitution = (institution) => {
  selectedInstitution.value = institution
}

const openInstitutionDialog = (institution = null) => {
  editingInstitution.value = institution
  if (institution) {
    institutionForm.value = { name: institution.name }
  } else {
    institutionForm.value = { name: '' }
  }
  institutionDialog.value = true
}

const openDepartmentDialog = (department = null) => {
  editingDepartment.value = department
  if (department) {
    departmentForm.value = {
      name: department.name,
      institution_id: department.institution_id
    }
  } else {
    departmentForm.value = {
      name: '',
      institution_id: selectedInstitution.value?.id || null
    }
  }
  departmentDialog.value = true
}

const closeInstitutionDialog = () => {
  institutionDialog.value = false
  institutionForm.value = { name: '' }
}

const closeDepartmentDialog = () => {
  departmentDialog.value = false
  departmentForm.value = { name: '', institution_id: null }
}

const saveInstitution = async () => {
  try {
    const formData = { name: institutionForm.value.name }
    if (editingInstitution.value) {
      await updateInstitution(editingInstitution.value.id, formData)
      showSnackbar('機関を更新しました', 'success')
    } else {
      await createInstitution(formData)
      showSnackbar('機関を追加しました', 'success')
    }
    institutionDialog.value = false
    await loadInstitutions()
  } catch (error) {
    showSnackbar(error.response?.data?.detail || error.message || '保存に失敗しました', 'error')
  }
}

const saveDepartment = async () => {
  try {
    const formData = {
      name: departmentForm.value.name,
      institution_id: departmentForm.value.institution_id
    }
    if (editingDepartment.value) {
      await updateDepartment(editingDepartment.value.id, formData)
      showSnackbar('所属を更新しました', 'success')
    } else {
      await createDepartment(formData)
      showSnackbar('所属を追加しました', 'success')
    }
    departmentDialog.value = false
    await loadDepartments()
  } catch (error) {
    showSnackbar(error.response?.data?.detail || error.message || '保存に失敗しました', 'error')
  }
}

const deleteInstitution = async (institution) => {
  if (!confirm(`機関「${institution.name}」を削除しますか？関連する所属も削除されます。`)) {
    return
  }
  try {
    await deleteInstitutionApi(institution.id)
    showSnackbar('機関を削除しました', 'success')
    if (selectedInstitution.value?.id === institution.id) {
      selectedInstitution.value = null
    }
    await loadInstitutions()
    await loadDepartments()
  } catch (error) {
    showSnackbar(error.response?.data?.detail || '削除に失敗しました', 'error')
  }
}

const deleteDepartment = async (department) => {
  if (!confirm(`所属「${department.name}」を削除しますか？`)) {
    return
  }
  try {
    await deleteDepartmentApi(department.id)
    showSnackbar('所属を削除しました', 'success')
    await loadDepartments()
  } catch (error) {
    showSnackbar(error.response?.data?.detail || '削除に失敗しました', 'error')
  }
}

const showSnackbar = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(async () => {
  try {
    const [userResponse, rolesResponse] = await Promise.all([
      getCurrentUser(),
      getRoles()
    ])
    currentUser.value = userResponse.data
    roles.value = rolesResponse.data
  } catch (error) {
    console.error('Failed to load user/roles:', error)
  }
  loadInstitutions()
  loadDepartments()
})
</script>
