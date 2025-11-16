<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <v-btn
        variant="text"
        prepend-icon="mdi-arrow-left"
        @click="$router.go(-1)"
        class="mb-4"
      >
        Back
      </v-btn>

      <h1 class="text-h4 font-weight-bold mb-2">
        Generate Timetable
      </h1>
      <p class="text-h6 text-medium-emphasis">
        Create a professional academic timetable with constraint validation
      </p>
    </div>

    <v-row>
      <!-- Configuration Form -->
      <v-col cols="12" lg="4">
        <v-card class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-cog" class="mr-2" />
            Timetable Configuration
          </v-card-title>
          <v-card-text>
            <v-form ref="formRef" v-model="validForm">
              <!-- Branch Selection -->
              <v-select
                v-model="timetableConfig.branch_id"
                :items="branches"
                item-title="name"
                item-value="id"
                label="Branch"
                placeholder="Select branch"
                :rules="[v => !!v || 'Branch is required']"
                required
                class="mb-4"
                variant="outlined"
                density="comfortable"
              />

              <!-- Semester Selection -->
              <v-select
                v-model="timetableConfig.semester_id"
                :items="semesters"
                item-title="display_name"
                item-value="id"
                label="Semester"
                placeholder="Select semester"
                :rules="[v => !!v || 'Semester is required']"
                required
                class="mb-4"
                variant="outlined"
                density="comfortable"
                :loading="loadingSemesters"
              />

              <!-- Section -->
              <v-text-field
                v-model="timetableConfig.section"
                label="Section"
                placeholder="e.g., A, B, C"
                :rules="[v => !!v || 'Section is required']"
                required
                class="mb-4"
                variant="outlined"
                density="comfortable"
                maxlength="2"
              />

              <!-- Academic Year -->
              <v-text-field
                v-model="timetableConfig.academic_year"
                label="Academic Year"
                placeholder="e.g., 2024-25"
                :rules="[v => !!v || 'Academic year is required']"
                required
                class="mb-4"
                variant="outlined"
                density="comfortable"
                pattern="[0-9]{4}-[0-9]{2}"
              />

              <!-- Constraint Configuration -->
              <v-divider class="my-4" />
              <div class="text-h6 mb-3">Constraint Configuration</div>

              <v-checkbox
                v-for="constraint in constraintOptions"
                :key="constraint.key"
                v-model="timetableConfig.constraint_config[constraint.key]"
                :label="constraint.label"
                :messages="constraint.description"
                class="mb-2"
                density="compact"
                hide-details="auto"
              />

              <!-- Constraint Priority -->
              <v-select
                v-model="timetableConfig.constraint_config.priority_mode"
                :items="priorityModes"
                item-title="label"
                item-value="value"
                label="Constraint Priority Mode"
                class="mb-4"
                variant="outlined"
                density="comfortable"
                messages="How to prioritize constraints during generation"
              />
            </v-form>

            <!-- Action Buttons -->
            <div class="d-flex gap-3 mt-6">
              <v-btn
                color="primary"
                size="large"
                class="btn-gradient flex-grow-1"
                :loading="generating"
                :disabled="!validForm || generating"
                @click="generateTimetable"
              >
                <v-icon icon="mdi-calendar-plus" class="mr-2" />
                Generate Timetable
              </v-btn>

              <v-btn
                color="secondary"
                variant="outlined"
                size="large"
                :disabled="generating"
                @click="resetForm"
              >
                <v-icon icon="mdi-refresh" class="mr-2" />
                Reset
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Constraint Summary Card -->
        <v-card class="custom-card mt-4" v-if="timetableConfig.branch_id">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-information" class="mr-2" />
            Constraint Summary
          </v-card-title>
          <v-card-text>
            <div class="text-body-2 mb-3">
              <strong>{{ enabledConstraintsCount }}</strong> of {{ constraintOptions.length }} constraints enabled
            </div>
            <v-chip
              v-for="constraint in constraintOptions"
              :key="constraint.key"
              :color="timetableConfig.constraint_config[constraint.key] ? 'success' : 'grey'"
              size="small"
              class="ma-1"
            >
              {{ constraint.label }}
            </v-chip>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Generation Results -->
      <v-col cols="12" lg="8">
        <!-- Generation Progress -->
        <v-card v-if="generating" class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-progress-clock" class="mr-2" />
            Generating Timetable...
          </v-card-title>
          <v-card-text>
            <div class="text-center pa-6">
              <v-progress-circular
                indeterminate
                color="primary"
                size="64"
                class="mb-4"
              />
              <div class="text-h6 mb-2">
                {{ generationStatus.message }}
              </div>
              <div class="text-body-2 text-medium-emphasis">
                {{ generationStatus.description }}
              </div>
              <v-progress-linear
                v-model="generationProgress"
                color="primary"
                height="6"
                rounded
                class="mt-4"
              />
            </div>
          </v-card-text>
        </v-card>

        <!-- Generation Results -->
        <v-card v-else-if="generationResult" class="custom-card">
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon
                :icon="generationResult.success ? 'mdi-check-circle' : 'mdi-alert-circle'"
                :color="generationResult.success ? 'success' : 'error'"
                class="mr-2"
              />
              Generation Result
            </div>
            <v-btn
              v-if="generationResult.success"
              color="primary"
              prepend-icon="mdi-eye"
              @click="viewGeneratedTimetable"
            >
              View Timetable
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-alert
              :type="generationResult.success ? 'success' : 'error'"
              :title="generationResult.success ? 'Success!' : 'Generation Failed'"
              class="mb-4"
            >
              {{ generationResult.message }}
            </v-alert>

            <div v-if="generationResult.success">
              <!-- Statistics -->
              <v-row class="mb-4">
                <v-col cols="12" sm="6" md="3">
                  <v-card color="primary" variant="elevated" class="text-center">
                    <v-card-text>
                      <div class="text-h2 font-weight-bold">
                        {{ generationResult.entries }}
                      </div>
                      <div class="text-body-2">
                        Total Entries
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-card color="success" variant="elevated" class="text-center">
                    <v-card-text>
                      <div class="text-h2 font-weight-bold">
                        {{ generationResult.constraint_compliance.satisfied }}
                      </div>
                      <div class="text-body-2">
                        Constraints Satisfied
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-card color="warning" variant="elevated" class="text-center">
                    <v-card-text>
                      <div class="text-h2 font-weight-bold">
                        {{ generationResult.constraint_compliance.compliance_percentage }}%
                      </div>
                      <div class="text-body-2">
                        Compliance Rate
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-card color="info" variant="elevated" class="text-center">
                    <v-card-text>
                      <div class="text-h2 font-weight-bold">
                        {{ generationResult.statistics.total_hours }}
                      </div>
                      <div class="text-body-2">
                        Total Hours
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Constraint Violations -->
              <div v-if="generationResult.constraint_compliance.violations.length > 0">
                <v-alert type="warning" class="mb-3">
                  <v-alert-title>Constraint Violations</v-alert-title>
                  <ul>
                    <li v-for="violation in generationResult.constraint_compliance.violations" :key="violation.constraint">
                      {{ violation.message }}
                    </li>
                  </ul>
                </v-alert>
              </div>

              <!-- Action Buttons -->
              <div class="d-flex gap-3">
                <v-btn
                  color="primary"
                  prepend-icon="mdi-eye"
                  @click="viewGeneratedTimetable"
                >
                  View Timetable
                </v-btn>
                <v-btn
                  color="success"
                  prepend-icon="mdi-download"
                  @click="exportGeneratedTimetable"
                >
                  Export PDF
                </v-btn>
                <v-btn
                  color="info"
                  prepend-icon="mdi-refresh"
                  @click="regenerateTimetable"
                >
                  Regenerate
                </v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Constraint Information -->
        <v-card v-else class="custom-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-information-outline" class="mr-2" />
            Constraint Information
          </v-card-title>
          <v-card-text>
            <div class="text-body-1 mb-4">
              The timetable generator enforces the following constraints to create professional schedules:
            </div>

            <v-expansion-panels variant="accordion">
              <v-expansion-panel
                v-for="(constraint, index) in constraintOptions"
                :key="constraint.key"
              >
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-checkbox
                      :model-value="timetableConfig.constraint_config[constraint.key]"
                      @update:model-value="(value) => timetableConfig.constraint_config[constraint.key] = value"
                      density="compact"
                      hide-details
                      class="mr-3"
                      @click.stop
                    />
                    {{ constraint.label }}
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div class="text-body-2">
                    {{ constraint.description }}
                  </div>
                  <div class="mt-2">
                    <v-chip
                      :color="constraint.priority === 'high' ? 'error' : constraint.priority === 'medium' ? 'warning' : 'info'"
                      size="small"
                    >
                      {{ constraint.priority.toUpperCase() }} PRIORITY
                    </v-chip>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { timetableAPI, branchAPI, semesterAPI, apiUtils } from '@/services/api'

