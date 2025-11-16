import axios from 'axios'

// Create axios instance with default configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add auth token here if needed
    // const token = localStorage.getItem('authToken')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 400:
          console.error('Bad Request:', data.error || data.message || 'Invalid request')
          break
        case 401:
          console.error('Unauthorized:', data.error || 'Authentication required')
          // You can redirect to login page here
          break
        case 403:
          console.error('Forbidden:', data.error || 'Permission denied')
          break
        case 404:
          console.error('Not Found:', data.error || 'Resource not found')
          break
        case 500:
          console.error('Server Error:', data.error || 'Internal server error')
          break
        default:
          console.error('API Error:', data.error || data.message || 'Unknown error')
      }
    } else if (error.request) {
      console.error('Network Error:', 'No response received from server')
    } else {
      console.error('Request Error:', error.message)
    }

    return Promise.reject(error)
  }
)

// API methods for different endpoints
export const timetableAPI = {
  // Dashboard statistics
  getDashboardStats: () => api.get('/dashboard/'),

  // Timetable operations
  generateTimetable: (data) => api.post('/generate/', data),
  regenerateTimetable: (sessionId, data) => api.post(`/timetable/${sessionId}/regenerate/`, data),
  getTimetableGrid: (sessionId) => api.get('/grid/', { params: { session_id: sessionId } }),
  validateConstraints: (sessionId) => api.post('/validate/', { session_id: sessionId }),

  // Timetable sessions
  getTimetables: (params) => api.get('/timetable/', { params }),
  getTimetable: (id) => api.get(`/timetable/${id}/`),
  getTimetableEntries: (id) => api.get(`/timetable/${id}/entries/`),
  deleteTimetable: (id) => api.delete(`/timetable/${id}/`),

  // Export operations
  exportPDF: (id) => api.get(`/timetable/${id}/export/pdf/`, { responseType: 'blob' }),
  exportCSV: (id) => api.get(`/timetable/${id}/export/csv/`, { responseType: 'blob' }),
}

export const subjectAPI = {
  getSubjects: (params) => api.get('/subjects/', { params }),
  getSubject: (id) => api.get(`/subjects/${id}/`),
  createSubject: (data) => api.post('/subjects/', data),
  updateSubject: (id, data) => api.put(`/subjects/${id}/`, data),
  deleteSubject: (id) => api.delete(`/subjects/${id}/`),
  bulkImport: (formData) => api.post('/subjects/bulk_import/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  }),
}

export const teacherAPI = {
  getTeachers: (params) => api.get('/teachers/', { params }),
  getTeacher: (id) => api.get(`/teachers/${id}/`),
  createTeacher: (data) => api.post('/teachers/', data),
  updateTeacher: (id, data) => api.put(`/teachers/${id}/`, data),
  deleteTeacher: (id) => api.delete(`/teachers/${id}/`),
}

export const branchAPI = {
  getBranches: (params) => api.get('/branches/', { params }),
  getBranch: (id) => api.get(`/branches/${id}/`),
  createBranch: (data) => api.post('/branches/', data),
  updateBranch: (id, data) => api.put(`/branches/${id}/`, data),
  deleteBranch: (id) => api.delete(`/branches/${id}/`),
}

export const semesterAPI = {
  getSemesters: (params) => api.get('/semesters/', { params }),
  getSemester: (id) => api.get(`/semesters/${id}/`),
  createSemester: (data) => api.post('/semesters/', data),
  updateSemester: (id, data) => api.put(`/semesters/${id}/`, data),
  deleteSemester: (id) => api.delete(`/semesters/${id}/`),
}

export const classroomAPI = {
  getClassrooms: (params) => api.get('/classrooms/', { params }),
  getClassroom: (id) => api.get(`/classrooms/${id}/`),
  createClassroom: (data) => api.post('/classrooms/', data),
  updateClassroom: (id, data) => api.put(`/classrooms/${id}/`, data),
  deleteClassroom: (id) => api.delete(`/classrooms/${id}/`),
}

export const constraintAPI = {
  getConfigs: (params) => api.get('/constraint-configs/', { params }),
  getConfig: (id) => api.get(`/constraint-configs/${id}/`),
  createConfig: (data) => api.post('/constraint-configs/', data),
  updateConfig: (id, data) => api.put(`/constraint-configs/${id}/`, data),
  deleteConfig: (id) => api.delete(`/constraint-configs/${id}/`),
}

// Utility functions
export const apiUtils = {
  // Handle file download
  downloadFile: (response, filename) => {
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  // Format API error messages
  formatError: (error) => {
    if (error.response?.data?.error) {
      return error.response.data.error
    } else if (error.response?.data?.message) {
      return error.response.data.message
    } else if (error.message) {
      return error.message
    } else {
      return 'An unexpected error occurred'
    }
  },

  // Create FormData for file uploads
  createFormData: (data, fileField = 'file') => {
    const formData = new FormData()
    Object.keys(data).forEach(key => {
      if (key === fileField && data[key] instanceof File) {
        formData.append(key, data[key])
      } else if (typeof data[key] === 'object') {
        formData.append(key, JSON.stringify(data[key]))
      } else {
        formData.append(key, data[key])
      }
    })
    return formData
  }
}

export default api