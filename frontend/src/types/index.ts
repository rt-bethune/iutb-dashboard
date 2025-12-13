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

// Recrutement types
export interface RecrutementIndicators {
  annee_courante: number
  total_candidats: number
  candidats_acceptes: number
  candidats_confirmes: number
  taux_acceptation: number
  taux_confirmation: number
  par_type_bac: Record<string, number>
  par_origine: Record<string, number>
  par_mention: Record<string, number>
  evolution: VoeuStats[]
  top_lycees: Array<{ lycee: string; count: number }>
}

export interface VoeuStats {
  annee: number
  nb_voeux: number
  nb_acceptes: number
  nb_confirmes: number
  nb_refuses: number
  nb_desistes: number
  rang_dernier_appele?: number
}

// Budget types
export interface BudgetIndicators {
  annee: number
  budget_total: number
  total_engage: number
  total_paye: number
  total_disponible: number
  taux_execution: number
  taux_engagement: number
  par_categorie: LigneBudget[]
  evolution_mensuelle: Record<string, number>
  top_depenses: Depense[]
  previsionnel: number
  realise: number
}

export interface LigneBudget {
  categorie: string
  budget_initial: number
  budget_modifie: number
  engage: number
  paye: number
  disponible: number
}

export interface Depense {
  id: string
  libelle: string
  montant: number
  categorie: string
  date: string
  fournisseur?: string
}

// EDT types
export interface EDTIndicators {
  periode_debut: string
  periode_fin: string
  total_heures: number
  heures_cm: number
  heures_td: number
  heures_tp: number
  repartition_types: Record<string, number>
  charges_enseignants: ChargeEnseignant[]
  total_heures_complementaires: number
  occupation_salles: OccupationSalle[]
  taux_occupation_moyen: number
  heures_par_module: Record<string, number>
  evolution_hebdo: Record<string, number>
}

export interface ChargeEnseignant {
  enseignant: string
  heures_cm: number
  heures_td: number
  heures_tp: number
  heures_projet: number
  total_heures: number
  heures_statutaires: number
  heures_complementaires: number
}

export interface OccupationSalle {
  salle: string
  capacite: number
  heures_occupees: number
  heures_disponibles: number
  taux_occupation: number
}
