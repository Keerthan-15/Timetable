<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-h4 font-weight-bold mb-2">
        Dashboard
      </h1>
      <p class="text-h6 text-medium-emphasis">
        Welcome to the Academic Timetable Management System
      </p>
    </div>

    <!-- Statistics Cards -->
    <v-row class="mb-6">
      <v-col
        v-for="stat in overviewStats"
        :key="stat.title"
        cols="12"
        sm="6"
        md="4"
        lg="2"
      >
        <v-card class="stat-card custom-card">
          <v-card-text class="pa-4">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="stat-value">
                  {{ stat.value }}
                </div>
                <div class="stat-label">
                  {{ stat.title }}
                </div>
              </div>
              <v-icon
                :icon="stat.icon"
                :color="stat.color"
                class="stat-icon"
              />
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Timetable Statistics -->
    <v-row class="mb-6">
      <v-col cols="12" lg="8">
        <v-card class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-calendar-check" class="mr-2" />
            Timetable Generation Statistics
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-card
                  color="primary"
                  variant="elevated"
                  class="text-center"
                >
                  <v-card-text>
                    <div class="text-h2 font-weight-bold">
                      {{ timetableStats.total }}
                    </div>
                    <div class="text-body-2">
                      Total Timetables
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card
                  color="success"
                  variant="elevated"
                  class="text-center"
                >
                  <v-card-text>
                    <div class="text-h2 font-weight-bold">
                      {{ timetableStats.valid }}
                    </div>
                    <div class="text-body-2">
                      Valid Timetables
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card
                  color="warning"
                  variant="elevated"
                  class="text-center"
                >
                  <v-card-text>
                    <div class="text-h2 font-weight-bold">
                      {{ timetableStats.success_rate.toFixed(1) }}%
                    </div>
                    <div class="text-body-2">
                      Success Rate
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-chart-pie" class="mr-2" />
            Subject Distribution
          </v-card-title>
          <v-card-text>
            <div v-if="subjectDistribution.length > 0">
              <div
                v-for="subject in subjectDistribution"
                :key="subject.subject_type"
                class="d-flex align-center justify-space-between mb-3"
              >
                <div class="d-flex align-center">
                  <v-chip
                    :color="getSubjectTypeColor(subject.subject_type)"
                    size="small"
                    class="mr-3"
                  >
                    {{ subject.count }}
                  </v-chip>
                  <span class="text-capitalize">
                    {{ subject.subject_type.replace('_', ' ') }}
                  </span>
                </div>
                <v-progress-linear
                  :model-value="(subject.count / totalSubjects) * 100"
                  :color="getSubjectTypeColor(subject.subject_type)"
                  height="6"
                  rounded
                  style="width: 100px"
                />
              </div>
            </div>
            <div v-else class="text-center pa-4">
              <v-icon icon="mdi-information" size="48" color="grey-lighten-1" />
              <div class="text-grey-darken-1 mt-2">
                No subject data available
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-flash" class="mr-2" />
            Quick Actions
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  color="primary"
                  size="large"
                  block
                  class="btn-gradient"
                  prepend-icon="mdi-calendar-plus"
                  @click="$router.push('/timetable/generate')"
                >
                  Generate Timetable
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  color="success"
                  size="large"
                  block
                  variant="elevated"
                  prepend-icon="mdi-view-list"
                  @click="$router.push('/timetable')"
                >
                  View Timetables
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  color="info"
                  size="large"
                  block
                  variant="elevated"
                  prepend-icon="mdi-book-open-variant"
                  @click="$router.push('/subjects')"
                >
                  Manage Subjects
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-btn
                  color="warning"
                  size="large"
                  block
                  variant="elevated"
                  prepend-icon="mdi-file-chart"
                  @click="$router.push('/reports')"
                >
                  Generate Reports
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Timetables and Activity -->
    <v-row>
      <v-col cols="12" lg="8">
        <v-card class="custom-card">
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon icon="mdi-history" class="mr-2" />
              Recent Timetables
            </div>
            <v-btn
              variant="text"
              prepend-icon="mdi-eye"
              @click="$router.push('/timetable')"
            >
              View All
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-list v-if="recentTimetables.length > 0">
              <v-list-item
                v-for="timetable in recentTimetables"
                :key="timetable.id"
                class="mb-2"
              >
                <template #prepend>
                  <v-avatar
                    :color="timetable.is_valid ? 'success' : 'warning'"
                    size="40"
                  >
                    <v-icon :icon="timetable.is_valid ? 'mdi-check' : 'mdi-alert'" />
                  </v-avatar>
                </template>

                <v-list-item-title class="font-weight-medium">
                  {{ timetable.branch_name }} - {{ timetable.semester_name }} (Section {{ timetable.section }})
                </v-list-item-title>

                <v-list-item-subtitle>
                  {{ formatDate(timetable.generated_at) }}
                  <span
                    :class="getComplianceClass(timetable)"
                    class="ml-2"
                  >
                    {{ getComplianceText(timetable) }}
                  </span>
                </v-list-item-subtitle>

                <template #append>
                  <v-btn-group variant="outlined" density="compact">
                    <v-btn
                      size="small"
                      prepend-icon="mdi-eye"
                      @click="viewTimetable(timetable.id)"
                    >
                      View
                    </v-btn>
                    <v-btn
                      v-if="timetable.is_valid"
                      size="small"
                      prepend-icon="mdi-download"
                      @click="exportTimetable(timetable.id)"
                    >
                      Export
                    </v-btn>
                  </v-btn-group>
                </template>
              </v-list-item>
            </v-list>

            <div v-else class="empty-state">
              <v-icon icon="mdi-calendar-blank" class="empty-icon" />
              <div class="empty-title">
                No timetables generated yet
              </div>
              <div class="empty-description">
                Generate your first timetable to get started
              </div>
              <v-btn
                color="primary"
                prepend-icon="mdi-calendar-plus"
                @click="$router.push('/timetable/generate')"
              >
                Generate Timetable
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-door-sliding" class="mr-2" />
            Room Utilization
          </v-card-title>
          <v-card-text>
            <div v-if="roomDistribution.length > 0">
              <div
                v-for="room in roomDistribution"
                :key="room.room_type"
                class="d-flex align-center justify-space-between mb-3"
              >
                <div class="d-flex align-center">
                  <v-chip
                    :color="getRoomTypeColor(room.room_type)"
                    size="small"
                    class="mr-3"
                  >
                    {{ room.count }}
                  </v-chip>
                  <span class="text-capitalize">
                    {{ room.room_type.replace('_', ' ') }}s
                  </span>
                </div>
                <v-progress-linear
                  :model-value="(room.count / totalRooms) * 100"
                  :color="getRoomTypeColor(room.room_type)"
                  height="6"
                  rounded
                  style="width: 100px"
                />
              </div>
            </div>
            <div v-else class="text-center pa-4">
              <v-icon icon="mdi-door-closed" size="48" color="grey-lighten-1" />
              <div class="text-grey-darken-1 mt-2">
                No room data available
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { timetableAPI, apiUtils } from '@/services/api'
import { format } from 'date-fns'

