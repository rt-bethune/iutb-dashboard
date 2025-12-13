import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminRecrutementApi } from '../services/api'
import { 
  Plus, Trash2, Upload, Users, FileSpreadsheet, Save,
  TrendingUp, CheckCircle, XCircle, Clock, BarChart3, School
} from 'lucide-react'

const TYPES_BAC = ['Général', 'Technologique', 'Professionnel']
const MENTIONS = ['TB', 'B', 'AB', 'Passable', 'Non renseignée']

interface StatsForm {
  nb_voeux: number
  nb_acceptes: number
  nb_confirmes: number
  nb_refuses: number
  nb_desistes: number
  par_type_bac: Record<string, number>
  par_mention: Record<string, number>
  par_origine: Record<string, number>
  par_lycees: Record<string, number>
}

export default function AdminRecrutement() {
  const queryClient = useQueryClient()
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear())
  const [showNewCampagneForm, setShowNewCampagneForm] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [activeTab, setActiveTab] = useState<'stats' | 'repartition'>('stats')
  
  // Forms state
  const [newCampagne, setNewCampagne] = useState({ annee: new Date().getFullYear() + 1, nb_places: 100 })
  const [importFile, setImportFile] = useState<File | null>(null)
  const [newOrigine, setNewOrigine] = useState({ departement: '', count: 0 })
  const [newLycee, setNewLycee] = useState({ nom: '', count: 0 })
  
  // Stats form state
  const [statsForm, setStatsForm] = useState<StatsForm>({
    nb_voeux: 0,
    nb_acceptes: 0,
    nb_confirmes: 0,
    nb_refuses: 0,
    nb_desistes: 0,
    par_type_bac: {},
    par_mention: {},
    par_origine: {},
    par_lycees: {},
  })

  // Queries
  const { data: campagnes = [], isLoading: campagnesLoading } = useQuery({
    queryKey: ['recrutementCampagnes'],
    queryFn: adminRecrutementApi.getCampagnes,
  })

  const { data: campagneData } = useQuery({
    queryKey: ['recrutementCampagne', selectedYear],
    queryFn: () => adminRecrutementApi.getCampagne(selectedYear),
    enabled: !!selectedYear && campagnes.some((c: any) => c.annee === selectedYear),
  })

  const { data: stats } = useQuery({
    queryKey: ['recrutementStats', selectedYear],
    queryFn: () => adminRecrutementApi.getStats(selectedYear),
    enabled: !!selectedYear && campagnes.some((c: any) => c.annee === selectedYear),
  })

  // Load stats into form when data arrives
  useEffect(() => {
    if (stats) {
      // Convert top_lycees array to par_lycees dict if needed
      let lycees = stats.par_lycees || {}
      if (!stats.par_lycees && stats.top_lycees) {
        lycees = stats.top_lycees.reduce((acc: Record<string, number>, l: {lycee: string, count: number}) => {
          if (l.lycee) acc[l.lycee] = l.count
          return acc
        }, {})
      }
      setStatsForm({
        nb_voeux: stats.nb_voeux || 0,
        nb_acceptes: stats.nb_acceptes || 0,
        nb_confirmes: stats.nb_confirmes || 0,
        nb_refuses: stats.nb_refuses || 0,
        nb_desistes: stats.nb_desistes || 0,
        par_type_bac: stats.par_type_bac || {},
        par_mention: stats.par_mention || {},
        par_origine: stats.par_origine || {},
        par_lycees: lycees,
      })
    }
  }, [stats])

  // Mutations
  const createCampagneMutation = useMutation({
    mutationFn: adminRecrutementApi.createCampagne,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recrutementCampagnes'] })
      setShowNewCampagneForm(false)
      setNewCampagne({ annee: new Date().getFullYear() + 1, nb_places: 100 })
    },
  })

  const updateCampagneMutation = useMutation({
    mutationFn: ({ annee, data }: { annee: number; data: any }) => 
      adminRecrutementApi.updateCampagne(annee, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recrutementCampagne', selectedYear] })
    },
  })

  const deleteCampagneMutation = useMutation({
    mutationFn: adminRecrutementApi.deleteCampagne,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recrutementCampagnes'] })
    },
  })

  const saveStatsMutation = useMutation({
    mutationFn: (data: StatsForm) => adminRecrutementApi.saveStats(selectedYear, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recrutementStats', selectedYear] })
      queryClient.invalidateQueries({ queryKey: ['recrutementCampagnes'] })
      queryClient.invalidateQueries({ queryKey: ['recrutement', 'indicators'] })
      alert('Indicateurs enregistrés avec succès !')
    },
    onError: (error: any) => {
      alert(`Erreur: ${error.response?.data?.detail || error.message}`)
    },
  })

  const importExcelMutation = useMutation({
    mutationFn: ({ file, annee }: { file: File; annee: number }) => adminRecrutementApi.importExcel(file, annee),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['recrutementCampagnes'] })
      queryClient.invalidateQueries({ queryKey: ['recrutementStats', selectedYear] })
      setShowImportModal(false)
      setImportFile(null)
      alert(`Import réussi: ${data.candidats_importes} candidats importés`)
    },
    onError: (error: any) => {
      alert(`Erreur: ${error.response?.data?.detail || error.message}`)
    },
  })

  const formatPercent = (value: number) =>
    new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 1 }).format(value)

  const handleAddOrigine = () => {
    if (newOrigine.departement && newOrigine.count > 0) {
      setStatsForm({
        ...statsForm,
        par_origine: {
          ...statsForm.par_origine,
          [newOrigine.departement]: newOrigine.count,
        },
      })
      setNewOrigine({ departement: '', count: 0 })
    }
  }

  const handleRemoveOrigine = (dept: string) => {
    const newOrigines = { ...statsForm.par_origine }
    delete newOrigines[dept]
    setStatsForm({ ...statsForm, par_origine: newOrigines })
  }

  const handleAddLycee = () => {
    if (newLycee.nom && newLycee.count > 0) {
      setStatsForm({
        ...statsForm,
        par_lycees: {
          ...statsForm.par_lycees,
          [newLycee.nom]: newLycee.count,
        },
      })
      setNewLycee({ nom: '', count: 0 })
    }
  }

  const handleRemoveLycee = (lycee: string) => {
    const newLycees = { ...statsForm.par_lycees }
    delete newLycees[lycee]
    setStatsForm({ ...statsForm, par_lycees: newLycees })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Administration Recrutement</h1>
          <p className="text-gray-600">Saisir les indicateurs Parcoursup par campagne</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Upload size={18} />
            Importer fichier
          </button>
          <button
            onClick={() => setShowNewCampagneForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Plus size={18} />
            Nouvelle campagne
          </button>
        </div>
      </div>

      {/* Year selector */}
      <div className="flex gap-2 flex-wrap">
        {campagnes.map((c: any) => (
          <button
            key={c.annee}
            onClick={() => setSelectedYear(c.annee)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedYear === c.annee
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {c.annee}
          </button>
        ))}
        {campagnes.length === 0 && !campagnesLoading && (
          <p className="text-gray-500 italic">Aucune campagne. Créez-en une pour commencer.</p>
        )}
      </div>

      {/* Campagne config */}
      {campagneData && (
        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold mb-3">Configuration campagne {selectedYear}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-500 mb-1">Nombre de places</label>
              <input
                type="number"
                value={campagneData.nb_places}
                onChange={(e) => updateCampagneMutation.mutate({ 
                  annee: selectedYear, 
                  data: { nb_places: parseInt(e.target.value) }
                })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-1">Rang dernier appelé</label>
              <input
                type="number"
                value={campagneData.rang_dernier_appele || ''}
                onChange={(e) => updateCampagneMutation.mutate({ 
                  annee: selectedYear, 
                  data: { rang_dernier_appele: parseInt(e.target.value) || null }
                })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Non défini"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-1">Taux de remplissage</label>
              <p className="px-3 py-2 bg-gray-50 rounded-lg font-medium">
                {campagneData.nb_places > 0 && statsForm.nb_confirmes > 0
                  ? formatPercent(statsForm.nb_confirmes / campagneData.nb_places)
                  : '-'}
              </p>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  if (confirm(`Supprimer la campagne ${selectedYear} et toutes ses données ?`)) {
                    deleteCampagneMutation.mutate(selectedYear)
                  }
                }}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      {campagneData && (
        <div className="border-b border-gray-200">
          <nav className="flex gap-4">
            <button
              onClick={() => setActiveTab('stats')}
              className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'stats'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <BarChart3 size={18} />
                Indicateurs principaux
              </div>
            </button>
            <button
              onClick={() => setActiveTab('repartition')}
              className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'repartition'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <Users size={18} />
                Répartitions
              </div>
            </button>
          </nav>
        </div>
      )}

      {/* Stats Form */}
      {campagneData && activeTab === 'stats' && (
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <BarChart3 size={20} />
            Indicateurs de recrutement - {selectedYear}
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                <Users size={14} className="inline mr-1" />
                Total vœux/candidats
              </label>
              <input
                type="number"
                min="0"
                value={statsForm.nb_voeux}
                onChange={(e) => setStatsForm({ ...statsForm, nb_voeux: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg text-lg font-semibold"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                <CheckCircle size={14} className="inline mr-1 text-green-600" />
                Acceptés
              </label>
              <input
                type="number"
                min="0"
                value={statsForm.nb_acceptes}
                onChange={(e) => setStatsForm({ ...statsForm, nb_acceptes: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg text-lg font-semibold text-green-600"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                <TrendingUp size={14} className="inline mr-1 text-emerald-600" />
                Confirmés (inscrits)
              </label>
              <input
                type="number"
                min="0"
                value={statsForm.nb_confirmes}
                onChange={(e) => setStatsForm({ ...statsForm, nb_confirmes: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg text-lg font-semibold text-emerald-600"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                <XCircle size={14} className="inline mr-1 text-red-600" />
                Refusés
              </label>
              <input
                type="number"
                min="0"
                value={statsForm.nb_refuses}
                onChange={(e) => setStatsForm({ ...statsForm, nb_refuses: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg text-lg font-semibold text-red-600"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                <Clock size={14} className="inline mr-1 text-orange-600" />
                Désistés
              </label>
              <input
                type="number"
                min="0"
                value={statsForm.nb_desistes}
                onChange={(e) => setStatsForm({ ...statsForm, nb_desistes: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg text-lg font-semibold text-orange-600"
              />
            </div>
          </div>

          {/* Calculated rates */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg mb-6">
            <div>
              <span className="text-sm text-gray-500">Taux d'acceptation</span>
              <p className="text-xl font-bold text-green-600">
                {statsForm.nb_voeux > 0 
                  ? formatPercent(statsForm.nb_acceptes / statsForm.nb_voeux)
                  : '-'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Taux de confirmation</span>
              <p className="text-xl font-bold text-emerald-600">
                {statsForm.nb_acceptes > 0 
                  ? formatPercent(statsForm.nb_confirmes / statsForm.nb_acceptes)
                  : '-'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Taux de remplissage</span>
              <p className="text-xl font-bold text-indigo-600">
                {campagneData.nb_places > 0 
                  ? formatPercent(statsForm.nb_confirmes / campagneData.nb_places)
                  : '-'}
              </p>
            </div>
          </div>

          <button
            onClick={() => saveStatsMutation.mutate(statsForm)}
            disabled={saveStatsMutation.isPending}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            <Save size={18} />
            {saveStatsMutation.isPending ? 'Enregistrement...' : 'Enregistrer les indicateurs'}
          </button>
        </div>
      )}

      {/* Répartitions Form */}
      {campagneData && activeTab === 'repartition' && (
        <div className="space-y-6">
          {/* Par type de bac */}
          <div className="bg-white rounded-xl shadow p-6">
            <h3 className="font-semibold mb-4">Répartition par type de bac</h3>
            <div className="grid grid-cols-3 gap-4">
              {TYPES_BAC.map((type) => (
                <div key={type}>
                  <label className="block text-sm text-gray-600 mb-1">{type}</label>
                  <input
                    type="number"
                    min="0"
                    value={statsForm.par_type_bac[type] || 0}
                    onChange={(e) => setStatsForm({
                      ...statsForm,
                      par_type_bac: {
                        ...statsForm.par_type_bac,
                        [type]: parseInt(e.target.value) || 0,
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Total: {Object.values(statsForm.par_type_bac).reduce((a, b) => a + b, 0)}
            </p>
          </div>

          {/* Par mention */}
          <div className="bg-white rounded-xl shadow p-6">
            <h3 className="font-semibold mb-4">Répartition par mention au bac</h3>
            <div className="grid grid-cols-5 gap-4">
              {MENTIONS.map((mention) => (
                <div key={mention}>
                  <label className="block text-sm text-gray-600 mb-1">{mention}</label>
                  <input
                    type="number"
                    min="0"
                    value={statsForm.par_mention[mention] || 0}
                    onChange={(e) => setStatsForm({
                      ...statsForm,
                      par_mention: {
                        ...statsForm.par_mention,
                        [mention]: parseInt(e.target.value) || 0,
                      },
                    })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Total: {Object.values(statsForm.par_mention).reduce((a, b) => a + b, 0)}
            </p>
          </div>

          {/* Par origine géographique */}
          <div className="bg-white rounded-xl shadow p-6">
            <h3 className="font-semibold mb-4">Répartition par origine géographique</h3>
            
            {/* Add new origine */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Département (ex: 62, 59, Belgique...)"
                value={newOrigine.departement}
                onChange={(e) => setNewOrigine({ ...newOrigine, departement: e.target.value })}
                className="flex-1 px-3 py-2 border rounded-lg"
              />
              <input
                type="number"
                min="0"
                placeholder="Nombre"
                value={newOrigine.count || ''}
                onChange={(e) => setNewOrigine({ ...newOrigine, count: parseInt(e.target.value) || 0 })}
                className="w-24 px-3 py-2 border rounded-lg"
              />
              <button
                onClick={handleAddOrigine}
                className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200"
              >
                <Plus size={18} />
              </button>
            </div>

            {/* Origines list */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(statsForm.par_origine).map(([dept, count]) => (
                <div key={dept} className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
                  <span className="font-medium">{dept}</span>
                  <span className="text-gray-500">{count}</span>
                  <button
                    onClick={() => handleRemoveOrigine(dept)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {Object.keys(statsForm.par_origine).length === 0 && (
                <p className="text-gray-500 text-sm italic">Aucune origine ajoutée</p>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Total: {Object.values(statsForm.par_origine).reduce((a, b) => a + b, 0)}
            </p>
          </div>

          {/* Par lycée */}
          <div className="bg-white rounded-xl shadow p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <School size={20} />
              Répartition par lycée d'origine
            </h3>
            
            {/* Add new lycee */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Nom du lycée..."
                value={newLycee.nom}
                onChange={(e) => setNewLycee({ ...newLycee, nom: e.target.value })}
                className="flex-1 px-3 py-2 border rounded-lg"
              />
              <input
                type="number"
                min="0"
                placeholder="Nombre"
                value={newLycee.count || ''}
                onChange={(e) => setNewLycee({ ...newLycee, count: parseInt(e.target.value) || 0 })}
                className="w-24 px-3 py-2 border rounded-lg"
              />
              <button
                onClick={handleAddLycee}
                className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200"
              >
                <Plus size={18} />
              </button>
            </div>

            {/* Lycees list */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(statsForm.par_lycees).map(([lycee, count]) => (
                <div key={lycee} className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
                  <span className="font-medium text-sm">{lycee}</span>
                  <span className="text-gray-500">{count}</span>
                  <button
                    onClick={() => handleRemoveLycee(lycee)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {Object.keys(statsForm.par_lycees).length === 0 && (
                <p className="text-gray-500 text-sm italic">Aucun lycée ajouté</p>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Total: {Object.values(statsForm.par_lycees).reduce((a, b) => a + b, 0)}
            </p>
          </div>

          <button
            onClick={() => saveStatsMutation.mutate(statsForm)}
            disabled={saveStatsMutation.isPending}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            <Save size={18} />
            {saveStatsMutation.isPending ? 'Enregistrement...' : 'Enregistrer les répartitions'}
          </button>
        </div>
      )}

      {/* New Campagne Modal */}
      {showNewCampagneForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-4">Nouvelle campagne de recrutement</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                <input
                  type="number"
                  value={newCampagne.annee}
                  onChange={(e) => setNewCampagne({ ...newCampagne, annee: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de places</label>
                <input
                  type="number"
                  value={newCampagne.nb_places}
                  onChange={(e) => setNewCampagne({ ...newCampagne, nb_places: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowNewCampagneForm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => createCampagneMutation.mutate(newCampagne)}
                disabled={createCampagneMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Créer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-4">Importer des données Parcoursup</h3>
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
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="import-file-recrutement"
                  />
                  <label htmlFor="import-file-recrutement" className="cursor-pointer text-indigo-600 hover:text-indigo-700">
                    {importFile ? importFile.name : 'Choisir un fichier'}
                  </label>
                  <p className="text-xs text-gray-500 mt-2">
                    Format CSV ou Excel exporté depuis Parcoursup
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
                onClick={() => {
                  if (!importFile) return
                  importExcelMutation.mutate({ file: importFile, annee: selectedYear })
                }}
                disabled={!importFile || importExcelMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {importExcelMutation.isPending ? 'Import...' : 'Importer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
