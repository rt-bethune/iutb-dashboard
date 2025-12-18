import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'
import ChartContainer from '../components/ChartContainer'
import StatCard from '../components/StatCard'
import DataTable from '../components/DataTable'
import api from '../services/api'
import {
  GraduationCap,
  Users,
  BarChart3,
  TrendingUp,
  TrendingDown,
  FileText,
  AlertTriangle,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'

interface TableauBord {
  department: string
  annee: string
  semestre: string
  statistiques: {
    effectif_total: number
    moyenne_promo: number
    ecart_type: number
    mediane: number
    taux_reussite: number
    taux_difficulte: number
    taux_excellence: number
  }
  taux_validation: {
    taux_global: number
    par_ue: Record<string, number>
    par_module: Record<string, number>
  }
  mentions: {
    tres_bien: number
    bien: number
    assez_bien: number
    passable: number
    insuffisant: number
    eliminatoire: number
    pourcentage_admis: number
  }
  indicateurs_cles: Record<string, { valeur: number; tendance: string; vs_annee_prec: number }>
}

interface ModuleAnalyse {
  code: string
  nom: string
  moyenne: number
  ecart_type: number
  taux_validation: number
  taux_echec: number
  alerte: boolean
  alerte_message?: string
  semestre?: string
  formation?: string
}

interface ComparaisonInterannuelle {
  annees: string[]
  moyennes: number[]
  taux_reussite: number[]
  taux_absenteisme: number[]
  effectifs: number[]
}

interface AnalyseTypeBac {
  par_type: Record<string, {
    effectif: number
    pourcentage: number
    moyenne: number
    taux_reussite: number
    taux_excellence: number
  }>
  type_meilleur: string
  type_difficulte: string
}

const MENTION_COLORS = ['#10b981', '#34d399', '#6ee7b7', '#fbbf24', '#f97316', '#ef4444']
const TREND_COLORS = { hausse: 'text-green-600', baisse: 'text-red-600', stable: 'text-gray-600' }

export default function IndicateursPage() {
  const { department } = useDepartment()
  const { checkPermission } = useAuth()
  const [semestre, setSemestre] = useState('')
  const [annee, setAnnee] = useState('2024-2025')

  const canView = checkPermission(department, 'can_view_scolarite')

  // Fetch tableau de bord
  const { data: tableau, isLoading: tableauLoading } = useQuery({
    queryKey: ['tableau-bord', department, annee, semestre],
    queryFn: () =>
      api.get<TableauBord>(`/${department}/indicateurs/tableau-bord`, {
        params: { annee, semestre: semestre || undefined },
      }).then(res => res.data),
    enabled: canView,
  })

  // Fetch modules analysis
  const { data: modules, isLoading: modulesLoading } = useQuery({
    queryKey: ['modules-analyse', department, semestre],
    queryFn: () =>
      api.get<ModuleAnalyse[]>(`/${department}/indicateurs/modules`, {
        params: { semestre: semestre || undefined, tri: 'taux_echec' },
      }).then(res => res.data),
    enabled: canView,
  })

  // Fetch comparaison interannuelle
  const { data: comparaison, isLoading: comparaisonLoading } = useQuery({
    queryKey: ['comparaison-inter', department],
    queryFn: () => api.get<ComparaisonInterannuelle>(`/${department}/indicateurs/comparaison-interannuelle`).then(res => res.data),
    enabled: canView,
  })

  // Fetch analyse type bac
  const { data: typeBac, isLoading: typeBacLoading } = useQuery({
    queryKey: ['type-bac', department, semestre],
    queryFn: () => api.get<AnalyseTypeBac>(`/${department}/indicateurs/analyse-type-bac`).then(res => res.data),
    enabled: canView,
  })

  if (!canView) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-yellow-500" />
        <p className="mt-4 text-gray-600">
          Vous n'avez pas la permission d'accéder aux indicateurs pour ce département.
        </p>
      </div>
    )
  }

  // Prepare chart data
  const mentionsData = tableau
    ? [
        { name: 'Très Bien', value: tableau.mentions.tres_bien },
        { name: 'Bien', value: tableau.mentions.bien },
        { name: 'Assez Bien', value: tableau.mentions.assez_bien },
        { name: 'Passable', value: tableau.mentions.passable },
        { name: 'Insuffisant', value: tableau.mentions.insuffisant },
        { name: 'Éliminatoire', value: tableau.mentions.eliminatoire },
      ]
    : []

  const evolutionData = comparaison
    ? comparaison.annees.map((year: string, i: number) => ({
        annee: year,
        moyenne: comparaison.moyennes[i],
        taux_reussite: (comparaison.taux_reussite[i] * 100).toFixed(1),
        effectif: comparaison.effectifs[i],
      }))
    : []

  const typeBacData = typeBac
    ? Object.entries(typeBac.par_type).map(([type, data]) => {
        const typedData = data as { taux_reussite: number; moyenne: number; effectif: number }
        return {
          type,
          moyenne: typedData.moyenne,
          effectif: typedData.effectif,
          taux_reussite: (typedData.taux_reussite * 100).toFixed(1),
        }
      })
    : []

  const validationRadarData = tableau
    ? Object.entries(tableau.taux_validation.par_ue).map(([ue, taux]) => ({
        ue,
        taux: ((taux as number) * 100).toFixed(0),
      }))
    : []

  const modulesColumns = [
    { key: 'code', header: 'Code' },
    { key: 'nom', header: 'Module' },
    { key: 'formation', header: 'Formation' },
    { key: 'semestre', header: 'Semestre' },
    {
      key: 'moyenne',
      header: 'Moyenne',
      render: (row: ModuleAnalyse) => (
        <span className={row.moyenne < 10 ? 'text-red-600 font-medium' : ''}>
          {row.moyenne.toFixed(1)}
        </span>
      ),
    },
    {
      key: 'ecart_type',
      header: 'Écart-type',
      render: (row: ModuleAnalyse) => row.ecart_type.toFixed(1),
    },
    {
      key: 'taux_echec',
      header: 'Taux échec',
      render: (row: ModuleAnalyse) => (
        <span className={row.taux_echec > 0.25 ? 'text-red-600 font-medium' : ''}>
          {(row.taux_echec * 100).toFixed(0)}%
        </span>
      ),
    },
    {
      key: 'alerte',
      header: 'Alerte',
      render: (row: ModuleAnalyse) =>
        row.alerte ? (
          <span className="text-red-600" title={row.alerte_message}>
            ⚠️
          </span>
        ) : (
          <span className="text-green-600">✓</span>
        ),
    },
  ]

  const getTrendIcon = (tendance: string) => {
    if (tendance === 'hausse') return <TrendingUp className="h-4 w-4 text-green-600" />
    if (tendance === 'baisse') return <TrendingDown className="h-4 w-4 text-red-600" />
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Indicateurs de Cohorte</h1>
          <p className="text-gray-500">
            Statistiques avancées - Département {department}
          </p>
        </div>
        <a
          href={`/api/${department}/indicateurs/rapport-semestre?annee=${annee}&semestre=${semestre || 'S1'}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <FileText className="h-5 w-5 mr-2" />
          Générer rapport
        </a>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
            <select
              value={annee}
              onChange={(e) => setAnnee(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="2024-2025">2024-2025</option>
              <option value="2023-2024">2023-2024</option>
              <option value="2022-2023">2022-2023</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Semestre</label>
            <select
              value={semestre}
              onChange={(e) => setSemestre(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Tous</option>
              <option value="S1">S1</option>
              <option value="S2">S2</option>
              <option value="S3">S3</option>
              <option value="S4">S4</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <StatCard
          title="Effectif"
          value={tableau?.statistiques.effectif_total || 0}
          icon={<Users className="h-6 w-6" />}
          loading={tableauLoading}
        />
        <StatCard
          title="Moyenne promo"
          value={tableau?.statistiques.moyenne_promo.toFixed(1) || '0'}
          suffix="/20"
          icon={<BarChart3 className="h-6 w-6" />}
          loading={tableauLoading}
        />
        <StatCard
          title="Taux réussite"
          value={tableau ? (tableau.statistiques.taux_reussite * 100).toFixed(0) : '0'}
          suffix="%"
          icon={<GraduationCap className="h-6 w-6" />}
          color="green"
          loading={tableauLoading}
        />
        <StatCard
          title="En difficulté"
          value={tableau ? (tableau.statistiques.taux_difficulte * 100).toFixed(0) : '0'}
          suffix="%"
          icon={<AlertTriangle className="h-6 w-6" />}
          color="red"
          loading={tableauLoading}
        />
        <StatCard
          title="Excellence"
          value={tableau ? (tableau.statistiques.taux_excellence * 100).toFixed(0) : '0'}
          suffix="%"
          icon={<TrendingUp className="h-6 w-6" />}
          color="green"
          loading={tableauLoading}
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Mentions distribution */}
        <ChartContainer title="Répartition des mentions" loading={tableauLoading}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={mentionsData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, value }) => `${name}: ${value}`}
                dataKey="value"
              >
                {mentionsData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={MENTION_COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* Validation par UE (Radar) */}
        <ChartContainer title="Taux de validation par UE" loading={tableauLoading}>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={validationRadarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="ue" />
              <PolarRadiusAxis domain={[0, 100]} />
              <Radar
                name="Taux validation"
                dataKey="taux"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.5}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Évolution interannuelle */}
        <ChartContainer title="Évolution interannuelle" loading={comparaisonLoading}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={evolutionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="annee" />
              <YAxis yAxisId="left" domain={[8, 14]} />
              <YAxis yAxisId="right" orientation="right" domain={[60, 100]} />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="moyenne"
                name="Moyenne"
                stroke="#3b82f6"
                strokeWidth={2}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="taux_reussite"
                name="Taux réussite (%)"
                stroke="#10b981"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* Analyse par type de bac */}
        <ChartContainer title="Réussite par type de bac" loading={typeBacLoading}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={typeBacData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="moyenne" name="Moyenne" fill="#3b82f6" />
              <Bar dataKey="taux_reussite" name="Taux réussite (%)" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Modules analysis table */}
      <ChartContainer title="Analyse par module (triés par taux d'échec)" loading={modulesLoading} height="h-auto">
        <DataTable
          columns={modulesColumns}
          data={modules || []}
          emptyMessage="Aucun module à afficher"
        />
      </ChartContainer>

      {/* Key indicators with trends */}
      {tableau?.indicateurs_cles && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Indicateurs clés vs année précédente</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(tableau.indicateurs_cles).map(([key, data]) => {
              const typedData = data as { valeur: number; tendance: string; vs_annee_prec: number }
              return (
                <div key={key} className="border rounded-lg p-4">
                  <p className="text-sm text-gray-500 capitalize">{key.replace(/_/g, ' ')}</p>
                  <div className="flex items-center mt-1">
                    <span className="text-xl font-bold">
                      {typeof typedData.valeur === 'number' && typedData.valeur < 1
                        ? (typedData.valeur * 100).toFixed(0) + '%'
                        : typedData.valeur}
                    </span>
                    <span className={`ml-2 flex items-center ${TREND_COLORS[typedData.tendance as keyof typeof TREND_COLORS]}`}>
                      {getTrendIcon(typedData.tendance)}
                      {typedData.vs_annee_prec > 0 ? '+' : ''}
                      {typeof typedData.vs_annee_prec === 'number' && Math.abs(typedData.vs_annee_prec) < 1
                        ? (typedData.vs_annee_prec * 100).toFixed(0) + '%'
                        : typedData.vs_annee_prec}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
