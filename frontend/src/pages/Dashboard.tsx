import { useQuery } from '@tanstack/react-query'
import { GraduationCap, Users, Wallet, Calendar, TrendingUp } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import { scolariteApi, recrutementApi, budgetApi, edtApi } from '@/services/api'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Dashboard() {
  const { data: scolarite } = useQuery({
    queryKey: ['scolarite', 'indicators'],
    queryFn: scolariteApi.getIndicators,
  })

  const { data: recrutement } = useQuery({
    queryKey: ['recrutement', 'indicators'],
    queryFn: () => recrutementApi.getIndicators(),
  })

  const { data: budget } = useQuery({
    queryKey: ['budget', 'indicators'],
    queryFn: () => budgetApi.getIndicators(),
  })

  const { data: edt } = useQuery({
    queryKey: ['edt', 'indicators'],
    queryFn: () => edtApi.getIndicators(),
  })

  // Prepare chart data
  const effectifsData = scolarite?.evolution_effectifs 
    ? Object.entries(scolarite.evolution_effectifs).map(([year, count]) => ({
        annee: year,
        effectif: count
      }))
    : []

  const formationsData = scolarite?.etudiants_par_formation
    ? Object.entries(scolarite.etudiants_par_formation).map(([name, value]) => ({
        name,
        value
      }))
    : []

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-gray-500 mt-1">Vue d'ensemble des indicateurs du département</p>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Étudiants"
          value={scolarite?.total_etudiants ?? '-'}
          subtitle="Tous semestres"
          change={5.6}
          changeLabel="vs année précédente"
          icon={<GraduationCap className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Candidatures"
          value={recrutement?.total_candidats ?? '-'}
          subtitle={`${recrutement?.candidats_confirmes ?? 0} confirmés`}
          change={3.8}
          changeLabel="vs année précédente"
          icon={<Users className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Budget disponible"
          value={budget ? `${(budget.total_disponible / 1000).toFixed(0)}k€` : '-'}
          subtitle={`Sur ${budget ? (budget.budget_total / 1000).toFixed(0) : 0}k€ total`}
          icon={<Wallet className="w-6 h-6" />}
          color="yellow"
        />
        <StatCard
          title="Heures totales"
          value={edt?.total_heures ?? '-'}
          subtitle={`${edt?.total_heures_complementaires ?? 0}h complémentaires`}
          icon={<Calendar className="w-6 h-6" />}
          color="purple"
        />
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Taux de réussite"
          value={scolarite ? `${scolarite.taux_reussite_global.toFixed(1)}%` : '-'}
          subtitle="Global tous semestres"
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
        <StatCard
          title="Taux d'acceptation"
          value={recrutement ? `${(recrutement.taux_acceptation * 100).toFixed(1)}%` : '-'}
          subtitle="Parcoursup"
          color="blue"
        />
        <StatCard
          title="Taux d'exécution budget"
          value={budget ? `${(budget.taux_execution * 100).toFixed(1)}%` : '-'}
          subtitle="Payé sur budget total"
          color="yellow"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer 
          title="Évolution des effectifs"
          subtitle="Nombre d'étudiants par année"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={effectifsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="annee" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="effectif" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer
          title="Répartition par formation"
          subtitle="Étudiants par filière"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={formationsData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                labelLine={false}
              >
                {formationsData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Quick tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top modules */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Modules - Résultats</h3>
          <div className="space-y-3">
            {scolarite?.modules_stats.slice(0, 5).map((module: { code: string; nom: string; moyenne: number; taux_reussite: number }) => (
              <div key={module.code} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{module.code}</p>
                  <p className="text-sm text-gray-500">{module.nom}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">{module.moyenne.toFixed(1)}</p>
                  <p className="text-sm text-gray-500">{module.taux_reussite.toFixed(0)}% réussite</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Budget categories */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget par catégorie</h3>
          <div className="space-y-3">
            {budget?.par_categorie.map((ligne: { categorie: string; budget_initial: number; paye: number }, idx: number) => (
              <div key={ligne.categorie} className="flex items-center gap-4">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                />
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {ligne.categorie}
                    </span>
                    <span className="text-sm text-gray-500">
                      {(ligne.paye / 1000).toFixed(0)}k€ / {(ligne.budget_initial / 1000).toFixed(0)}k€
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full transition-all"
                      style={{ 
                        width: `${(ligne.paye / ligne.budget_initial) * 100}%`,
                        backgroundColor: COLORS[idx % COLORS.length]
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
