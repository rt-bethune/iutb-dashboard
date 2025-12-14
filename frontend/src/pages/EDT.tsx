import { useQuery } from '@tanstack/react-query'
import { Clock, Users, Building } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import DataTable from '@/components/DataTable'
import ProgressBar from '@/components/ProgressBar'
import PermissionGate from '@/components/PermissionGate'
import { edtApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'
import type { ChargeEnseignant, OccupationSalle } from '@/types'

export default function EDT() {
  const { department } = useDepartment()

  const { data: indicators, isLoading, error } = useQuery({
    queryKey: ['edt', 'indicators', department],
    queryFn: () => edtApi.getIndicators(department),
  })

  const { data: repartition } = useQuery({
    queryKey: ['edt', 'repartition', department],
    queryFn: () => edtApi.getRepartition(department),
    enabled: !!indicators,
  })

  const { data: heuresComp } = useQuery({
    queryKey: ['edt', 'heures-complementaires', department],
    queryFn: () => edtApi.getHeuresComplementaires(department),
    enabled: !!indicators,
  })

  // Handle permission errors
  if (error) {
    const axiosError = error as any
    if (axiosError?.response?.status === 403) {
      return (
        <PermissionGate domain="edt" action="view">
          <div />
        </PermissionGate>
      )
    }
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        Erreur lors du chargement des données
      </div>
    )
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Chargement...</div>
  }

  // Prepare chart data
  const typeData = repartition ? [
    { name: 'CM', value: repartition.cm?.heures ?? 0, fill: '#3b82f6' },
    { name: 'TD', value: repartition.td?.heures ?? 0, fill: '#10b981' },
    { name: 'TP', value: repartition.tp?.heures ?? 0, fill: '#f59e0b' },
  ] : []

  const chargesData = indicators?.charges_enseignants.map((c: ChargeEnseignant) => ({
    name: c.enseignant.split(' ')[0],
    cm: c.heures_cm,
    td: c.heures_td,
    tp: c.heures_tp,
    hc: c.heures_complementaires,
  })) ?? []

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _occupationData = indicators?.occupation_salles.map((s: OccupationSalle) => ({
    salle: s.salle,
    occupation: (s.taux_occupation * 100).toFixed(1),
  })) ?? []

  const enseignantColumns = [
    { key: 'enseignant', header: 'Enseignant' },
    { 
      key: 'heures_cm', 
      header: 'CM',
      align: 'right' as const,
      render: (item: ChargeEnseignant) => `${item.heures_cm}h`
    },
    { 
      key: 'heures_td', 
      header: 'TD',
      align: 'right' as const,
      render: (item: ChargeEnseignant) => `${item.heures_td}h`
    },
    { 
      key: 'heures_tp', 
      header: 'TP',
      align: 'right' as const,
      render: (item: ChargeEnseignant) => `${item.heures_tp}h`
    },
    { 
      key: 'total_heures', 
      header: 'Total éq. TD',
      align: 'right' as const,
      render: (item: ChargeEnseignant) => (
        <span className="font-semibold">{item.total_heures.toFixed(0)}h</span>
      )
    },
    { 
      key: 'heures_complementaires', 
      header: 'HC',
      align: 'right' as const,
      render: (item: ChargeEnseignant) => (
        <span className={item.heures_complementaires > 0 ? 'text-orange-600 font-medium' : ''}>
          {item.heures_complementaires > 0 ? `+${item.heures_complementaires.toFixed(0)}h` : '-'}
        </span>
      )
    },
  ]

  const salleColumns = [
    { key: 'salle', header: 'Salle' },
    { 
      key: 'capacite', 
      header: 'Capacité',
      align: 'right' as const,
    },
    { 
      key: 'heures_occupees', 
      header: 'Heures occupées',
      align: 'right' as const,
      render: (item: OccupationSalle) => `${item.heures_occupees}h`
    },
    { 
      key: 'taux_occupation', 
      header: 'Occupation',
      align: 'right' as const,
      render: (item: OccupationSalle) => (
        <div className="flex items-center gap-2 justify-end">
          <ProgressBar 
            value={item.taux_occupation * 100} 
            showPercentage={false}
            size="sm"
            color={item.taux_occupation > 0.7 ? 'green' : item.taux_occupation > 0.4 ? 'yellow' : 'red'}
          />
          <span className="w-12 text-right">{(item.taux_occupation * 100).toFixed(0)}%</span>
        </div>
      )
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Emploi du temps</h1>
        <p className="text-gray-500 mt-1">
          Charges et occupation - {indicators?.periode_debut} au {indicators?.periode_fin}
        </p>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Heures totales"
          value={`${indicators?.total_heures ?? 0}h`}
          icon={<Clock className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Heures complémentaires"
          value={`${indicators?.total_heures_complementaires ?? 0}h`}
          subtitle={`${heuresComp?.enseignants ?? 0} enseignants concernés`}
          icon={<Users className="w-6 h-6" />}
          color="yellow"
        />
        <StatCard
          title="Enseignants"
          value={indicators?.charges_enseignants.length ?? 0}
          icon={<Users className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Occupation moyenne"
          value={`${((indicators?.taux_occupation_moyen ?? 0) * 100).toFixed(0)}%`}
          subtitle="des salles"
          icon={<Building className="w-6 h-6" />}
          color="purple"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer
          title="Répartition CM / TD / TP"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={typeData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}h`}
              >
                {typeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Legend />
              <Tooltip formatter={(value) => `${value}h`} />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer
          title="Charges par enseignant"
          subtitle="Répartition CM/TD/TP"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chargesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="cm" name="CM" stackId="a" fill="#3b82f6" />
              <Bar dataKey="td" name="TD" stackId="a" fill="#10b981" />
              <Bar dataKey="tp" name="TP" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* Hours summary */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Résumé des heures</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="font-medium text-blue-900">Cours Magistraux (CM)</span>
            </div>
            <p className="text-3xl font-bold text-blue-700">{indicators?.heures_cm ?? 0}h</p>
            <p className="text-sm text-blue-600 mt-1">
              {((indicators?.heures_cm ?? 0) / (indicators?.total_heures || 1) * 100).toFixed(0)}% du total
            </p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="font-medium text-green-900">Travaux Dirigés (TD)</span>
            </div>
            <p className="text-3xl font-bold text-green-700">{indicators?.heures_td ?? 0}h</p>
            <p className="text-sm text-green-600 mt-1">
              {((indicators?.heures_td ?? 0) / (indicators?.total_heures || 1) * 100).toFixed(0)}% du total
            </p>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span className="font-medium text-yellow-900">Travaux Pratiques (TP)</span>
            </div>
            <p className="text-3xl font-bold text-yellow-700">{indicators?.heures_tp ?? 0}h</p>
            <p className="text-sm text-yellow-600 mt-1">
              {((indicators?.heures_tp ?? 0) / (indicators?.total_heures || 1) * 100).toFixed(0)}% du total
            </p>
          </div>
        </div>
      </div>

      {/* Teachers table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Charges enseignants</h3>
        <DataTable 
          data={indicators?.charges_enseignants ?? []}
          columns={enseignantColumns}
        />
      </div>

      {/* Heures complémentaires detail */}
      {heuresComp && heuresComp.detail && heuresComp.detail.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Heures complémentaires</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {heuresComp.detail.map((item: { enseignant: string; heures: number }) => (
              <div key={item.enseignant} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <span className="font-medium text-gray-900">{item.enseignant}</span>
                <span className="text-orange-600 font-semibold">+{item.heures.toFixed(0)}h</span>
              </div>
            ))}
          </div>
          <div className="mt-4 p-4 bg-gray-100 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="font-medium text-gray-700">Total heures complémentaires</span>
              <span className="text-xl font-bold text-orange-600">{heuresComp.total.toFixed(0)}h</span>
            </div>
          </div>
        </div>
      )}

      {/* Rooms table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Occupation des salles</h3>
        <DataTable 
          data={indicators?.occupation_salles ?? []}
          columns={salleColumns}
        />
      </div>
    </div>
  )
}