const router = useRouter()
const appStore = useAppStore()

// Reactive state
const validForm = ref(false)
const loadingSemesters = ref(false)
const generating = ref(false)
const generationProgress = ref(0)
const generationResult = ref(null)

const branches = ref([])
const semesters = ref([])

const timetableConfig = ref({
  branch_id: null,
  semester_id: null,
  section: 'A',
  academic_year: '2024-25',
  constraint_config: {
    priority_first_period: true,
    lab_continuous_blocks: true,
    one_lab_per_day: true,
    tutorial_last_period: true,
    saturday_activities: true,
    exact_credit_hours: true,
    priority_mode: 'balanced'
  }
})

const generationStatus = ref({
  message: 'Initializing...',
  description: 'Preparing timetable generation...'
})

// Constraint options with detailed descriptions
const constraintOptions = ref([
  {
    key: 'priority_first_period',
    label: 'First Period Priority',
    description: 'High-credit subjects (3+ credits) get first period allocation on weekdays (Monday-Friday)',
    priority: 'high'
  },
  {
    key: 'lab_continuous_blocks',
    label: 'Continuous Lab Blocks',
    description: 'Lab classes must be scheduled in 2-hour continuous blocks (periods 2-3, 4-5, or 6-7)',
    priority: 'high'
  },
  {
    key: 'one_lab_per_day',
    label: 'One Lab Per Day',
    description: 'Maximum one laboratory subject per day to prevent scheduling conflicts',
    priority: 'high'
  },
  {
    key: 'tutorial_last_period',
    label: 'Tutorial in Last Period',
    description: 'Tutorial, remedial, and proctor classes must be scheduled in the last period of the day',
    priority: 'medium'
  },
  {
    key: 'saturday_activities',
    label: 'Saturday Activities',
    description: 'Schedule NSS/Sports/Yoga activities in 2-hour blocks after break on Saturday',
    priority: 'medium'
  },
  {
    key: 'exact_credit_hours',
    label: 'Exact Credit Hours',
    description: 'Allocate exact number of hours per week based on subject credits and requirements',
    priority: 'high'
  }
])

