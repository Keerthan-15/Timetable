import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const globalLoading = ref(false)
  const loadingMessage = ref('Loading...')
  const notification = ref({
    show: false,
    message: '',
    type: 'info',
    timeout: 3000
  })

  // Actions
  const setGlobalLoading = (show, message = 'Loading...') => {
    globalLoading.value = show
    loadingMessage.value = message
  }

  const showNotification = (message, type = 'info', timeout = 3000) => {
    notification.value = {
      show: true,
      message,
      type,
      timeout
    }
  }

  const hideNotification = () => {
    notification.value.show = false
  }

  const showSuccess = (message, timeout = 3000) => {
    showNotification(message, 'success', timeout)
  }

  const showError = (message, timeout = 5000) => {
    showNotification(message, 'error', timeout)
  }

  const showWarning = (message, timeout = 4000) => {
    showNotification(message, 'warning', timeout)
  }

  const showInfo = (message, timeout = 3000) => {
    showNotification(message, 'info', timeout)
  }

  return {
    // State
    globalLoading,
    loadingMessage,
    notification,
    // Actions
    setGlobalLoading,
    showNotification,
    hideNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo
  }
})