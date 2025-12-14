import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminBudgetApi } from '../services/api'
import { useDepartment } from '../contexts/DepartmentContext'
import { 
  Plus, Trash2, Upload, Edit2, FileSpreadsheet, 
  TrendingUp, TrendingDown, DollarSign, AlertCircle
} from 'lucide-react'

// Types
interface LigneBudget {
  id: number
  categorie: string
  budget_initial: number
  budget_modifie: number
  engage: number
  paye: number
  disponible: number
}

interface Depense {
  id: number
  libelle: string
  montant: number
  categorie: string
  date_depense: string
  fournisseur?: string
  numero_commande?: string
  statut: string
}

const CATEGORIES = [
  { value: 'fonctionnement', label: 'Fonctionnement' },
  { value: 'investissement', label: 'Investissement' },
  { value: 'missions', label: 'Missions' },
  { value: 'fournitures', label: 'Fournitures' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'formation', label: 'Formation' },
  { value: 'autre', label: 'Autre' },
]

export default function AdminBudget() {
  const { department } = useDepartment()
  const queryClient = useQueryClient()
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear())
  const [showNewYearForm, setShowNewYearForm] = useState(false)
  const [showNewLigneForm, setShowNewLigneForm] = useState(false)
  const [showNewDepenseForm, setShowNewDepenseForm] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [editingLigne, setEditingLigne] = useState<number | null>(null)
  
  // Forms state
  const [newYear, setNewYear] = useState({ annee: new Date().getFullYear() + 1, budget_total: 0, previsionnel: 0 })
  const [newLigne, setNewLigne] = useState({ categorie: 'fonctionnement', budget_initial: 0, budget_modifie: 0, engage: 0, paye: 0 })
  const [newDepense, setNewDepense] = useState({ libelle: '', montant: 0, categorie: 'fonctionnement', date_depense: new Date().toISOString().split('T')[0], fournisseur: '', statut: 'engagee' })
  const [importFile, setImportFile] = useState<File | null>(null)

  // Queries
  const { data: years = [], isLoading: yearsLoading } = useQuery({
    queryKey: ['budgetYears', department],
    queryFn: () => adminBudgetApi.getYears(department),
  })

  const { data: yearData } = useQuery({
    queryKey: ['budgetYear', department, selectedYear],
    queryFn: () => adminBudgetApi.getYear(department, selectedYear),
    enabled: !!selectedYear,
  })

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { data: depenses = [], isLoading: depensesLoading } = useQuery({
    queryKey: ['budgetDepenses', department, selectedYear],
    queryFn: () => adminBudgetApi.getDepenses(department, selectedYear, { limit: 100 }),
    enabled: !!selectedYear,
  })

  // Mutations
  const createYearMutation = useMutation({
    mutationFn: (data: { annee: number; budget_total: number; previsionnel: number }) => 
      adminBudgetApi.createYear(department, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetYears', department] })
      setShowNewYearForm(false)
      setNewYear({ annee: new Date().getFullYear() + 1, budget_total: 0, previsionnel: 0 })
    },
  })

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const deleteYearMutation = useMutation({
    mutationFn: (annee: number) => adminBudgetApi.deleteYear(department, annee),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetYears', department] })
    },
  })

  const createLigneMutation = useMutation({
    mutationFn: (data: typeof newLigne) => adminBudgetApi.createLigne(department, selectedYear, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetYear', department, selectedYear] })
      setShowNewLigneForm(false)
      setNewLigne({ categorie: 'fonctionnement', budget_initial: 0, budget_modifie: 0, engage: 0, paye: 0 })
    },
  })

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const updateLigneMutation = useMutation({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    mutationFn: ({ id, data }: { id: number; data: any }) => adminBudgetApi.updateLigne(department, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetYear', department, selectedYear] })
      setEditingLigne(null)
    },
  })

  const deleteLigneMutation = useMutation({
    mutationFn: (ligneId: number) => adminBudgetApi.deleteLigne(department, ligneId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetYear', department, selectedYear] })
    },
  })

  const createDepenseMutation = useMutation({
    mutationFn: (data: typeof newDepense) => adminBudgetApi.createDepense(department, selectedYear, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetDepenses', department, selectedYear] })
      queryClient.invalidateQueries({ queryKey: ['budgetYear', department, selectedYear] })
      setShowNewDepenseForm(false)
      setNewDepense({ libelle: '', montant: 0, categorie: 'fonctionnement', date_depense: new Date().toISOString().split('T')[0], fournisseur: '', statut: 'engagee' })
    },
  })

  const deleteDepenseMutation = useMutation({
    mutationFn: (depenseId: number) => adminBudgetApi.deleteDepense(department, depenseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgetDepenses', department, selectedYear] })
      queryClient.invalidateQueries({ queryKey: ['budgetYear', department, selectedYear] })
    },
  })

  const importMutation = useMutation({
    mutationFn: ({ file, annee }: { file: File; annee: number }) => adminBudgetApi.importFile(department, file, annee),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['budgetYears', department] })
      queryClient.invalidateQueries({ queryKey: ['budgetYear', department, selectedYear] })
      setShowImportModal(false)
      setImportFile(null)
      alert(`Import réussi: ${data.lignes_importees} lignes importées`)
    },
    onError: (error: any) => {
      alert(`Erreur: ${error.response?.data?.detail || error.message}`)
    },
  })

  const formatCurrency = (value: number) => 
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value)

  const formatPercent = (value: number) =>
    new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 1 }).format(value)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Administration Budget</h1>
          <p className="text-gray-600">Gérer les données budgétaires par année</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Upload size={18} />
            Importer Excel
          </button>
          <button
            onClick={() => setShowNewYearForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Plus size={18} />
            Nouvelle année
          </button>
        </div>
      </div>

      {/* Year selector */}
      <div className="flex gap-2 flex-wrap">
        {years.map((year: any) => (
          <button
            key={year.annee}
            onClick={() => setSelectedYear(year.annee)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedYear === year.annee
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {year.annee}
          </button>
        ))}
        {years.length === 0 && !yearsLoading && (
          <p className="text-gray-500 italic">Aucune année budgétaire. Créez-en une ou importez des données.</p>
        )}
      </div>

      {/* Year summary */}
      {yearData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="text-blue-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Budget Total</p>
                <p className="text-xl font-bold">{formatCurrency(yearData.budget_total)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrendingUp className="text-orange-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Engagé</p>
                <p className="text-xl font-bold">{formatCurrency(yearData.total_engage)}</p>
                <p className="text-xs text-gray-400">{formatPercent(yearData.taux_engagement)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingDown className="text-green-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Payé</p>
                <p className="text-xl font-bold">{formatCurrency(yearData.total_paye)}</p>
                <p className="text-xs text-gray-400">{formatPercent(yearData.taux_execution)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <AlertCircle className="text-purple-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Disponible</p>
                <p className="text-xl font-bold">{formatCurrency(yearData.total_disponible)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Budget lines */}
      {yearData && (
        <div className="bg-white rounded-xl shadow">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="text-lg font-semibold">Lignes budgétaires - {selectedYear}</h2>
            <button
              onClick={() => setShowNewLigneForm(true)}
              className="flex items-center gap-1 px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-sm"
            >
              <Plus size={16} />
              Ajouter
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Catégorie</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Budget Initial</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Budget Modifié</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Engagé</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Payé</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Disponible</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {yearData.lignes.map((ligne: LigneBudget) => (
                  <tr key={ligne.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium capitalize">{ligne.categorie}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(ligne.budget_initial)}</td>
                    <td className="px-4 py-3 text-right">{formatCurrency(ligne.budget_modifie)}</td>
                    <td className="px-4 py-3 text-right text-orange-600">{formatCurrency(ligne.engage)}</td>
                    <td className="px-4 py-3 text-right text-green-600">{formatCurrency(ligne.paye)}</td>
                    <td className="px-4 py-3 text-right text-blue-600">{formatCurrency(ligne.disponible)}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => setEditingLigne(ligne.id)}
                          className="p-1 text-gray-500 hover:text-indigo-600"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Supprimer cette ligne ?')) {
                              deleteLigneMutation.mutate(ligne.id)
                            }
                          }}
                          className="p-1 text-gray-500 hover:text-red-600"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {yearData.lignes.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                      Aucune ligne budgétaire. Ajoutez-en une ou importez un fichier Excel.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Depenses */}
      {yearData && (
        <div className="bg-white rounded-xl shadow">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="text-lg font-semibold">Dépenses - {selectedYear}</h2>
            <button
              onClick={() => setShowNewDepenseForm(true)}
              className="flex items-center gap-1 px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-sm"
            >
              <Plus size={16} />
              Ajouter
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Date</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Libellé</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Catégorie</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Montant</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Statut</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {depenses.map((dep: Depense) => (
                  <tr key={dep.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{new Date(dep.date_depense).toLocaleDateString('fr-FR')}</td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium">{dep.libelle}</p>
                        {dep.fournisseur && <p className="text-xs text-gray-500">{dep.fournisseur}</p>}
                      </div>
                    </td>
                    <td className="px-4 py-3 capitalize">{dep.categorie}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatCurrency(dep.montant)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        dep.statut === 'payee' ? 'bg-green-100 text-green-700' :
                        dep.statut === 'engagee' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {dep.statut}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => {
                            if (confirm('Supprimer cette dépense ?')) {
                              deleteDepenseMutation.mutate(dep.id)
                            }
                          }}
                          className="p-1 text-gray-500 hover:text-red-600"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {depenses.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      Aucune dépense enregistrée.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Year Modal */}
      {showNewYearForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-4">Nouvelle année budgétaire</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                <input
                  type="number"
                  value={newYear.annee}
                  onChange={(e) => setNewYear({ ...newYear, annee: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Budget Total</label>
                <input
                  type="number"
                  value={newYear.budget_total}
                  onChange={(e) => setNewYear({ ...newYear, budget_total: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prévisionnel</label>
                <input
                  type="number"
                  value={newYear.previsionnel}
                  onChange={(e) => setNewYear({ ...newYear, previsionnel: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowNewYearForm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => createYearMutation.mutate(newYear)}
                disabled={createYearMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Créer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Ligne Modal */}
      {showNewLigneForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-4">Nouvelle ligne budgétaire</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie</label>
                <select
                  value={newLigne.categorie}
                  onChange={(e) => setNewLigne({ ...newLigne, categorie: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Budget Initial</label>
                <input
                  type="number"
                  value={newLigne.budget_initial}
                  onChange={(e) => setNewLigne({ ...newLigne, budget_initial: parseFloat(e.target.value), budget_modifie: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowNewLigneForm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => createLigneMutation.mutate(newLigne)}
                disabled={createLigneMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Ajouter
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Depense Modal */}
      {showNewDepenseForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Nouvelle dépense</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Libellé</label>
                <input
                  type="text"
                  value={newDepense.libelle}
                  onChange={(e) => setNewDepense({ ...newDepense, libelle: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  placeholder="Ex: Achat serveur Dell"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Montant (€)</label>
                <input
                  type="number"
                  value={newDepense.montant}
                  onChange={(e) => setNewDepense({ ...newDepense, montant: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie</label>
                <select
                  value={newDepense.categorie}
                  onChange={(e) => setNewDepense({ ...newDepense, categorie: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  value={newDepense.date_depense}
                  onChange={(e) => setNewDepense({ ...newDepense, date_depense: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                <select
                  value={newDepense.statut}
                  onChange={(e) => setNewDepense({ ...newDepense, statut: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="prevue">Prévue</option>
                  <option value="engagee">Engagée</option>
                  <option value="payee">Payée</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Fournisseur</label>
                <input
                  type="text"
                  value={newDepense.fournisseur}
                  onChange={(e) => setNewDepense({ ...newDepense, fournisseur: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  placeholder="Optionnel"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowNewDepenseForm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => createDepenseMutation.mutate(newDepense)}
                disabled={createDepenseMutation.isPending || !newDepense.libelle || !newDepense.montant}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Ajouter
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-4">Importer un fichier Excel</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                <input
                  type="number"
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Fichier Excel</label>
                <div className="border-2 border-dashed rounded-lg p-6 text-center">
                  <FileSpreadsheet className="mx-auto text-gray-400 mb-2" size={40} />
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="import-file"
                  />
                  <label htmlFor="import-file" className="cursor-pointer text-indigo-600 hover:text-indigo-700">
                    {importFile ? importFile.name : 'Choisir un fichier'}
                  </label>
                  <p className="text-xs text-gray-500 mt-2">
                    Colonnes attendues: Catégorie, Budget Initial, Budget Modifié, Engagé, Payé
                  </p>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => { setShowImportModal(false); setImportFile(null); }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => importFile && importMutation.mutate({ file: importFile, annee: selectedYear })}
                disabled={!importFile || importMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {importMutation.isPending ? 'Import...' : 'Importer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
