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

