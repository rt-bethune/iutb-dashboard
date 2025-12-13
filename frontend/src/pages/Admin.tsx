import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Settings, Database, RefreshCw, Trash2, Play, 
  CheckCircle, XCircle, AlertCircle, Clock, 
  Server, HardDrive, Activity, FileText,
  Plus, Edit, TestTube, Loader2
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
  next_run?: string
  enabled: boolean
}

interface ActivityLog {
  id: string
  timestamp: string
  action: string
  details?: string
  status: string
  source?: string
}

interface SystemSettings {
  dashboard_title: string
  department_name: string
  academic_year: string
  cache_enabled: boolean
  cache_ttl_default: number
  items_per_page: number
}

export default function Admin() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'overview' | 'sources' | 'cache' | 'jobs' | 'settings' | 'logs'>('overview')

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

  const { data: logs } = useQuery({
    queryKey: ['admin', 'logs'],
    queryFn: () => adminApi.getLogs(50),
  })

  const { data: settings } = useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: adminApi.getSettings,
  })

  // Mutations
  const syncMutation = useMutation({
    mutationFn: adminApi.syncSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] })
    },
  })

  const clearCacheMutation = useMutation({
    mutationFn: adminApi.clearCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cache'] })
    },
  })

  const runJobMutation = useMutation({
    mutationFn: adminApi.runJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] })
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
    { id: 'logs', label: 'Logs', icon: FileText },
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
        <SourcesTab 
          sources={Array.isArray(sources) ? sources : []} 
          onSync={(id) => syncMutation.mutate(id)}
          isSyncing={syncMutation.isPending}
        />
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
          isRunning={runJobMutation.isPending}
        />
      )}

      {activeTab === 'settings' && (
        <SettingsTab settings={settings} />
      )}

      {activeTab === 'logs' && (
        <LogsTab logs={logs || []} />
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
          title="Sources actives"
          value={`${dashboard?.active_sources ?? 0}/${dashboard?.total_sources ?? 0}`}
          icon={<Database className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Cache"
          value={dashboard?.cache_stats?.connected ? 'Connecté' : 'Déconnecté'}
          subtitle={`${dashboard?.cache_stats?.keys ?? 0} clés`}
          icon={<HardDrive className="w-6 h-6" />}
          color={dashboard?.cache_stats?.connected ? 'green' : 'red'}
        />
        <StatCard
          title="Jobs planifiés"
          value={dashboard?.scheduled_jobs ?? 0}
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

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent syncs */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Dernières synchronisations</h3>
          <div className="space-y-3">
            {dashboard?.recent_syncs?.length > 0 ? (
              dashboard.recent_syncs.map((sync: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    {sync.success ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{sync.source_name}</p>
                      <p className="text-sm text-gray-500">{sync.records_synced} enregistrements</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">{sync.duration_seconds}s</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">Aucune synchronisation récente</p>
            )}
          </div>
        </div>

        {/* Recent logs */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Activité récente</h3>
          <div className="space-y-2">
            {dashboard?.recent_logs?.length > 0 ? (
              dashboard.recent_logs.map((log: ActivityLog) => (
                <div key={log.id} className="flex items-start gap-3 p-2">
                  <StatusIcon status={log.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{log.action}</p>
                    {log.details && (
                      <p className="text-sm text-gray-500 truncate">{log.details}</p>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(log.timestamp).toLocaleTimeString('fr-FR')}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">Aucune activité récente</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Sources Tab
function SourcesTab({ 
  sources, 
  onSync, 
  isSyncing 
}: { 
  sources: DataSource[]
  onSync: (id: string) => void
  isSyncing: boolean
}) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Sources de données</h3>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Ajouter une source
        </button>
      </div>

      <div className="grid gap-4">
        {sources.map(source => (
          <div key={source.id} className="card">
            <div className="flex items-start justify-between">
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
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-gray-900">{source.name}</h4>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      source.status === 'active' ? 'bg-green-100 text-green-700' :
                      source.status === 'error' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {source.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{source.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                    <span>Type: {source.type}</span>
                    {source.last_sync && (
                      <span>Dernière sync: {new Date(source.last_sync).toLocaleString('fr-FR')}</span>
                    )}
                    {source.records_count !== undefined && (
                      <span>{source.records_count} enregistrements</span>
                    )}
                  </div>
                  {source.last_error && (
                    <p className="text-sm text-red-500 mt-2">Erreur: {source.last_error}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button 
                  onClick={() => onSync(source.id)}
                  disabled={isSyncing}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Synchroniser"
                >
                  {isSyncing ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <RefreshCw className="w-5 h-5" />
                  )}
                </button>
                <button 
                  className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                  title="Tester la connexion"
                >
                  <TestTube className="w-5 h-5" />
                </button>
                <button 
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Modifier"
                >
                  <Edit className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
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
  isRunning 
}: { 
  jobs: ScheduledJob[]
  onRun: (id: string) => void
  isRunning: boolean
}) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Jobs planifiés</h3>
      
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Job</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Prochaine exécution</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">État</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {jobs.map(job => (
              <tr key={job.id}>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{job.name}</div>
                  <div className="text-sm text-gray-500">{job.id}</div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {job.next_run ? new Date(job.next_run).toLocaleString('fr-FR') : '-'}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    job.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {job.enabled ? 'Actif' : 'Inactif'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onRun(job.id)}
                    disabled={isRunning}
                    className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Exécuter maintenant"
                  >
                    {isRunning ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Settings Tab
function SettingsTab({ settings }: { settings?: SystemSettings }) {
  const [formData, setFormData] = useState<SystemSettings>(settings || {
    dashboard_title: 'Dashboard Département',
    department_name: 'Département RT',
    academic_year: '2024-2025',
    cache_enabled: true,
    cache_ttl_default: 3600,
    items_per_page: 25,
  })

  const handleChange = (field: keyof SystemSettings, value: string | number | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
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
              Nom du département
            </label>
            <input
              type="text"
              value={formData.department_name}
              onChange={(e) => handleChange('department_name', e.target.value)}
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
              <p className="text-sm text-gray-500">Activer la mise en cache des données</p>
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
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Affichage</h3>
        
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
      </div>

      <div className="flex justify-end">
        <button className="btn-primary">
          Enregistrer les modifications
        </button>
      </div>
    </div>
  )
}

// Logs Tab
function LogsTab({ logs }: { logs: ActivityLog[] }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Logs d'activité</h3>
        <button className="text-sm text-blue-600 hover:text-blue-700">
          Exporter les logs
        </button>
      </div>
      
      <div className="card overflow-hidden">
        <div className="divide-y divide-gray-200">
          {logs.map(log => (
            <div key={log.id} className="flex items-start gap-4 p-4 hover:bg-gray-50">
              <StatusIcon status={log.status} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{log.action}</span>
                  {log.source && (
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      {log.source}
                    </span>
                  )}
                </div>
                {log.details && (
                  <p className="text-sm text-gray-500 mt-1">{log.details}</p>
                )}
              </div>
              <span className="text-sm text-gray-400 whitespace-nowrap">
                {new Date(log.timestamp).toLocaleString('fr-FR')}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Helper components
function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'success':
      return <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
    case 'error':
      return <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
    case 'warning':
      return <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0" />
    default:
      return <Activity className="w-5 h-5 text-blue-500 flex-shrink-0" />
  }
}
