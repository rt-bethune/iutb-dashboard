import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users, UserCheck, TrendingUp, MapPin, AlertCircle, Settings, Calendar } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import DataTable from '@/components/DataTable'
import { adminRecrutementApi } from '@/services/api'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']

export default function Recrutement() {
  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined)

  // Fetch available years (campagnes)
  const { data: campagnes } = useQuery({
    queryKey: ['recrutement', 'campagnes'],
    queryFn: () => adminRecrutementApi.getCampagnes(),
  })

  const availableYears = (campagnes ?? []).map((c: { annee: number }) => c.annee).sort((a: number, b: number) => b - a)

  const { data: indicators, isLoading } = useQuery({
    queryKey: ['recrutement', 'indicators', selectedYear],
    queryFn: () => adminRecrutementApi.getIndicators(selectedYear),
  })

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Chargement...</div>
  }

  // Empty state - no data in database
  if (!indicators || indicators.total_candidats === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Recrutement</h1>
          <p className="text-gray-500 mt-1">Analyse des candidatures Parcoursup</p>
        </div>
        <div className="card flex flex-col items-center justify-center py-12">
          <AlertCircle className="w-16 h-16 text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Aucune donnée disponible</h2>
          <p className="text-gray-500 mb-6 text-center max-w-md">
            Les données Parcoursup n'ont pas encore été importées. 
            Utilisez l'interface d'administration pour ajouter des campagnes et des candidats.
          </p>
          <Link 
            to="/admin/recrutement" 
            className="btn-primary flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Gérer les données Parcoursup
          </Link>
        </div>
      </div>
    )
  }

  // Prepare chart data
  const bacData = indicators?.par_type_bac
    ? Object.entries(indicators.par_type_bac).map(([name, value]) => ({ name, value }))
    : []

  const origineData = indicators?.par_origine
    ? Object.entries(indicators.par_origine)
        .sort((a, b) => (b[1] as number) - (a[1] as number))
        .slice(0, 8)
        .map(([name, value]) => ({ name, value: value as number }))
    : []

  const mentionData = indicators?.par_mention
    ? Object.entries(indicators.par_mention).map(([name, value]) => ({ name, value }))
    : []

  // Evolution data from indicators (if available) - transform to chart format
  const evolutionData = (indicators?.evolution ?? []).map((e: any) => ({
    annee: e.annee,
    voeux: e.nb_voeux,
    acceptes: e.nb_acceptes,
    confirmes: e.nb_confirmes,
  }))

  const lyceeColumns = [
    { key: 'lycee', header: 'Lycée' },
    { 
      key: 'count', 
      header: 'Candidats',
      align: 'right' as const,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page header with year selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Recrutement</h1>
          <p className="text-gray-500 mt-1">
            Analyse des candidatures Parcoursup - Année {indicators?.annee_courante}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-gray-400" />
          <select
            value={selectedYear ?? ''}
            onChange={(e) => setSelectedYear(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">Année la plus récente</option>
            {availableYears.map((year: number) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total candidatures"
          value={indicators?.total_candidats ?? 0}
          icon={<Users className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Acceptés"
          value={indicators?.candidats_acceptes ?? 0}
          subtitle={`${((indicators?.taux_acceptation ?? 0) * 100).toFixed(1)}% du total`}
          icon={<UserCheck className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Confirmés"
          value={indicators?.candidats_confirmes ?? 0}
          subtitle={`${((indicators?.taux_confirmation ?? 0) * 100).toFixed(1)}% des acceptés`}
          icon={<TrendingUp className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="Taux de remplissage"
          value={`${indicators?.candidats_confirmes ?? 0}/52`}
          subtitle="Places pourvues"
          color="yellow"
        />
      </div>

      {/* Evolution chart */}
      <ChartContainer
        title="Évolution du recrutement"
        subtitle="Nombre de candidatures et admissions sur plusieurs années"
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={evolutionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="annee" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} />
            <Tooltip />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="voeux" 
              name="Vœux" 
              stackId="1"
              stroke="#3b82f6" 
              fill="#93c5fd" 
            />
            <Area 
              type="monotone" 
              dataKey="acceptes" 
              name="Acceptés" 
              stackId="2"
              stroke="#10b981" 
              fill="#6ee7b7" 
            />
            <Area 
              type="monotone" 
              dataKey="confirmes" 
              name="Confirmés" 
              stackId="3"
              stroke="#8b5cf6" 
              fill="#c4b5fd" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartContainer>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer
          title="Répartition par type de bac"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={bacData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {bacData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend layout="vertical" align="right" verticalAlign="middle" />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer
          title="Origine géographique"
          subtitle="Top départements"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={origineData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" stroke="#6b7280" fontSize={12} />
              <YAxis type="category" dataKey="name" stroke="#6b7280" fontSize={11} width={100} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Mention and lycees */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer
          title="Répartition par mention au bac"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={mentionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-gray-500" />
            <h3 className="text-lg font-semibold text-gray-900">Top lycées d'origine</h3>
          </div>
          <DataTable 
            data={indicators?.top_lycees ?? []}
            columns={lyceeColumns}
          />
        </div>
      </div>

      {/* Funnel visualization */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Entonnoir de recrutement</h3>
        <div className="flex items-center justify-center gap-4">
          {[
            { label: 'Candidatures', value: indicators?.total_candidats ?? 0, color: 'bg-blue-500' },
            { label: 'Acceptés', value: indicators?.candidats_acceptes ?? 0, color: 'bg-green-500' },
            { label: 'Confirmés', value: indicators?.candidats_confirmes ?? 0, color: 'bg-purple-500' },
          ].map((step, idx) => (
            <div key={step.label} className="flex items-center gap-4">
              <div className="text-center">
                <div 
                  className={`${step.color} text-white rounded-lg px-6 py-4 min-w-[120px]`}
                  style={{ 
                    transform: `scale(${1 - idx * 0.1})`,
                  }}
                >
                  <div className="text-2xl font-bold">{step.value}</div>
                  <div className="text-sm opacity-90">{step.label}</div>
                </div>
              </div>
              {idx < 2 && (
                <div className="text-gray-400 text-2xl">→</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
