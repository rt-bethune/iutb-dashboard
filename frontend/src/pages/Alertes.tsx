import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { useDepartment } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'
import ChartContainer from '../components/ChartContainer'
import StatCard from '../components/StatCard'
import DataTable from '../components/DataTable'
import api from '../services/api'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  User,
  BarChart3,
  Clock,
  GraduationCap,
} from 'lucide-react'
import FilterBar, { YearSelector, PeriodSelector, FilterConfig, FilterValues } from '../components/FilterBar'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

interface Alerte {
  etudiant_id: string
  etudiant_nom: string
  etudiant_prenom: string
  type_alerte: string
  niveau: 'critique' | 'attention' | 'info'
  message: string
  valeur_actuelle: number
  seuil: number
  date_detection: string
  semestre: string
  modules_concernes?: string[]
}

interface StatistiquesAlertes {
  total_alertes: number
  par_niveau: Record<string, number>
  par_type: Record<string, number>
  evolution_semaine: Array<{ semaine: string; nouvelles: number; resolues: number }>
}

const NIVEAU_COLORS = {
  critique: { bg: 'bg-red-100', text: 'text-red-800', icon: AlertCircle },
  attention: { bg: 'bg-orange-100', text: 'text-orange-800', icon: AlertTriangle },
  info: { bg: 'bg-blue-100', text: 'text-blue-800', icon: Info },
}

const TYPE_LABELS: Record<string, string> = {
  difficulte_academique: 'Difficulté académique',
  assiduite: 'Assiduité',
  decrochage: 'Risque décrochage',
  progression_negative: 'Progression négative',
  retard_travaux: 'Retard travaux',
  absence_evaluation: 'Absence évaluation',
}

const PIE_COLORS = ['#ef4444', '#f97316', '#3b82f6']