const priorityModes = ref([
  { value: 'balanced', label: 'Balanced (Default)' },
  { value: 'strict', label: 'Strict Constraint Enforcement' },
  { value: 'flexible', label: 'Flexible Constraint Handling' }
])

// Computed properties
const enabledConstraintsCount = computed(() => {
  return Object.values(timetableConfig.value.constraint_config)
    .filter(value => typeof value === 'boolean' && value)
    .length
})

// Methods
const loadBranches = async () => {
  try {
    const response = await branchAPI.getBranches()
    branches.value = response.data.results || response.data
  } catch (error) {
    console.error('Error loading branches:', error)
    appStore.showError('Failed to load branches')
  }
}

const loadSemesters = async () => {
  if (!timetableConfig.value.branch_id) {
    semesters.value = []
    return
  }

  try {
    loadingSemesters.value = true
    const response = await semesterAPI.getSemesters()
    const allSemesters = response.data.results || response.data

    // Create display name for semesters
    semesters.value = allSemesters.map(semester => ({
      ...semester,
      display_name: `${semester.academic_year} ${semester.semester_type} Semester ${semester.number}`
    }))
  } catch (error) {
    console.error('Error loading semesters:', error)
    appStore.showError('Failed to load semesters')
  } finally {
    loadingSemesters.value = false
  }
}

