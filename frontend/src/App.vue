<template>
  <v-app>
    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail"
      permanent
      class="elevation-2"
    >
      <v-list-item
        :title="appTitle"
        nav
        class="pa-4 primary text-white"
      >
        <template #prepend>
          <v-avatar
            color="white"
            class="primary--text"
            size="32"
          >
            <v-icon icon="mdi-calendar-clock" />
          </v-avatar>
        </template>
      </v-list-item>

      <v-divider />

      <v-list
        density="compact"
        nav
      >
        <v-list-item
          v-for="item in navigationItems"
          :key="item.title"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          exact
        />
      </v-list>

      <template #append>
        <v-list-item
          :prepend-icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
          @click="rail = !rail"
        />
      </template>
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar
      color="primary"
      prominent
      elevation="2"
    >
      <template #prepend>
        <v-app-bar-nav-icon
          v-if="$vuetify.display.mdAndDown"
          @click="drawer = !drawer"
        />
      </template>

      <v-app-bar-title>{{ appTitle }}</v-app-bar-title>

      <v-spacer />

      <v-btn icon @click="toggleTheme">
        <v-icon :icon="isDark ? 'mdi-brightness-7' : 'mdi-brightness-4'" />
      </v-btn>

      <v-menu offset-y>
        <template #activator="{ props }">
          <v-btn
            icon
            v-bind="props"
          >
            <v-avatar
              size="32"
              color="primary-lighten-1"
            >
              <v-icon icon="mdi-account" />
            </v-avatar>
          </v-btn>
        </template>

        <v-list>
          <v-list-item prepend-icon="mdi-account-circle" title="Profile" />
          <v-list-item prepend-icon="mdi-cog" title="Settings" />
          <v-divider />
          <v-list-item prepend-icon="mdi-logout" title="Logout" />
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Main Content -->
    <v-main>
      <v-container
        fluid
        class="pa-4"
      >
        <router-view v-slot="{ Component, route }">
          <transition
            name="page"
            mode="out-in"
          >
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </v-container>
    </v-main>

    <!-- Footer -->
    <v-footer
      color="primary"
      app
      class="text-center"
    >
      <span class="text-white">
        © {{ new Date().getFullYear() }} Academic Timetable Management System. All rights reserved.
      </span>
    </v-footer>

    <!-- Global Loading Overlay -->
    <v-overlay
      v-model="globalLoading"
      class="align-center justify-center"
      contained
      persistent
    >
      <v-card
        color="white"
        class="pa-6 text-center"
        elevation="8"
      >
        <v-progress-circular
          indeterminate
          color="primary"
          size="48"
          class="mb-4"
        />
        <div class="text-h6">
          {{ loadingMessage }}
        </div>
      </v-card>
    </v-overlay>

    <!-- Global Notification SnackBar -->
    <v-snackbar
      v-model="notification.show"
      :color="notification.type"
      :timeout="notification.timeout"
      location="top right"
    >
      <div class="d-flex align-center">
        <v-icon
          :icon="getNotificationIcon(notification.type)"
          class="mr-2"
        />
        {{ notification.message }}
      </div>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const theme = useTheme()

// Reactive state
const drawer = ref(true)
const rail = ref(false)

// Computed properties
const appTitle = computed(() => 'Timetable Manager')
const isDark = computed(() => theme.global.name.value === 'dark')
const globalLoading = computed(() => appStore.globalLoading)
const loadingMessage = computed(() => appStore.loadingMessage)
const notification = computed(() => appStore.notification)

// Navigation items
const navigationItems = ref([
  {
    title: 'Dashboard',
    icon: 'mdi-view-dashboard',
    to: '/'
  },
  {
    title: 'Timetable',
    icon: 'mdi-calendar-week',
    to: '/timetable'
  },
  {
    title: 'Subjects',
    icon: 'mdi-book-open-variant',
    to: '/subjects'
  },
  {
    title: 'Teachers',
    icon: 'mdi-account-tie',
    to: '/teachers'
  },
  {
    title: 'Classrooms',
    icon: 'mdi-door-sliding',
    to: '/classrooms'
  },
  {
    title: 'Reports',
    icon: 'mdi-file-chart',
    to: '/reports'
  },
  {
    title: 'Settings',
    icon: 'mdi-cog',
    to: '/settings'
  }
])

// Methods
const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

const getNotificationIcon = (type) => {
  const icons = {
    success: 'mdi-check-circle',
    error: 'mdi-alert-circle',
    warning: 'mdi-alert',
    info: 'mdi-information'
  }
  return icons[type] || 'mdi-information'
}
</script>

<style lang="scss" scoped>
.v-navigation-drawer {
  .v-list-item--active {
    background-color: rgba(25, 118, 210, 0.12);
    color: rgb(25, 118, 210);
  }
}

// Page transitions
.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
}
</style>