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

