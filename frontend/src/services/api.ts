import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Scolarité
export const scolariteApi = {
  getIndicators: () => api.get('/scolarite/indicators?refresh=true').then(res => res.data),
  getEtudiants: (params?: { formation?: string; semestre?: string; limit?: number }) => 
    api.get('/scolarite/etudiants', { params }).then(res => res.data),
  getModules: (semestre?: string) => 
    api.get('/scolarite/modules', { params: { semestre } }).then(res => res.data),
  getEffectifs: () => api.get('/scolarite/effectifs').then(res => res.data),
  getReussite: () => api.get('/scolarite/reussite').then(res => res.data),
}

// Recrutement
export const recrutementApi = {
  getIndicators: (annee?: number) => 
    api.get('/recrutement/indicators', { params: { annee } }).then(res => res.data),
  getEvolution: () => api.get('/recrutement/evolution').then(res => res.data),
  getParBac: (annee?: number) => 
    api.get('/recrutement/par-bac', { params: { annee } }).then(res => res.data),
  getParOrigine: (annee?: number) => 
    api.get('/recrutement/par-origine', { params: { annee } }).then(res => res.data),
  getTopLycees: (limit?: number) => 
    api.get('/recrutement/top-lycees', { params: { limit } }).then(res => res.data),
  importFile: (file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/recrutement/import?annee=${annee}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
}

// Budget
export const budgetApi = {
  getIndicators: (annee?: number) => 
    api.get('/budget/indicators', { params: { annee } }).then(res => res.data),
  getParCategorie: (annee?: number) => 
    api.get('/budget/par-categorie', { params: { annee } }).then(res => res.data),
  getEvolution: (annee?: number) => 
    api.get('/budget/evolution', { params: { annee } }).then(res => res.data),
  getExecution: () => api.get('/budget/execution').then(res => res.data),
  getTopDepenses: (limit?: number) => 
    api.get('/budget/top-depenses', { params: { limit } }).then(res => res.data),
  importFile: (file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/budget/import?annee=${annee}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
}

// EDT
export const edtApi = {
  getIndicators: (annee?: string) => 
    api.get('/edt/indicators', { params: { annee } }).then(res => res.data),
  getCharges: (enseignant?: string) => 
    api.get('/edt/charges', { params: { enseignant } }).then(res => res.data),
  getOccupation: (salle?: string) => 
    api.get('/edt/occupation', { params: { salle } }).then(res => res.data),
  getRepartition: () => api.get('/edt/repartition').then(res => res.data),
  getHeuresComplementaires: () => api.get('/edt/heures-complementaires').then(res => res.data),
  getParModule: () => api.get('/edt/par-module').then(res => res.data),
  importFile: (file: File, annee?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/edt/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { annee },
    }).then(res => res.data)
  },
}