const router = useRouter()
const appStore = useAppStore()

// Reactive state
const loading = ref(false)
const dashboardData = ref({
  overview: {
    total_branches: 0,
    total_semesters: 0,
    total_subjects: 0,
    total_teachers: 0,
    total_rooms: 0
  },
  timetables: {
    total: 0,
    valid: 0,
    pending: 0,
    success_rate: 0
  },
  recent_timetables: [],
  subject_distribution: [],
  room_distribution: []
})

// Computed properties
const overviewStats = computed(() => [
  {
    title: 'Branches',
    value: dashboardData.value.overview.total_branches,
    icon: 'mdi-account-group',
    color: 'primary'
  },
  {
    title: 'Semesters',
    value: dashboardData.value.overview.total_semesters,
    icon: 'mdi-calendar-blank',
    color: 'secondary'
  },
  {
    title: 'Subjects',
    value: dashboardData.value.overview.total_subjects,
    icon: 'mdi-book-open-variant',
    color: 'info'
  },
  {
    title: 'Teachers',
    value: dashboardData.value.overview.total_teachers,
    icon: 'mdi-account-tie',
    color: 'success'
  },
  {
    title: 'Classrooms',
    value: dashboardData.value.overview.total_rooms,
    icon: 'mdi-door-sliding',
    color: 'warning'
  }
])

