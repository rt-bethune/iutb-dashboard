import { useQuery } from '@tanstack/react-query'
import { GraduationCap, Users, Wallet, Calendar, TrendingUp } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LabelList
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import { scolariteApi, recrutementApi, budgetApi, edtApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Dashboard() {
  const { department } = useDepartment()
  const { checkPermission } = useAuth()

  // Check permissions for each domain
  const canViewScolarite = checkPermission(department, 'can_view_scolarite')
  const canViewRecrutement = checkPermission(department, 'can_view_recrutement')
  const canViewBudget = checkPermission(department, 'can_view_budget')
  const canViewEdt = checkPermission(department, 'can_view_edt')

  const { data: scolarite } = useQuery({
    queryKey: ['scolarite', 'indicators', department],
    queryFn: () => scolariteApi.getIndicators(department),
    enabled: canViewScolarite,
  })

  const { data: recrutement } = useQuery({
    queryKey: ['recrutement', 'indicators', department],
    queryFn: () => recrutementApi.getIndicators(department),
    enabled: canViewRecrutement,
  })

  const { data: budget } = useQuery({
    queryKey: ['budget', 'indicators', department],
    queryFn: () => budgetApi.getIndicators(department),
    enabled: canViewBudget,
  })

  const { data: edt } = useQuery({
    queryKey: ['edt', 'indicators', department],
    queryFn: () => edtApi.getIndicators(department),
    enabled: canViewEdt,
  })

  // Prepare chart data
  
  // Build formation color map first
  const formationColorMap: Record<string, string> = {}
  if (scolarite?.etudiants_par_formation) {
    Object.keys(scolarite.etudiants_par_formation).forEach((formation, index) => {
      formationColorMap[formation] = COLORS[index % COLORS.length]
    })
  }

  // Helper to find which formation a semester belongs to
  const getFormationFromSemesterName = (semName: string): string => {
    const semLower = semName.toLowerCase()
    const isApprentissage = semLower.includes('apprentissage')
    const formations = Object.keys(formationColorMap)
    
    if (isApprentissage) {
      const appFormation = formations.find(f => f.toLowerCase().includes('apprentissage'))
      if (appFormation) return appFormation
    } else {
      const nonAppFormation = formations.find(f => !f.toLowerCase().includes('apprentissage'))
      if (nonAppFormation) return nonAppFormation
    }
    return formations[0] || ''
  }

  const semestreData = scolarite?.etudiants_par_semestre
    ? Object.entries(scolarite.etudiants_par_semestre).map(([sem, count]) => {
        // Extract short semester name
        const match = sem.match(/semestre\s*(\d+)/i)
        const semNum = match ? match[1] : '?'
        const isApprentissage = sem.toLowerCase().includes('apprentissage')
        const shortName = isApprentissage ? `S${semNum} App` : `S${semNum}`
        const formation = getFormationFromSemesterName(sem)
        return {
          name: shortName,
          fullName: sem,
          value: count,
          color: formationColorMap[formation] || COLORS[0]
        }
      })
    : []

  const typeBacData = recrutement?.par_type_bac
    ? Object.entries(recrutement.par_type_bac).map(([name, value]) => ({
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
        {canViewScolarite && (
          <StatCard
            title="Étudiants"
            value={scolarite?.total_etudiants ?? '-'}
            subtitle="Tous semestres"
            change={5.6}
            changeLabel="vs année précédente"
            icon={<GraduationCap className="w-6 h-6" />}
            color="blue"
          />
        )}
        {canViewRecrutement && (
          <StatCard
            title="Candidatures"
            value={recrutement?.total_candidats ?? '-'}
            subtitle={`${recrutement?.candidats_confirmes ?? 0} confirmés`}
            change={3.8}
            changeLabel="vs année précédente"
            icon={<Users className="w-6 h-6" />}
            color="green"
          />
        )}
        {canViewBudget && (
          <StatCard
            title="Budget disponible"
            value={budget ? `${(budget.total_disponible / 1000).toFixed(0)}k€` : '-'}
            subtitle={`Sur ${budget ? (budget.budget_total / 1000).toFixed(0) : 0}k€ total`}
            icon={<Wallet className="w-6 h-6" />}
            color="yellow"
          />
        )}
        {canViewEdt && (
          <StatCard
            title="Heures totales"
            value={edt?.total_heures ?? '-'}
            subtitle={`${edt?.total_heures_complementaires ?? 0}h complémentaires`}
            icon={<Calendar className="w-6 h-6" />}
            color="purple"
          />
        )}
      </div>

      {/* Secondary stats */}
      {(canViewScolarite || canViewRecrutement || canViewBudget) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {canViewScolarite && (
            <StatCard
              title="Taux de réussite"
              value={scolarite ? `${scolarite.taux_reussite_global.toFixed(1)}%` : '-'}
              subtitle="Global tous semestres"
              icon={<TrendingUp className="w-5 h-5" />}
              color="green"
            />
          )}
          {canViewRecrutement && (
            <StatCard
              title="Taux d'acceptation"
              value={recrutement ? `${(recrutement.taux_acceptation * 100).toFixed(1)}%` : '-'}
              subtitle="Parcoursup"
              color="blue"
            />
          )}
          {canViewBudget && (
            <StatCard
              title="Taux d'exécution budget"
              value={budget ? `${(budget.taux_execution * 100).toFixed(1)}%` : '-'}
              subtitle="Payé sur budget total"
              color="yellow"
            />
          )}
        </div>
      )}

      {/* Charts */}
      {(canViewScolarite || canViewRecrutement) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {canViewScolarite && (
            <ChartContainer 
              title="Répartition par semestre"
              subtitle="Étudiants par semestre"
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={semestreData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                  <YAxis stroke="#6b7280" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number, _name: string, props: { payload: { fullName: string } }) => [
                      `${value} étudiants`, 
                      props.payload.fullName
                    ]}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                    {semestreData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                    <LabelList dataKey="value" position="top" fill="#374151" fontSize={12} fontWeight={600} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}

          {canViewRecrutement && (
            <ChartContainer
              title="Répartition par type de bac"
              subtitle="Candidats par filière de baccalauréat"
            >
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={typeBacData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={false}
                  >
                    {typeBacData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [`${value} candidats`, 'Effectif']} />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}
        </div>
      )}

      {/* Quick tables */}
      {(canViewScolarite || canViewBudget) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top modules */}
          {canViewScolarite && (
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
          )}

          {/* Budget categories */}
          {canViewBudget && (
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
          )}
        </div>
      )}
    </div>
  )
}
