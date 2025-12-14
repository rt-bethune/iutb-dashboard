import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Settings, Database, Trash2, Play, 
  CheckCircle, AlertCircle, Clock, 
  Server, HardDrive, Activity,
  Loader2, X
} from 'lucide-react'
import StatCard from '@/components/StatCard'
import { adminApi } from '@/services/api'

// Types
interface DataSource {
  id: string
  name: string
  type: string
  status: string
  description?: string
  base_url?: string
  enabled: boolean
  auto_sync: boolean
  sync_interval_hours: number
  last_sync?: string
  last_error?: string
  records_count?: number
}

interface CacheStats {
  connected: boolean
  keys: number
  hits: number
  misses: number
  memory_used: string
  hit_rate: number
}

interface ScheduledJob {
  id: string
  name: string
  description?: string
  schedule: string
  next_run?: string
  enabled: boolean
}

interface SystemSettings {
  dashboard_title: string
  academic_year: string
  cache_enabled: boolean
  cache_ttl_default: number
  items_per_page: number
  default_chart_type: string
  date_format: string
  email_notifications: boolean
  notification_email?: string
}

export default function Admin() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'overview' | 'sources' | 'cache' | 'jobs' | 'settings'>('overview')

  // Queries
  const { data: dashboard, isLoading: loadingDashboard } = useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: adminApi.getDashboard,
  })

  const { data: sources } = useQuery({
    queryKey: ['admin', 'sources'],
    queryFn: () => adminApi.getSources(),
  })

  const { data: cacheStats } = useQuery({
    queryKey: ['admin', 'cache'],
    queryFn: () => adminApi.getCacheStats(),
  })

  const { data: jobs } = useQuery({
    queryKey: ['admin', 'jobs'],
    queryFn: () => adminApi.getJobs(),
  })

  const { data: settings } = useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: adminApi.getSettings,
  })

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [runningJobId, setRunningJobId] = useState<string | null>(null)

  // Auto-hide toast after 4 seconds
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  // Mutations
  const clearCacheMutation = useMutation({
    mutationFn: adminApi.clearCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cache'] })
      setToast({ message: 'Cache vidé avec succès', type: 'success' })
    },
    onError: () => {
      setToast({ message: 'Erreur lors du vidage du cache', type: 'error' })
    },
  })

  const runJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      setRunningJobId(jobId)
      return adminApi.runJob(jobId)
    },
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: ['admin'] })
      const job = jobs?.find((j: ScheduledJob) => j.id === jobId)
      setToast({ message: `Job "${job?.name || jobId}" exécuté avec succès`, type: 'success' })
      setRunningJobId(null)
    },
    onError: (_error, jobId) => {
      const job = jobs?.find((j: ScheduledJob) => j.id === jobId)
      setToast({ message: `Erreur lors de l'exécution du job "${job?.name || jobId}"`, type: 'error' })
      setRunningJobId(null)
    },
  })

  const updateSettingsMutation = useMutation({
    mutationFn: adminApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'settings'] })
    },
  })

  if (loadingDashboard) {
    return <div className="flex items-center justify-center h-64">Chargement...</div>
  }

  const tabs = [
    { id: 'overview', label: 'Vue d\'ensemble', icon: Activity },
    { id: 'sources', label: 'Sources de données', icon: Database },
    { id: 'cache', label: 'Cache', icon: HardDrive },
    { id: 'jobs', label: 'Jobs planifiés', icon: Clock },
    { id: 'settings', label: 'Paramètres', icon: Settings },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
        <p className="text-gray-500 mt-1">Gérer les sources de données, le cache et les paramètres</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {tabs.map(tab => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <OverviewTab dashboard={dashboard} />
      )}

      {activeTab === 'sources' && (
        <SourcesTab sources={Array.isArray(sources) ? sources : []} />
      )}

      {activeTab === 'cache' && (
        <CacheTab 
          stats={cacheStats} 
          onClear={(domain) => clearCacheMutation.mutate(domain)}
          isClearing={clearCacheMutation.isPending}
        />
      )}

      {activeTab === 'jobs' && (
        <JobsTab 
          jobs={jobs || []} 
          onRun={(id) => runJobMutation.mutate(id)}
          runningJobId={runningJobId}
        />
      )}

      {activeTab === 'settings' && (
        <SettingsTab 
          settings={settings} 
          onSave={(data) => updateSettingsMutation.mutate(data)}
          isSaving={updateSettingsMutation.isPending}
        />
      )}

      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg z-50 ${
          toast.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          {toast.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600" />
          )}
          <span className={toast.type === 'success' ? 'text-green-800' : 'text-red-800'}>
            {toast.message}
          </span>
          <button 
            onClick={() => setToast(null)}
            className={`ml-2 ${toast.type === 'success' ? 'text-green-600 hover:text-green-800' : 'text-red-600 hover:text-red-800'}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}

// Overview Tab
function OverviewTab({ dashboard }: { dashboard: any }) {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Sources de données"
          value={`${dashboard?.active_sources ?? 0}/${dashboard?.total_sources ?? 0} actives`}
          icon={<Database className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Cache Redis"
          value={dashboard?.cache_stats?.connected ? 'Connecté' : 'Déconnecté'}
          subtitle={`${dashboard?.cache_stats?.keys ?? 0} clés en cache`}
          icon={<HardDrive className="w-6 h-6" />}
          color={dashboard?.cache_stats?.connected ? 'green' : 'red'}
        />
        <StatCard
          title="Jobs planifiés"
          value={dashboard?.scheduled_jobs ?? 0}
          subtitle="Tâches automatiques"
          icon={<Clock className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Sources en erreur"
          value={dashboard?.sources_in_error ?? 0}
          icon={<AlertCircle className="w-6 h-6" />}
          color={dashboard?.sources_in_error > 0 ? 'red' : 'green'}
        />
      </div>

      {/* Cache details */}
      {dashboard?.cache_stats?.connected && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance du cache</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {((dashboard.cache_stats.hit_rate ?? 0) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-500">Taux de hit</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{dashboard.cache_stats.hits ?? 0}</p>
              <p className="text-sm text-gray-500">Hits</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-600">{dashboard.cache_stats.memory_used ?? 'N/A'}</p>
              <p className="text-sm text-gray-500">Mémoire utilisée</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Sources Tab - Read-only view of configured sources
function SourcesTab({ sources }: { sources: DataSource[] }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Sources de données</h3>
          <p className="text-sm text-gray-500 mt-1">
            Configuration des sources de données pour l'importation
          </p>
        </div>
      </div>

      <div className="grid gap-4">
        {sources.length === 0 ? (
          <div className="card text-center py-8">
            <Database className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">Aucune source de données configurée</p>
          </div>
        ) : (
          sources.map(source => (
            <div key={source.id} className="card">
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${
                  source.status === 'active' ? 'bg-green-100' :
                  source.status === 'error' ? 'bg-red-100' : 'bg-gray-100'
                }`}>
                  <Database className={`w-6 h-6 ${
                    source.status === 'active' ? 'text-green-600' :
                    source.status === 'error' ? 'text-red-600' : 'text-gray-600'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-gray-900">{source.name}</h4>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      source.status === 'active' ? 'bg-green-100 text-green-700' :
                      source.status === 'error' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {source.status === 'active' ? 'Actif' : 
                       source.status === 'error' ? 'Erreur' : 'Inactif'}
                    </span>
                    {!source.enabled && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700">
                        Désactivé
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{source.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                    <span className="capitalize">Type: {source.type}</span>
                    {source.auto_sync && (
                      <span>Sync auto: toutes les {source.sync_interval_hours}h</span>
                    )}
                    {source.records_count !== undefined && source.records_count > 0 && (
                      <span>{source.records_count} enregistrements</span>
                    )}
                  </div>
                  {source.last_error && (
                    <p className="text-sm text-red-500 mt-2">Erreur: {source.last_error}</p>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// Cache Tab
function CacheTab({ 
  stats, 
  onClear, 
  isClearing 
}: { 
  stats?: CacheStats
  onClear: (domain?: string) => void
  isClearing: boolean
}) {
  const domains = ['scolarite', 'recrutement', 'budget', 'edt']

  return (
    <div className="space-y-6">
      {/* Cache stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="État"
          value={stats?.connected ? 'Connecté' : 'Déconnecté'}
          icon={<Server className="w-6 h-6" />}
          color={stats?.connected ? 'green' : 'red'}
        />
        <StatCard
          title="Clés en cache"
          value={stats?.keys ?? 0}
          icon={<HardDrive className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Taux de hit"
          value={`${((stats?.hit_rate ?? 0) * 100).toFixed(1)}%`}
          subtitle={`${stats?.hits ?? 0} hits / ${stats?.misses ?? 0} misses`}
          color="blue"
        />
        <StatCard
          title="Mémoire utilisée"
          value={stats?.memory_used ?? 'N/A'}
          icon={<HardDrive className="w-6 h-6" />}
          color="blue"
        />
      </div>

      {/* Clear cache */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Vider le cache</h3>
        <p className="text-sm text-gray-500 mb-4">
          Videz le cache pour forcer un rafraîchissement des données depuis les sources.
        </p>
        
        <div className="flex flex-wrap gap-3">
          {domains.map(domain => (
            <button
              key={domain}
              onClick={() => onClear(domain)}
              disabled={isClearing}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors capitalize"
            >
              {isClearing ? <Loader2 className="w-4 h-4 animate-spin" /> : domain}
            </button>
          ))}
          <button
            onClick={() => onClear()}
            disabled={isClearing}
            className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Tout vider
          </button>
        </div>
      </div>
    </div>
  )
}

// Jobs Tab
function JobsTab({ 
  jobs, 
  onRun, 
  runningJobId 
}: { 
  jobs: ScheduledJob[]
  onRun: (id: string) => void
  runningJobId: string | null
}) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">Jobs planifiés</h3>
        <p className="text-sm text-gray-500 mt-1">
          Tâches automatiques de rafraîchissement des données
        </p>
      </div>
      
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Job</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Fréquence</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Prochaine exécution</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">État</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {jobs.map(job => {
              const isThisJobRunning = runningJobId === job.id
              const isAnyJobRunning = runningJobId !== null
              return (
              <tr key={job.id} className={`hover:bg-gray-50 ${isThisJobRunning ? 'bg-blue-50' : ''}`}>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{job.name}</div>
                  {job.description && (
                    <div className="text-sm text-gray-500">{job.description}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {job.schedule}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {job.next_run ? new Date(job.next_run).toLocaleString('fr-FR') : '-'}
                </td>
                <td className="px-4 py-3">
                  {isThisJobRunning ? (
                    <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700 flex items-center gap-1 w-fit">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      En cours...
                    </span>
                  ) : (
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      job.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {job.enabled ? 'Actif' : 'Inactif'}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onRun(job.id)}
                    disabled={isAnyJobRunning || !job.enabled}
                    className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title={isThisJobRunning ? 'Exécution en cours...' : 'Exécuter maintenant'}
                  >
                    {isThisJobRunning ? (
                      <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                  </button>
                </td>
              </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Settings Tab
function SettingsTab({ 
  settings,
  onSave,
  isSaving
}: { 
  settings?: SystemSettings
  onSave: (data: SystemSettings) => void
  isSaving: boolean
}) {
  const [formData, setFormData] = useState<SystemSettings>(settings || {
    dashboard_title: 'Dashboard Département',
    academic_year: '2024-2025',
    cache_enabled: true,
    cache_ttl_default: 3600,
    items_per_page: 25,
    default_chart_type: 'bar',
    date_format: 'DD/MM/YYYY',
    email_notifications: false,
    notification_email: '',
  })
  const [saved, setSaved] = useState(false)

  // Update form when settings load
  useState(() => {
    if (settings) {
      setFormData(settings)
    }
  })

  const handleChange = (field: keyof SystemSettings, value: string | number | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setSaved(false)
  }

  const handleSave = () => {
    onSave(formData)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Paramètres généraux</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Titre du dashboard
            </label>
            <input
              type="text"
              value={formData.dashboard_title}
              onChange={(e) => handleChange('dashboard_title', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Année universitaire
            </label>
            <input
              type="text"
              value={formData.academic_year}
              onChange={(e) => handleChange('academic_year', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="2024-2025"
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium text-gray-700">Cache activé</label>
              <p className="text-sm text-gray-500">Activer la mise en cache Redis des données</p>
            </div>
            <button
              onClick={() => handleChange('cache_enabled', !formData.cache_enabled)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                formData.cache_enabled ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            >
              <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                formData.cache_enabled ? 'left-7' : 'left-1'
              }`} />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              TTL par défaut (secondes)
            </label>
            <input
              type="number"
              value={formData.cache_ttl_default}
              onChange={(e) => handleChange('cache_ttl_default', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">Durée de vie des données en cache</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Affichage</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Éléments par page
            </label>
            <select
              value={formData.items_per_page}
              onChange={(e) => handleChange('items_per_page', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type de graphique par défaut
            </label>
            <select
              value={formData.default_chart_type}
              onChange={(e) => handleChange('default_chart_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="bar">Barres</option>
              <option value="line">Lignes</option>
              <option value="pie">Camembert</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-3">
        {saved && (
          <span className="flex items-center text-green-600 text-sm">
            <CheckCircle className="w-4 h-4 mr-1" />
            Paramètres sauvegardés
          </span>
        )}
        <button 
          onClick={handleSave}
          disabled={isSaving}
          className="btn-primary flex items-center gap-2"
        >
          {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
          Enregistrer les modifications
        </button>
      </div>
    </div>
  )
}