const timetableStats = computed(() => dashboardData.value.timetables)

const recentTimetables = computed(() => dashboardData.value.recent_timetables)

const subjectDistribution = computed(() => dashboardData.value.subject_distribution)

const roomDistribution = computed(() => dashboardData.value.room_distribution)

const totalSubjects = computed(() =>
  subjectDistribution.value.reduce((sum, item) => sum + item.count, 0)
)

const totalRooms = computed(() =>
  roomDistribution.value.reduce((sum, item) => sum + item.count, 0)
)

// Methods
const loadDashboardData = async () => {
  try {
    loading.value = true
    appStore.setGlobalLoading(true, 'Loading dashboard data...')

    const response = await timetableAPI.getDashboardStats()
    dashboardData.value = response.data
  } catch (error) {
    console.error('Error loading dashboard data:', error)
    appStore.showError('Failed to load dashboard data')
  } finally {
    loading.value = false
    appStore.setGlobalLoading(false)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
  } catch {
    return dateString
  }
}

const getSubjectTypeColor = (type) => {
  const colors = {
    theory: 'success',
    lab: 'warning',
    activity: 'info',
    mini_project: 'purple',
    tutorial: 'pink',
    remedial: 'deep-orange',
    proctor: 'cyan'
  }
  return colors[type] || 'grey'
}

const getRoomTypeColor = (type) => {
  const colors = {
    theory: 'blue',
    lab: 'green',
    activity: 'orange'
  }
  return colors[type] || 'grey'
}

const getComplianceClass = (timetable) => {
  const compliance = timetable.constraint_compliance
  if (!compliance || !compliance.is_compliant) {
    return 'text-error'
  } else if (compliance.compliance_percentage === 100) {
    return 'text-success'
  } else {
    return 'text-warning'
  }
}

const getComplianceText = (timetable) => {
  const compliance = timetable.constraint_compliance
  if (!compliance) {
    return 'Not validated'
  } else if (compliance.is_compliant) {
    return `${compliance.compliance_percentage}% Compliant`
  } else {
    return 'Non-compliant'
  }
}

const viewTimetable = (timetableId) => {
  router.push({
    name: 'Timetable',
    query: { session_id: timetableId }
  })
}

const exportTimetable = async (timetableId) => {
  try {
    appStore.setGlobalLoading(true, 'Generating PDF export...')

    const response = await timetableAPI.exportPDF(timetableId)
    const timetable = recentTimetables.value.find(t => t.id === timetableId)
    const filename = timetable
      ? `timetable_${timetable.branch_code}_${timetable.semester}_${timetable.section}.pdf`
      : `timetable_${timetableId}.pdf`

    apiUtils.downloadFile(response, filename)
    appStore.showSuccess('PDF exported successfully')
  } catch (error) {
    console.error('Error exporting PDF:', error)
    appStore.showError('Failed to export PDF')
  } finally {
    appStore.setGlobalLoading(false)
  }
}

// Lifecycle
onMounted(() => {
  loadDashboardData()
})
</script>

<style lang="scss" scoped>
.stat-card {
  border-radius: 16px !important;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--primary-gradient);
  }

  .stat-icon {
    position: absolute;
    top: 16px;
    right: 16px;
    opacity: 0.1;
    font-size: 3rem !important;
  }
}
</style>