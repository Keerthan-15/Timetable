import { createRouter, createWebHistory } from 'vue-router'
import { useAppStore } from '@/stores/app'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: 'Dashboard',
      icon: 'mdi-view-dashboard'
    }
  },
  {
    path: '/timetable',
    name: 'Timetable',
    component: () => import('@/views/TimableView.vue'),
    meta: {
      title: 'Timetable',
      icon: 'mdi-calendar-week'
    }
  },
  {
    path: '/timetable/generate',
    name: 'GenerateTimetable',
    component: () => import('@/views/GenerateTimetable.vue'),
    meta: {
      title: 'Generate Timetable',
      icon: 'mdi-calendar-plus'
    }
  },
  {
    path: '/subjects',
    name: 'Subjects',
    component: () => import('@/views/Subjects.vue'),
    meta: {
      title: 'Subjects',
      icon: 'mdi-book-open-variant'
    }
  },
  {
    path: '/teachers',
    name: 'Teachers',
    component: () => import('@/views/Teachers.vue'),
    meta: {
      title: 'Teachers',
      icon: 'mdi-account-tie'
    }
  },
  {
    path: '/classrooms',
    name: 'Classrooms',
    component: () => import('@/views/Classrooms.vue'),
    meta: {
      title: 'Classrooms',
      icon: 'mdi-door-sliding'
    }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue'),
    meta: {
      title: 'Reports',
      icon: 'mdi-file-chart'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: {
      title: 'Settings',
      icon: 'mdi-cog'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: 'Page Not Found'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const appStore = useAppStore()

  // Set page title
  document.title = to.meta.title
    ? `${to.meta.title} - Timetable Manager`
    : 'Timetable Manager'

  // Start loading
  if (to.name !== from.name) {
    appStore.setGlobalLoading(true, 'Loading...')
  }

  next()
})

router.afterEach(() => {
  const appStore = useAppStore()
  // Stop loading
  setTimeout(() => {
    appStore.setGlobalLoading(false)
  }, 300)
})

export default router