export default function AlertesPage() {
  const { department } = useDepartment()
  const { checkPermission } = useAuth()
  const [searchParams] = useSearchParams()

  const [filters, setFilters] = useState<FilterValues>({
    niveau: searchParams.get('niveau') || '',
    type_alerte: searchParams.get('type_alerte') || '',
    semestre: searchParams.get('semestre') || '',
    formation: searchParams.get('formation') || '',
    modalite: searchParams.get('modalite') || '',
    search: searchParams.get('search') || '',
  })
  const [annee, setAnnee] = useState('2024-2025')
  const [periode, setPeriode] = useState('current')

  // Sync filters if URL changes
  useEffect(() => {
    const niveau = searchParams.get('niveau')
    const type = searchParams.get('type_alerte')
    if (niveau !== null || type !== null) {
      setFilters(prev => ({
        ...prev,
        niveau: niveau || prev.niveau,
        type_alerte: type || prev.type_alerte
      }))
    }
  }, [searchParams])

  const filterConfigs: FilterConfig[] = useMemo(() => [
    {
      key: 'niveau',
      label: 'Niveau',
      type: 'select',
      options: [
        { value: '', label: 'Tous les niveaux' },
        { value: 'critique', label: '🔴 Critique' },
        { value: 'attention', label: '🟠 Attention' },
        { value: 'info', label: '🟡 Info' },
      ]
    },
    {
      key: 'type_alerte',
      label: 'Type d\'alerte',
      type: 'select',
      options: [
        { value: '', label: 'Tous les types' },
        ...Object.entries(TYPE_LABELS).map(([value, label]) => ({ value, label }))
      ]
    },
    {
      key: 'semestre',
      label: 'Semestre',
      type: 'select',
      options: [
        { value: '', label: 'Tous' },
        { value: 'S1', label: 'S1' },
        { value: 'S2', label: 'S2' },
        { value: 'S3', label: 'S3' },
        { value: 'S4', label: 'S4' },
        { value: 'S5', label: 'S5' },
        { value: 'S6', label: 'S6' },
      ]
    },
    {
      key: 'formation',
      label: 'Formation',
      type: 'select',
      options: [
        { value: '', label: 'Toutes' },
        { value: 'BUT1', label: 'BUT1' },
        { value: 'BUT2', label: 'BUT2' },
        { value: 'BUT3', label: 'BUT3' },
        { value: 'LP', label: 'Licence Pro' },
      ]
    },
    {
      key: 'modalite',
      label: 'Modalité',
      type: 'select',
      options: [
        { value: '', label: 'Toutes' },
        { value: 'FI', label: 'Initial' },
        { value: 'FA', label: 'Alternance' },
      ]
    },
    {
      key: 'search',
      label: 'Recherche',
      type: 'search',
      placeholder: 'Nom ou prénom...'
    }
  ], [])

  const canView = checkPermission(department, 'can_view_scolarite')

  const queryParams = useMemo(() => ({
    ...filters,
    annee,
    periode
  }), [filters, annee, periode])

  // Fetch alertes
  const { data: alertes, isLoading: alertesLoading } = useQuery({
    queryKey: ['alertes', department, queryParams],
    queryFn: () => api.get<Alerte[]>(`/${department}/alertes/`, { params: queryParams }).then(res => res.data),
    enabled: canView,
  })

  // Fetch statistiques
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['alertes-stats', department, queryParams],
    queryFn: () => api.get<StatistiquesAlertes>(`/${department}/alertes/statistiques`, { params: queryParams }).then(res => res.data),
    enabled: canView,
  })

  if (!canView) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-yellow-500" />
        <p className="mt-4 text-gray-600">
          Vous n'avez pas la permission d'accéder aux alertes pour ce département.
        </p>
      </div>
    )
  }

  // Prepare chart data
  const niveauChartData = stats
    ? Object.entries(stats.par_niveau).map(([niveau, count]) => ({
      name: niveau.charAt(0).toUpperCase() + niveau.slice(1),
      value: count,
    }))
    : []

  const typeChartData = stats
    ? Object.entries(stats.par_type).map(([type, count]) => ({
      name: TYPE_LABELS[type] || type,
      value: count,
    }))
    : []

  const columns = [
    {
      key: 'niveau',
      header: 'Niveau',
      render: (row: Alerte) => {
        const { bg, text, icon: Icon } = NIVEAU_COLORS[row.niveau]
        return (
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
            <Icon className="h-4 w-4 mr-1" />
            {row.niveau}
          </span>
        )
      },
    },
    {
      key: 'etudiant',
      header: 'Étudiant',
      render: (row: Alerte) => (
        <a
          href={`/alertes/etudiant/${row.etudiant_id}`}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          {row.etudiant_nom} {row.etudiant_prenom}
        </a>
      ),
    },
    {
      key: 'type_alerte',
      header: 'Type',
      render: (row: Alerte) => TYPE_LABELS[row.type_alerte] || row.type_alerte,
    },
    {
      key: 'message',
      header: 'Message',
    },
    {
      key: 'semestre',
      header: 'Semestre',
    },
    {
      key: 'date_detection',
      header: 'Date détection',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alertes Étudiants</h1>
          <p className="text-gray-500">
            Suivi des étudiants en difficulté - Département {department}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <PeriodSelector value={periode} onChange={setPeriode} />
          <YearSelector value={annee} onChange={setAnnee} />
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar
        filters={filterConfigs}
        values={filters}
        onChange={setFilters}
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total alertes"
          value={stats?.total_alertes || 0}
          icon={<AlertTriangle className="h-6 w-6" />}
          loading={statsLoading}
        />
        <StatCard
          title="Critiques"
          value={stats?.par_niveau?.critique || 0}
          icon={<AlertCircle className="h-6 w-6" />}
          color="red"
          loading={statsLoading}
        />
        <StatCard
          title="Attention"
          value={stats?.par_niveau?.attention || 0}
          icon={<AlertTriangle className="h-6 w-6" />}
          color="orange"
          loading={statsLoading}
        />
        <StatCard
          title="Info"
          value={stats?.par_niveau?.info || 0}
          icon={<Info className="h-6 w-6" />}
          color="blue"
          loading={statsLoading}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChartContainer title="Répartition par niveau" loading={statsLoading}>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={niveauChartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {niveauChartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer title="Répartition par type" loading={statsLoading}>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={typeChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Quick access buttons */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <a
          href="/alertes/etudiants-en-difficulte"
          className="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <GraduationCap className="h-8 w-8 text-red-500 mr-3" />
          <div>
            <p className="font-medium">En difficulté</p>
            <p className="text-sm text-gray-500">Moyenne &lt; 8</p>
          </div>
        </a>
        <a
          href="/alertes/etudiants-absents"
          className="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <Clock className="h-8 w-8 text-orange-500 mr-3" />
          <div>
            <p className="font-medium">Absentéisme</p>
            <p className="text-sm text-gray-500">&gt; 15% absences</p>
          </div>
        </a>
        <a
          href="/alertes/etudiants-risque-decrochage"
          className="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <AlertTriangle className="h-8 w-8 text-red-600 mr-3" />
          <div>
            <p className="font-medium">Risque décrochage</p>
            <p className="text-sm text-gray-500">Score &gt; 0.6</p>
          </div>
        </a>
        <a
          href="/alertes/felicitations"
          className="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <BarChart3 className="h-8 w-8 text-green-500 mr-3" />
          <div>
            <p className="font-medium">Félicitations</p>
            <p className="text-sm text-gray-500">Top 10%</p>
          </div>
        </a>
      </div>


      {/* Alerts table */}
      <ChartContainer title="Liste des alertes" loading={alertesLoading} height="h-auto">
        <DataTable
          columns={columns}
          data={alertes || []}
          emptyMessage="Aucune alerte pour les filtres sélectionnés"
        />
      </ChartContainer>
    </div>
  )
}
