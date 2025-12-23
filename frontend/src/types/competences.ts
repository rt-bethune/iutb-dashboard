export interface NiveauCompetence {
  niveau: number
  nom: string
  description?: string
}

export interface Competence {
  code: string
  nom: string
  description?: string
  niveaux: NiveauCompetence[]
}

export interface UEValidation {
  ue_code: string
  ue_titre: string
  moyenne: number | null
  valide: boolean
  semestre?: string
}

export interface UEEtudiant {
  etudiant_id: string
  nom: string
  prenom: string
  formation?: string
  semestre?: string
  parcours?: string
  nb_ues: number
  nb_ues_validees: number
  taux_validation: number
  valide: boolean
  moyenne_generale?: number | null
  ue_validations: UEValidation[]
}

export interface UEStats {
  total_etudiants: number
  taux_validation_global: number
  par_ue: Record<string, number>
  moyenne_par_ue: Record<string, number>
  distribution_taux_validation: Record<string, number>
  parcours_disponibles: string[]
}
