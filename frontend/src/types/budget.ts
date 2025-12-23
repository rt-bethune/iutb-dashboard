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

