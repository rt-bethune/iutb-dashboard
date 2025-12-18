import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401/403 errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear and redirect to login
      localStorage.removeItem('auth_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Helper to build department-scoped URLs
const withDept = (path: string, department: string) => `/${department}${path}`

// Scolarité
export const scolariteApi = {
  getIndicators: (department: string, annee?: string) => 
    api.get(withDept('/scolarite/indicators', department), { params: { annee } }).then(res => res.data),
  getEtudiants: (department: string, params?: { formation?: string; semestre?: string; limit?: number }) => 
    api.get(withDept('/scolarite/etudiants', department), { params }).then(res => res.data),
  getModules: (department: string, semestre?: string) => 
    api.get(withDept('/scolarite/modules', department), { params: { semestre } }).then(res => res.data),
  getEffectifs: (department: string) => 
    api.get(withDept('/scolarite/effectifs', department)).then(res => res.data),
  getReussite: (department: string) => 
    api.get(withDept('/scolarite/reussite', department)).then(res => res.data),
}

// Alertes étudiants
export const alertesApi = {
  getAlertes: (department: string, params?: { niveau?: string; type_alerte?: string; semestre?: string; limit?: number }) =>
    api.get(withDept('/alertes/', department), { params }).then(res => res.data),
  getStatistiques: (department: string, semestre?: string) =>
    api.get(withDept('/alertes/statistiques', department), { params: { semestre } }).then(res => res.data),
  getConfig: (department: string) =>
    api.get(withDept('/alertes/config', department)).then(res => res.data),
  updateConfig: (department: string, config: any) =>
    api.put(withDept('/alertes/config', department), config).then(res => res.data),
  getFicheEtudiant: (department: string, etudiantId: string) =>
    api.get(withDept(`/alertes/etudiant/${etudiantId}`, department)).then(res => res.data),
  getAbsencesEtudiant: (department: string, etudiantId: string, semestre?: string) =>
    api.get(withDept(`/alertes/etudiant/${etudiantId}/absences`, department), { params: { semestre } }).then(res => res.data),
  getProgressionEtudiant: (department: string, etudiantId: string) =>
    api.get(withDept(`/alertes/etudiant/${etudiantId}/progression`, department)).then(res => res.data),
  getRisqueEtudiant: (department: string, etudiantId: string) =>
    api.get(withDept(`/alertes/etudiant/${etudiantId}/risque`, department)).then(res => res.data),
  getEtudiantsEnDifficulte: (department: string, params?: { semestre?: string; seuil_moyenne?: number }) =>
    api.get(withDept('/alertes/etudiants-en-difficulte', department), { params }).then(res => res.data),
  getEtudiantsAbsents: (department: string, params?: { semestre?: string; seuil_absences?: number }) =>
    api.get(withDept('/alertes/etudiants-absents', department), { params }).then(res => res.data),
  getEtudiantsRisqueDecrochage: (department: string, params?: { semestre?: string; seuil_score?: number }) =>
    api.get(withDept('/alertes/etudiants-risque-decrochage', department), { params }).then(res => res.data),
  getFelicitations: (department: string, params?: { semestre?: string; top_percent?: number }) =>
    api.get(withDept('/alertes/felicitations', department), { params }).then(res => res.data),
}

// Indicateurs cohorte
export const indicateursApi = {
  getTableauBord: (department: string, params?: { annee?: string; semestre?: string }) =>
    api.get(withDept('/indicateurs/tableau-bord', department), { params }).then(res => res.data),
  getStatistiques: (department: string, params?: { semestre?: string; groupe?: string }) =>
    api.get(withDept('/indicateurs/statistiques', department), { params }).then(res => res.data),
  getTauxValidation: (department: string, semestre?: string) =>
    api.get(withDept('/indicateurs/taux-validation', department), { params: { semestre } }).then(res => res.data),
  getMentions: (department: string, semestre?: string) =>
    api.get(withDept('/indicateurs/mentions', department), { params: { semestre } }).then(res => res.data),
  getModules: (department: string, params?: { semestre?: string; tri?: string }) =>
    api.get(withDept('/indicateurs/modules', department), { params }).then(res => res.data),
  getModule: (department: string, codeModule: string, semestre?: string) =>
    api.get(withDept(`/indicateurs/modules/${codeModule}`, department), { params: { semestre } }).then(res => res.data),
  getAbsenteisme: (department: string, semestre?: string) =>
    api.get(withDept('/indicateurs/absenteisme', department), { params: { semestre } }).then(res => res.data),
  getTauxPassage: (department: string, annee?: string) =>
    api.get(withDept('/indicateurs/taux-passage', department), { params: { annee } }).then(res => res.data),
  getComparaisonInterannuelle: (department: string, nbAnnees?: number) =>
    api.get(withDept('/indicateurs/comparaison-interannuelle', department), { params: { nb_annees: nbAnnees } }).then(res => res.data),
  getAnalyseTypeBac: (department: string, semestre?: string) =>
    api.get(withDept('/indicateurs/analyse-type-bac', department), { params: { semestre } }).then(res => res.data),
  getAnalyseBoursiers: (department: string, semestre?: string) =>
    api.get(withDept('/indicateurs/analyse-boursiers', department), { params: { semestre } }).then(res => res.data),
  getPredictifs: (department: string, semestre?: string) =>
    api.get(withDept('/indicateurs/predictifs', department), { params: { semestre } }).then(res => res.data),
  getRapportSemestre: (department: string, annee: string, semestre: string) =>
    api.get(withDept('/indicateurs/rapport-semestre', department), { params: { annee, semestre } }).then(res => res.data),
}

// Recrutement
export const recrutementApi = {
  getIndicators: (department: string, annee?: number) => 
    api.get(withDept('/recrutement/indicators', department), { params: { annee } }).then(res => res.data),
  getEvolution: (department: string) => 
    api.get(withDept('/recrutement/evolution', department)).then(res => res.data),
  getParBac: (department: string, annee?: number) => 
    api.get(withDept('/recrutement/par-bac', department), { params: { annee } }).then(res => res.data),
  getParOrigine: (department: string, annee?: number) => 
    api.get(withDept('/recrutement/par-origine', department), { params: { annee } }).then(res => res.data),
  getTopLycees: (department: string, limit?: number) => 
    api.get(withDept('/recrutement/top-lycees', department), { params: { limit } }).then(res => res.data),
  importFile: (department: string, file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(withDept(`/recrutement/import?annee=${annee}`, department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
}

// Budget
export const budgetApi = {
  getIndicators: (department: string, annee?: number) => 
    api.get(withDept('/budget/indicators', department), { params: { annee } }).then(res => res.data),
  getParCategorie: (department: string, annee?: number) => 
    api.get(withDept('/budget/par-categorie', department), { params: { annee } }).then(res => res.data),
  getEvolution: (department: string, annee?: number) => 
    api.get(withDept('/budget/evolution', department), { params: { annee } }).then(res => res.data),
  getExecution: (department: string) => 
    api.get(withDept('/budget/execution', department)).then(res => res.data),
  getTopDepenses: (department: string, limit?: number) => 
    api.get(withDept('/budget/top-depenses', department), { params: { limit } }).then(res => res.data),
  importFile: (department: string, file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(withDept(`/budget/import?annee=${annee}`, department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
}

// EDT
export const edtApi = {
  getIndicators: (department: string, annee?: string) => 
    api.get(withDept('/edt/indicators', department), { params: { annee } }).then(res => res.data),
  getCharges: (department: string, enseignant?: string) => 
    api.get(withDept('/edt/charges', department), { params: { enseignant } }).then(res => res.data),
  getOccupation: (department: string, salle?: string) => 
    api.get(withDept('/edt/occupation', department), { params: { salle } }).then(res => res.data),
  getRepartition: (department: string) => 
    api.get(withDept('/edt/repartition', department)).then(res => res.data),
  getHeuresComplementaires: (department: string) => 
    api.get(withDept('/edt/heures-complementaires', department)).then(res => res.data),
  getParModule: (department: string) => 
    api.get(withDept('/edt/par-module', department)).then(res => res.data),
  importFile: (department: string, file: File, annee?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(withDept('/edt/import', department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { annee },
    }).then(res => res.data)
  },
}

// Upload (department-scoped)
export const uploadApi = {
  uploadFile: (department: string, file: File, type: string, description?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    if (description) formData.append('description', description)
    return api.post(withDept('/upload/file', department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  listFiles: (department: string, type?: string) =>
    api.get(withDept('/upload/files', department), { params: { type } }).then(res => res.data),
  deleteFile: (department: string, filename: string, type: string) =>
    api.delete(withDept(`/upload/file/${type}/${filename}`, department)).then(res => res.data),
  downloadFile: (department: string, filename: string, type: string) =>
    api.get(withDept(`/upload/download/${type}/${filename}`, department), { responseType: 'blob' }),
}

// Admin (global - not department-scoped)
export const adminApi = {
  // Dashboard
  getDashboard: () => api.get('/admin/dashboard').then(res => res.data),
  
  // Sources (read-only for now)
  getSources: (type?: string) => 
    api.get('/admin/sources', { params: { type } }).then(res => res.data),
  getSource: (id: string) => 
    api.get(`/admin/sources/${id}`).then(res => res.data),
  
  // Settings
  getSettings: () => api.get('/admin/settings').then(res => res.data),
  updateSettings: (data: any) => 
    api.put('/admin/settings', data).then(res => res.data),
  
  // Cache
  getCacheStats: () => api.get('/admin/cache/stats').then(res => res.data),
  clearCache: (domain?: string) => 
    api.post('/admin/cache/clear', null, { params: { domain } }).then(res => res.data),
  warmupCache: (department?: string) =>
    api.post('/admin/cache/warmup', null, { params: { department } }).then(res => res.data),
  
  // Jobs
  getJobs: () => api.get('/admin/jobs').then(res => res.data),
  runJob: (id: string) => 
    api.post(`/admin/jobs/${id}/run`).then(res => res.data),
}

// Admin Budget CRUD (department-scoped)
export const adminBudgetApi = {
  // Budget years
  getYears: (department: string) => 
    api.get(withDept('/admin/budget/years', department)).then(res => res.data),
  getYear: (department: string, annee: number) => 
    api.get(withDept(`/admin/budget/year/${annee}`, department)).then(res => res.data),
  createYear: (department: string, data: { annee: number; budget_total?: number; previsionnel?: number; lignes?: any[] }) =>
    api.post(withDept('/admin/budget/year', department), data).then(res => res.data),
  updateYear: (department: string, annee: number, data: { budget_total?: number; previsionnel?: number }) =>
    api.put(withDept(`/admin/budget/year/${annee}`, department), data).then(res => res.data),
  deleteYear: (department: string, annee: number) => 
    api.delete(withDept(`/admin/budget/year/${annee}`, department)).then(res => res.data),
  
  // Budget lines
  createLigne: (department: string, annee: number, data: { categorie: string; budget_initial: number; budget_modifie?: number; engage?: number; paye?: number }) =>
    api.post(withDept(`/admin/budget/year/${annee}/ligne`, department), data).then(res => res.data),
  updateLigne: (department: string, ligneId: number, data: { budget_initial?: number; budget_modifie?: number; engage?: number; paye?: number }) =>
    api.put(withDept(`/admin/budget/ligne/${ligneId}`, department), data).then(res => res.data),
  deleteLigne: (department: string, ligneId: number) => 
    api.delete(withDept(`/admin/budget/ligne/${ligneId}`, department)).then(res => res.data),
  
  // Depenses
  getDepenses: (department: string, annee: number, params?: { categorie?: string; statut?: string; limit?: number }) =>
    api.get(withDept(`/admin/budget/year/${annee}/depenses`, department), { params }).then(res => res.data),
  createDepense: (department: string, annee: number, data: { libelle: string; montant: number; categorie: string; date_depense: string; fournisseur?: string; numero_commande?: string; statut?: string }) =>
    api.post(withDept(`/admin/budget/year/${annee}/depense`, department), data).then(res => res.data),
  updateDepense: (department: string, depenseId: number, data: any) =>
    api.put(withDept(`/admin/budget/depense/${depenseId}`, department), data).then(res => res.data),
  deleteDepense: (department: string, depenseId: number) => 
    api.delete(withDept(`/admin/budget/depense/${depenseId}`, department)).then(res => res.data),
  
  // Import
  importFile: (department: string, file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(withDept(`/admin/budget/import?annee=${annee}`, department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  
  // Indicators (from DB)
  getIndicators: (department: string, annee?: number) =>
    api.get(withDept('/admin/budget/indicators', department), { params: { annee } }).then(res => res.data),
}

// Admin Recrutement CRUD (department-scoped)
export const adminRecrutementApi = {
  // Campagnes
  getCampagnes: (department: string) => 
    api.get(withDept('/admin/recrutement/campagnes', department)).then(res => res.data),
  getCampagne: (department: string, annee: number) => 
    api.get(withDept(`/admin/recrutement/campagne/${annee}`, department)).then(res => res.data),
  createCampagne: (department: string, data: { annee: number; nb_places?: number; date_debut?: string; date_fin?: string }) =>
    api.post(withDept('/admin/recrutement/campagne', department), data).then(res => res.data),
  updateCampagne: (department: string, annee: number, data: { nb_places?: number; date_debut?: string; date_fin?: string; rang_dernier_appele?: number }) =>
    api.put(withDept(`/admin/recrutement/campagne/${annee}`, department), data).then(res => res.data),
  deleteCampagne: (department: string, annee: number) => 
    api.delete(withDept(`/admin/recrutement/campagne/${annee}`, department)).then(res => res.data),
  
  // Candidats
  getCandidats: (department: string, annee: number, params?: { statut?: string; type_bac?: string; limit?: number }) =>
    api.get(withDept(`/admin/recrutement/campagne/${annee}/candidats`, department), { params }).then(res => res.data),
  getCandidat: (department: string, id: number) => 
    api.get(withDept(`/admin/recrutement/candidat/${id}`, department)).then(res => res.data),
  createCandidat: (department: string, annee: number, data: { type_bac: string; mention_bac?: string; departement_origine?: string; lycee?: string; statut?: string }) =>
    api.post(withDept(`/admin/recrutement/campagne/${annee}/candidat`, department), data).then(res => res.data),
  createCandidatsBulk: (department: string, annee: number, candidats: any[]) =>
    api.post(withDept(`/admin/recrutement/campagne/${annee}/candidats/bulk`, department), { candidats }).then(res => res.data),
  updateCandidat: (department: string, id: number, data: any) =>
    api.put(withDept(`/admin/recrutement/candidat/${id}`, department), data).then(res => res.data),
  deleteCandidat: (department: string, id: number) => 
    api.delete(withDept(`/admin/recrutement/candidat/${id}`, department)).then(res => res.data),
  
  // Import
  importCsv: (department: string, file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(withDept(`/admin/recrutement/import/csv?annee=${annee}`, department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  importExcel: (department: string, file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(withDept(`/admin/recrutement/import/excel?annee=${annee}`, department), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  
  // Stats & Indicators
  getStats: (department: string, annee: number) => 
    api.get(withDept(`/admin/recrutement/stats/${annee}`, department)).then(res => res.data),
  saveStats: (department: string, annee: number, data: {
    nb_voeux: number;
    nb_acceptes: number;
    nb_confirmes: number;
    nb_refuses?: number;
    nb_desistes?: number;
    par_type_bac?: Record<string, number>;
    par_mention?: Record<string, number>;
    par_origine?: Record<string, number>;
    par_lycees?: Record<string, number>;
  }) => api.post(withDept(`/admin/recrutement/stats/${annee}`, department), data).then(res => res.data),
  getEvolution: (department: string, limit?: number) => 
    api.get(withDept('/admin/recrutement/evolution', department), { params: { limit } }).then(res => res.data),
  getIndicators: (department: string, annee?: number) =>
    api.get(withDept('/admin/recrutement/indicators', department), { params: { annee } }).then(res => res.data),
}

// Departments endpoint (global)
export const departmentsApi = {
  getAll: () => api.get('/departments').then(res => res.data),
}

// Auth API
export const authApi = {
  devLogin: (username: string) => 
    api.post(`/auth/dev/login?username=${encodeURIComponent(username)}`).then(res => res.data),
  me: (token: string) => 
    api.get('/auth/me', { params: { token } }).then(res => res.data),
  validateToken: (token: string) =>
    api.post('/auth/validate-token', null, { params: { token } }).then(res => res.data),
  logout: (returnUrl?: string) => 
    api.get('/auth/logout', { params: { return_url: returnUrl } }).then(res => res.data),
}

// Users Admin API
export const usersApi = {
  // Users
  getUsers: (params?: { is_active?: boolean; search?: string }) =>
    api.get('/admin/users', { params }).then(res => res.data),
  getUser: (id: number) =>
    api.get(`/admin/users/${id}`).then(res => res.data),
  updateUser: (id: number, data: { is_active?: boolean; is_superadmin?: boolean }) =>
    api.put(`/admin/users/${id}`, data).then(res => res.data),
  validateUser: (id: number) =>
    api.post(`/admin/users/${id}/validate`).then(res => res.data),
  deleteUser: (id: number) =>
    api.delete(`/admin/users/${id}`).then(res => res.data),
  
  // Permissions
  getUserPermissions: (userId: number, department?: string) =>
    api.get(`/admin/users/${userId}/permissions`, { params: { department } }).then(res => res.data),
  updatePermission: (userId: number, department: string, data: {
    can_view_scolarite?: boolean;
    can_edit_scolarite?: boolean;
    can_view_recrutement?: boolean;
    can_edit_recrutement?: boolean;
    can_view_budget?: boolean;
    can_edit_budget?: boolean;
    can_view_edt?: boolean;
    can_edit_edt?: boolean;
    can_import?: boolean;
    can_export?: boolean;
    is_dept_admin?: boolean;
  }) => api.put(`/admin/users/${userId}/permissions/${department}`, data).then(res => res.data),
  deletePermission: (userId: number, department: string) =>
    api.delete(`/admin/users/${userId}/permissions/${department}`).then(res => res.data),
  grantPermissions: (userId: number, departments: string[], permissions: {
    can_view_scolarite?: boolean;
    can_view_recrutement?: boolean;
    can_view_budget?: boolean;
    can_view_edt?: boolean;
    can_export?: boolean;
  }) => api.post(`/admin/users/${userId}/permissions/bulk`, { departments, permissions }).then(res => res.data),
  
  // Department overview
  getDepartmentOverview: () =>
    api.get('/admin/users/departments/overview').then(res => res.data),
}

export default api
