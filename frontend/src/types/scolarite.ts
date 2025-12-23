// Scolarité types
export interface ScolariteIndicators {
  total_etudiants: number
  etudiants_par_formation: Record<string, number>
  etudiants_par_semestre: Record<string, number>
  moyenne_generale: number
  taux_reussite_global: number
  taux_absenteisme: number
  modules_stats: ModuleStats[]
  semestres_stats: SemestreStats[]
  evolution_effectifs: Record<string, number>
}

export interface ModuleStats {
  code: string
  nom: string
  moyenne: number
  mediane: number
  ecart_type: number
  taux_reussite: number
  nb_etudiants: number
  nb_notes: number
}

export interface SemestreStats {
  code: string
  nom: string
  annee: string
  nb_etudiants: number
  moyenne_generale: number
  taux_reussite: number
  taux_absenteisme: number
}

export interface Etudiant {
  id: string
  nom: string
  prenom: string
  email?: string
  formation: string
  semestre: string
  groupe?: string
}