const generateTimetable = async () => {
  if (!validForm.value) return

  try {
    generating.value = true
    generationProgress.value = 0
    generationResult.value = null

    // Update status messages
    updateGenerationStatus('Validating configuration...', 'Checking timetable parameters...')
    generationProgress.value = 10

    await new Promise(resolve => setTimeout(resolve, 500))

    updateGenerationStatus('Preparing data...', 'Loading subjects, teachers, and rooms...')
    generationProgress.value = 20

    await new Promise(resolve => setTimeout(resolve, 1000))

    updateGenerationStatus('Analyzing constraints...', 'Evaluating scheduling constraints...')
    generationProgress.value = 30

    await new Promise(resolve => setTimeout(resolve, 800))

    updateGenerationStatus('Generating timetable...', 'Creating optimal schedule using backtracking algorithm...')
    generationProgress.value = 50

    // Make API call
    const response = await timetableAPI.generateTimetable(timetableConfig.value)

    updateGenerationStatus('Validating results...', 'Checking constraint compliance...')
    generationProgress.value = 80

    await new Promise(resolve => setTimeout(resolve, 500))

    updateGenerationStatus('Finalizing...', 'Completing timetable generation...')
    generationProgress.value = 90

    await new Promise(resolve => setTimeout(resolve, 300))

    generationProgress.value = 100
    updateGenerationStatus('Complete!', 'Timetable generated successfully')

    // Store result
    generationResult.value = response.data

    // Show success message
    appStore.showSuccess('Timetable generated successfully!')

  } catch (error) {
    console.error('Error generating timetable:', error)
    const errorMessage = apiUtils.formatError(error)

    generationResult.value = {
      success: false,
      message: errorMessage
    }

    appStore.showError(`Failed to generate timetable: ${errorMessage}`)
  } finally {
    generating.value = false
  }
}

const updateGenerationStatus = (message, description) => {
  generationStatus.value = { message, description }
}

const resetForm = () => {
  timetableConfig.value = {
    branch_id: null,
    semester_id: null,
    section: 'A',
    academic_year: '2024-25',
    constraint_config: {
      priority_first_period: true,
      lab_continuous_blocks: true,
      one_lab_per_day: true,
      tutorial_last_period: true,
      saturday_activities: true,
      exact_credit_hours: true,
      priority_mode: 'balanced'
    }
  }
  generationResult.value = null
}

const viewGeneratedTimetable = () => {
  if (generationResult.value?.session_id) {
    router.push({
      name: 'Timetable',
      query: { session_id: generationResult.value.session_id }
    })
  }
}

const exportGeneratedTimetable = async () => {
  if (!generationResult.value?.session_id) return

  try {
    appStore.setGlobalLoading(true, 'Generating PDF export...')

    const response = await timetableAPI.exportPDF(generationResult.value.session_id)
    const filename = `timetable_${new Date().toISOString().split('T')[0]}.pdf`

    apiUtils.downloadFile(response, filename)
    appStore.showSuccess('PDF exported successfully')
  } catch (error) {
    console.error('Error exporting PDF:', error)
    appStore.showError('Failed to export PDF')
  } finally {
    appStore.setGlobalLoading(false)
  }
}

const regenerateTimetable = () => {
  if (generationResult.value?.session_id) {
    // Create a copy of the config and generate again
    const currentConfig = { ...timetableConfig.value }
    resetForm()
    timetableConfig.value = currentConfig
    generateTimetable()
  }
}

// Watchers
watch(() => timetableConfig.value.branch_id, () => {
  timetableConfig.value.semester_id = null
  loadSemesters()
})

// Lifecycle
onMounted(() => {
  loadBranches()
  loadSemesters()
})
</script>

<style lang="scss" scoped>
.v-expansion-panel-title {
  .v-checkbox {
    flex-shrink: 0;
  }
}
</style>