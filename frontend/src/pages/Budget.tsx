import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Wallet, TrendingUp, CreditCard, PiggyBank, AlertCircle, Calendar } from 'lucide-react'
import { Link } from 'react-router-dom'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, ComposedChart, Line
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import DataTable from '@/components/DataTable'
import ProgressBar from '@/components/ProgressBar'
import { adminBudgetApi } from '@/services/api'

interface CategorieItem {
  categorie: string
  budget_initial: number
  engage: number
  paye: number
  disponible: number
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('fr-FR', { 
    style: 'currency', 
    currency: 'EUR',
    maximumFractionDigits: 0
  }).format(value)
}

export default function Budget() {
  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined)

  // Fetch available years
  const { data: budgetYears } = useQuery({
    queryKey: ['budget', 'years'],
    queryFn: () => adminBudgetApi.getYears(),
  })

  const availableYears = (budgetYears ?? []).map((b: { annee: number }) => b.annee).sort((a: number, b: number) => b - a)

  const { data: indicators, isLoading } = useQuery({
    queryKey: ['budget', 'indicators', selectedYear],
    queryFn: () => adminBudgetApi.getIndicators(selectedYear),
  })

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Chargement...</div>
  }

  // Check if we have data
  const hasData = indicators && indicators.par_categorie && indicators.par_categorie.length > 0

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Budget</h1>
          <p className="text-gray-500 mt-1">Suivi budgétaire</p>
        </div>
        <div className="card text-center py-12">
          <AlertCircle className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Aucune donnée budgétaire</h3>
          <p className="text-gray-500 mb-4">
            Les données budget doivent être importées ou saisies manuellement.
          </p>
          <Link
            to="/admin/budget"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Gérer les données budget
          </Link>
        </div>
      </div>
    )
  }

  // Prepare chart data
  const categorieData = indicators?.par_categorie.map((cat: CategorieItem) => ({
    name: cat.categorie,
    budget: cat.budget_initial,
    engage: cat.engage,
    paye: cat.paye,
  })) ?? []

  const pieData = indicators?.par_categorie.map((cat: CategorieItem) => ({
    name: cat.categorie,
    value: cat.budget_initial,
  })) ?? []

  const evolutionData = indicators?.evolution_mensuelle
    ? Object.entries(indicators.evolution_mensuelle).map(([month, value]) => {
        // Calculate cumulative
        const months = Object.keys(indicators.evolution_mensuelle!).sort()
        const monthIndex = months.indexOf(month)
        const cumul = months.slice(0, monthIndex + 1).reduce((sum, m) => sum + (indicators.evolution_mensuelle![m] || 0), 0)
        return {
          mois: month.split('-')[1],
          depenses: value,
          cumul,
        }
      })
    : []

  const depenseColumns = [
    { key: 'libelle', header: 'Libellé' },
    { key: 'categorie', header: 'Catégorie' },
    { 
      key: 'montant', 
      header: 'Montant',
      align: 'right' as const,
      render: (item: Record<string, unknown>) => formatCurrency(item.montant as number)
    },
    { key: 'date', header: 'Date' },
  ]

  return (
    <div className="space-y-6">
      {/* Page header with year selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Budget</h1>
          <p className="text-gray-500 mt-1">Suivi budgétaire - Année {indicators?.annee}</p>
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
          title="Budget total"
          value={formatCurrency(indicators?.budget_total ?? 0)}
          icon={<Wallet className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Engagé"
          value={formatCurrency(indicators?.total_engage ?? 0)}
          subtitle={`${((indicators?.taux_engagement ?? 0) * 100).toFixed(1)}% du budget`}
          icon={<CreditCard className="w-6 h-6" />}
          color="yellow"
        />
        <StatCard
          title="Payé"
          value={formatCurrency(indicators?.total_paye ?? 0)}
          subtitle={`${((indicators?.taux_execution ?? 0) * 100).toFixed(1)}% exécuté`}
          icon={<TrendingUp className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Disponible"
          value={formatCurrency(indicators?.total_disponible ?? 0)}
          icon={<PiggyBank className="w-6 h-6" />}
          color="purple"
        />
      </div>

      {/* Execution gauges */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Taux d'exécution</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-600">Taux d'engagement</span>
              <span className="font-semibold">{((indicators?.taux_engagement ?? 0) * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar 
              value={(indicators?.taux_engagement ?? 0) * 100} 
              color="yellow"
              size="lg"
              showPercentage={false}
            />
            <p className="text-sm text-gray-500 mt-2">
              {formatCurrency(indicators?.total_engage ?? 0)} engagés sur {formatCurrency(indicators?.budget_total ?? 0)}
            </p>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-600">Taux d'exécution (payé)</span>
              <span className="font-semibold">{((indicators?.taux_execution ?? 0) * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar 
              value={(indicators?.taux_execution ?? 0) * 100} 
              color="green"
              size="lg"
              showPercentage={false}
            />
            <p className="text-sm text-gray-500 mt-2">
              {formatCurrency(indicators?.total_paye ?? 0)} payés sur {formatCurrency(indicators?.budget_total ?? 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer
          title="Budget par catégorie"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((_: unknown, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend layout="vertical" align="right" verticalAlign="middle" />
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer
          title="Exécution par catégorie"
          subtitle="Budget vs Engagé vs Payé"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categorieData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={12} tickFormatter={(v) => `${v/1000}k`} />
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
              <Legend />
              <Bar dataKey="budget" name="Budget" fill="#93c5fd" radius={[4, 4, 0, 0]} />
              <Bar dataKey="engage" name="Engagé" fill="#fcd34d" radius={[4, 4, 0, 0]} />
              <Bar dataKey="paye" name="Payé" fill="#6ee7b7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Evolution chart */}
      <ChartContainer
        title="Évolution mensuelle des dépenses"
        subtitle="Dépenses mensuelles et cumul"
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={evolutionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="mois" stroke="#6b7280" fontSize={12} />
            <YAxis yAxisId="left" stroke="#6b7280" fontSize={12} tickFormatter={(v) => `${v/1000}k`} />
            <YAxis yAxisId="right" orientation="right" stroke="#6b7280" fontSize={12} tickFormatter={(v) => `${v/1000}k`} />
            <Tooltip formatter={(value) => formatCurrency(value as number)} />
            <Legend />
            <Bar yAxisId="left" dataKey="depenses" name="Dépenses mensuelles" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="cumul" name="Cumul" stroke="#ef4444" strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartContainer>

      {/* Categories detail */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Détail par catégorie</h3>
        <div className="space-y-4">
          {indicators?.par_categorie.map((cat: CategorieItem, idx: number) => (
            <div key={cat.categorie} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                  />
                  <h4 className="font-semibold text-gray-900 capitalize">{cat.categorie}</h4>
                </div>
                <span className="text-sm font-medium text-gray-600">
                  {formatCurrency(cat.disponible)} disponible
                </span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                <div>
                  <span className="text-gray-500">Budget</span>
                  <p className="font-medium">{formatCurrency(cat.budget_initial)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Engagé</span>
                  <p className="font-medium text-yellow-600">{formatCurrency(cat.engage)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Payé</span>
                  <p className="font-medium text-green-600">{formatCurrency(cat.paye)}</p>
                </div>
              </div>
              <ProgressBar 
                value={cat.paye}
                max={cat.budget_initial}
                color={cat.paye / cat.budget_initial > 0.8 ? 'red' : 'green'}
                showPercentage
              />
            </div>
          ))}
        </div>
      </div>

      {/* Top expenses */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Principales dépenses</h3>
        <DataTable 
          data={indicators?.top_depenses ?? []}
          columns={depenseColumns}
        />
      </div>
    </div>
  )
}