// Upload
export const uploadApi = {
  uploadFile: (file: File, type: string, description?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    if (description) formData.append('description', description)
    return api.post('/upload/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  listFiles: (type?: string) =>
    api.get('/upload/files', { params: { type } }).then(res => res.data),
  deleteFile: (filename: string, type: string) =>
    api.delete(`/upload/file/${type}/${filename}`).then(res => res.data),
  downloadFile: (filename: string, type: string) =>
    api.get(`/upload/download/${type}/${filename}`, { responseType: 'blob' }),
}

// Admin
export const adminApi = {
  // Dashboard
  getDashboard: () => api.get('/admin/dashboard').then(res => res.data),
  
  // Sources
  getSources: (type?: string) => 
    api.get('/admin/sources', { params: { type } }).then(res => res.data),
  getSource: (id: string) => 
    api.get(`/admin/sources/${id}`).then(res => res.data),
  createSource: (data: any) => 
    api.post('/admin/sources', data).then(res => res.data),
  updateSource: (id: string, data: any) => 
    api.put(`/admin/sources/${id}`, data).then(res => res.data),
  deleteSource: (id: string) => 
    api.delete(`/admin/sources/${id}`).then(res => res.data),
  syncSource: (id: string) => 
    api.post(`/admin/sources/${id}/sync`).then(res => res.data),
  testSource: (id: string) => 
    api.post(`/admin/sources/${id}/test`).then(res => res.data),
  
  // Settings
  getSettings: () => api.get('/admin/settings').then(res => res.data),
  updateSettings: (data: any) => 
    api.put('/admin/settings', data).then(res => res.data),
  
  // Cache
  getCacheStats: () => api.get('/admin/cache/stats').then(res => res.data),
  clearCache: (domain?: string) => 
    api.post('/admin/cache/clear', null, { params: { domain } }).then(res => res.data),
  
  // Jobs
  getJobs: () => api.get('/admin/jobs').then(res => res.data),
  runJob: (id: string) => 
    api.post(`/admin/jobs/${id}/run`).then(res => res.data),
  
  // Logs
  getLogs: (limit?: number, status?: string) => 
    api.get('/admin/logs', { params: { limit, status } }).then(res => res.data),
}

// Admin Budget CRUD
export const adminBudgetApi = {
  // Budget years
  getYears: () => api.get('/admin/budget/years').then(res => res.data),
  getYear: (annee: number) => api.get(`/admin/budget/year/${annee}`).then(res => res.data),
  createYear: (data: { annee: number; budget_total?: number; previsionnel?: number; lignes?: any[] }) =>
    api.post('/admin/budget/year', data).then(res => res.data),
  updateYear: (annee: number, data: { budget_total?: number; previsionnel?: number }) =>
    api.put(`/admin/budget/year/${annee}`, data).then(res => res.data),
  deleteYear: (annee: number) => api.delete(`/admin/budget/year/${annee}`).then(res => res.data),
  
  // Budget lines
  createLigne: (annee: number, data: { categorie: string; budget_initial: number; budget_modifie?: number; engage?: number; paye?: number }) =>
    api.post(`/admin/budget/year/${annee}/ligne`, data).then(res => res.data),
  updateLigne: (ligneId: number, data: { budget_initial?: number; budget_modifie?: number; engage?: number; paye?: number }) =>
    api.put(`/admin/budget/ligne/${ligneId}`, data).then(res => res.data),
  deleteLigne: (ligneId: number) => api.delete(`/admin/budget/ligne/${ligneId}`).then(res => res.data),
  
  // Depenses
  getDepenses: (annee: number, params?: { categorie?: string; statut?: string; limit?: number }) =>
    api.get(`/admin/budget/year/${annee}/depenses`, { params }).then(res => res.data),
  createDepense: (annee: number, data: { libelle: string; montant: number; categorie: string; date_depense: string; fournisseur?: string; numero_commande?: string; statut?: string }) =>
    api.post(`/admin/budget/year/${annee}/depense`, data).then(res => res.data),
  updateDepense: (depenseId: number, data: any) =>
    api.put(`/admin/budget/depense/${depenseId}`, data).then(res => res.data),
  deleteDepense: (depenseId: number) => api.delete(`/admin/budget/depense/${depenseId}`).then(res => res.data),
  
  // Import
  importFile: (file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/admin/budget/import?annee=${annee}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  
  // Indicators (from DB)
  getIndicators: (annee?: number) =>
    api.get('/admin/budget/indicators', { params: { annee } }).then(res => res.data),
}

// Admin Recrutement CRUD
export const adminRecrutementApi = {
  // Campagnes
  getCampagnes: () => api.get('/admin/recrutement/campagnes').then(res => res.data),
  getCampagne: (annee: number) => api.get(`/admin/recrutement/campagne/${annee}`).then(res => res.data),
  createCampagne: (data: { annee: number; nb_places?: number; date_debut?: string; date_fin?: string }) =>
    api.post('/admin/recrutement/campagne', data).then(res => res.data),
  updateCampagne: (annee: number, data: { nb_places?: number; date_debut?: string; date_fin?: string; rang_dernier_appele?: number }) =>
    api.put(`/admin/recrutement/campagne/${annee}`, data).then(res => res.data),
  deleteCampagne: (annee: number) => api.delete(`/admin/recrutement/campagne/${annee}`).then(res => res.data),
  
  // Candidats
  getCandidats: (annee: number, params?: { statut?: string; type_bac?: string; limit?: number }) =>
    api.get(`/admin/recrutement/campagne/${annee}/candidats`, { params }).then(res => res.data),
  getCandidat: (id: number) => api.get(`/admin/recrutement/candidat/${id}`).then(res => res.data),
  createCandidat: (annee: number, data: { type_bac: string; mention_bac?: string; departement_origine?: string; lycee?: string; statut?: string }) =>
    api.post(`/admin/recrutement/campagne/${annee}/candidat`, data).then(res => res.data),
  createCandidatsBulk: (annee: number, candidats: any[]) =>
    api.post(`/admin/recrutement/campagne/${annee}/candidats/bulk`, { candidats }).then(res => res.data),
  updateCandidat: (id: number, data: any) =>
    api.put(`/admin/recrutement/candidat/${id}`, data).then(res => res.data),
  deleteCandidat: (id: number) => api.delete(`/admin/recrutement/candidat/${id}`).then(res => res.data),
  
  // Import
  importCsv: (file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/admin/recrutement/import/csv?annee=${annee}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  importExcel: (file: File, annee: number) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/admin/recrutement/import/excel?annee=${annee}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },
  
  // Stats & Indicators
  getStats: (annee: number) => api.get(`/admin/recrutement/stats/${annee}`).then(res => res.data),
  saveStats: (annee: number, data: {
    nb_voeux: number;
    nb_acceptes: number;
    nb_confirmes: number;
    nb_refuses?: number;
    nb_desistes?: number;
    par_type_bac?: Record<string, number>;
    par_mention?: Record<string, number>;
    par_origine?: Record<string, number>;
    par_lycees?: Record<string, number>;
  }) => api.post(`/admin/recrutement/stats/${annee}`, data).then(res => res.data),
  getEvolution: (limit?: number) => api.get('/admin/recrutement/evolution', { params: { limit } }).then(res => res.data),
  getIndicators: (annee?: number) =>
    api.get('/admin/recrutement/indicators', { params: { annee } }).then(res => res.data),
}

export default api
