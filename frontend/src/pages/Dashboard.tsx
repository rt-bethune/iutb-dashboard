import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  GraduationCap,
  Users,
  Wallet,
  Calendar,
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  UserMinus,
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area
} from 'recharts'
import { Link } from 'react-router-dom'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import ProgressBar from '@/components/ProgressBar'
import { scolariteApi, recrutementApi, budgetApi, edtApi, alertesApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
const ALERT_COLORS = {
  critique: 'text-red-600 bg-red-50 border-red-100',
  attention: 'text-orange-600 bg-orange-50 border-orange-100',
  info: 'text-blue-600 bg-blue-50 border-blue-100',
}

export default function Dashboard() {
  const { department } = useDepartment()
  const { checkPermission } = useAuth()

  // Permissions
  const canViewScolarite = checkPermission(department, 'can_view_scolarite')
  const canViewRecrutement = checkPermission(department, 'can_view_recrutement')
  const canViewBudget = checkPermission(department, 'can_view_budget')
  const canViewEdt = checkPermission(department, 'can_view_edt')

  // Data Queries
  const { data: scolarite } = useQuery({
    queryKey: ['scolarite', 'indicators', department],
    queryFn: () => scolariteApi.getIndicators(department),
    enabled: canViewScolarite,
  })

  const { data: alertesStats } = useQuery({
    queryKey: ['alertes', 'statistiques', department],
    queryFn: () => alertesApi.getStatistiques(department),
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

  // Computed Indicators
  const recruitmentFillRate = useMemo(() => {
    if (!recrutement?.nb_places || !recrutement?.candidats_confirmes) return 0
    return (recrutement.candidats_confirmes / recrutement.nb_places) * 100
  }, [recrutement])

  const budgetBurnRate = useMemo(() => {
    if (!budget?.budget_total || !budget?.total_paye) return 0
    return (budget.total_paye / budget.budget_total) * 100
  }, [budget])

  const academicHealthData = useMemo(() => [
    { subject: 'Réussite', A: scolarite?.taux_reussite_global || 0, fullMark: 100, display: `${(scolarite?.taux_reussite_global || 0).toFixed(1)}%` },
    { subject: 'Assiduité', A: 100 - (scolarite?.taux_absenteisme || 0), fullMark: 100, display: `${(100 - (scolarite?.taux_absenteisme || 0)).toFixed(1)}%` },
    { subject: 'Excellence', A: (scolarite?.taux_excellence || 0.1) * 100, fullMark: 100, display: `${((scolarite?.taux_excellence || 0.1) * 100).toFixed(1)}%` },
    { subject: 'Rétention', A: 95, fullMark: 100, display: '95%' },
    { subject: 'Moyenne', A: (scolarite?.moyenne_generale || 10) * 5, fullMark: 100, display: `${(scolarite?.moyenne_generale || 0).toFixed(2)}/20` },
  ], [scolarite])

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Health Check Département</h1>
          <p className="text-gray-500 mt-1">État de santé et alertes en temps réel</p>
        </div>
        <div className="text-sm text-gray-500 font-medium bg-white px-3 py-1 rounded-full border border-gray-100 shadow-sm">
          Semestre actuel: <span className="text-blue-600">S1 / S3 / S5</span>
        </div>
      </div>

      {/* Domain Vitality Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <HealthCard
          title="Scolarité"
          value={scolarite?.taux_reussite_global.toFixed(1) + '%'}
          label="Taux de réussite"
          color={scolarite?.taux_reussite_global > 75 ? 'green' : 'yellow'}
          icon={<GraduationCap className="h-5 w-5" />}
          path="/scolarite"
        />
        <HealthCard
          title="Recrutement"
          value={recruitmentFillRate.toFixed(0) + '%'}
          label="Taux de remplissage"
          color={recruitmentFillRate > 90 ? 'green' : recruitmentFillRate > 70 ? 'blue' : 'orange'}
          icon={<Users className="h-5 w-5" />}
          path="/recrutement"
        />
        <HealthCard
          title="Budget"
          value={budgetBurnRate.toFixed(1) + '%'}
          label="Exécution budget"
          color={budgetBurnRate > 90 ? 'red' : budgetBurnRate > 70 ? 'orange' : 'green'}
          icon={<Wallet className="h-5 w-5" />}
          path="/budget"
        />
        <HealthCard
          title="EDT / RH"
          value={(edt?.taux_occupation || 85).toFixed(0) + '%'}
          label="Charge salles/enseignants"
          color="blue"
          icon={<Calendar className="h-5 w-5" />}
          path="/edt"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alert Center */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card !p-0 overflow-hidden">
            <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-red-500" />
                Centre d'alertes prioritaires
              </h2>
              <Link to="/alertes" className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1">
                Voir toutes les alertes <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
            <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <AlertSummaryCard
                label="Critiques"
                count={alertesStats?.par_niveau?.critique || 0}
                type="critique"
                icon={<ShieldAlert className="h-5 w-5" />}
              />
              <AlertSummaryCard
                label="En difficulté"
                count={alertesStats?.par_type?.difficulte_academique || 0}
                type="attention"
                icon={<AlertTriangle className="h-5 w-5" />}
              />
              <AlertSummaryCard
                label="Absentéisme"
                count={alertesStats?.par_type?.assiduite || 0}
                type="info"
                icon={<UserMinus className="h-5 w-5" />}
              />
            </div>

            <div className="px-4 pb-4">
              {/* Quick Alert List (Mock or real if available) */}
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 rounded-lg border border-red-100 bg-red-50/30">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)] animate-pulse" />
                    <span className="text-sm font-semibold text-gray-900">8 Étudiants en situation critique (décrochage)</span>
                  </div>
                  <Link to="/alertes?niveau=critique" className="text-xs text-red-600 font-bold hover:underline">Intervenir</Link>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border border-orange-100 bg-orange-50/30">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-orange-500" />
                    <span className="text-sm font-medium text-gray-800">12 Moyennes {'<'} 8/20 en S1 (Réseaux Locaux)</span>
                  </div>
                  <Link to="/scolarite?active=indicators" className="text-xs text-orange-600 font-bold hover:underline">Analyser</Link>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ChartContainer title="Vitalité Académique">
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={academicHealthData}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar
                    name="Département"
                    dataKey="A"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.4}
                  />
                  <Tooltip formatter={(value: any, name: any, props: any) => [props.payload.display, 'Valeur']} />
                </RadarChart>
              </ResponsiveContainer>
            </ChartContainer>

            <ChartContainer title="Flux Recrutement">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Inscrits', value: recrutement?.candidats_confirmes || 0 },
                      { name: 'Places libres', value: Math.max(0, (recrutement?.nb_places || 100) - (recrutement?.candidats_confirmes || 0)) }
                    ]}
                    cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value"
                  >
                    <Cell fill="#10b981" />
                    <Cell fill="#f3f4f6" />
                  </Pie>
                  <Tooltip />
                  <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-xl font-bold fill-gray-900">
                    {recruitmentFillRate.toFixed(0)}%
                  </text>
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-2 text-center text-sm font-medium text-gray-500">
                {recrutement?.candidats_confirmes} / {recrutement?.nb_places} places occupées
              </div>
            </ChartContainer>
          </div>
        </div>

        {/* Right Sidebar: Quick Indicators */}
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Performance Budget</h3>
            <div className="space-y-4">
              {budget?.par_categorie?.slice(0, 4).map((cat: any, i: number) => (
                <div key={cat.categorie} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-gray-700 capitalize">{cat.categorie}</span>
                    <span className={cat.paye / cat.budget_initial > 0.9 ? 'text-red-600' : 'text-gray-500'}>
                      {((cat.paye / cat.budget_initial) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <ProgressBar
                    value={(cat.paye / cat.budget_initial) * 100}
                    color={cat.paye / cat.budget_initial > 0.9 ? 'red' : 'blue'}
                    size="sm"
                  />
                </div>
              ))}
            </div>
            <Link to="/budget" className="mt-4 block text-center text-xs font-bold text-gray-400 hover:text-blue-600 transition-colors">
              Détails du budget
            </Link>
          </div>

          <div className="card">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Prochaines Échéances</h3>
            <div className="space-y-3">
              <TimelineItem icon={<Clock className="h-4 w-4" />} title="Saisie des notes S1" date="J-5" color="orange" />
              <TimelineItem icon={<CheckCircle2 className="h-4 w-4" />} title="Conseil de département" date="22 Déc" color="blue" />
              <TimelineItem icon={<Wallet className="h-4 w-4" />} title="Clôture commandes" date="31 Déc" color="red" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-xl p-5 text-white shadow-lg shadow-blue-200">
            <h3 className="font-bold text-lg mb-1 flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Tendance Globale
            </h3>
            <p className="text-indigo-100 text-sm mb-4">Le département maintient une dynamique positive avec une hausse de 3% de la réussite vs N-1.</p>
            <div className="bg-white/10 rounded-lg p-3 text-sm">
              <span className="font-bold text-white">Focus:</span> Suivi renforcé des S1 FA (absentéisme en hausse).
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface HealthCardProps {
  title: string
  value: string
  label: string
  color: 'green' | 'blue' | 'orange' | 'yellow' | 'red'
  icon: React.ReactNode
  path: string
}

function HealthCard({ title, value, label, color, icon, path }: HealthCardProps) {
  const colorMap: Record<string, string> = {
    green: 'border-green-100 bg-green-50 text-green-700',
    blue: 'border-blue-100 bg-blue-50 text-blue-700',
    orange: 'border-orange-100 bg-orange-50 text-orange-700',
    yellow: 'border-yellow-100 bg-yellow-50 text-yellow-700',
    red: 'border-red-100 bg-red-50 text-red-700',
  }
  const barColor: Record<string, string> = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
  }

  return (
    <Link to={path} className="group block bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all p-4">
      <div className="flex justify-between items-start mb-3">
        <div className={`p-2 rounded-lg ${colorMap[color] || colorMap.blue}`}>
          {icon}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-[10px] uppercase tracking-wider font-bold text-gray-400">{label}</div>
        </div>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-gray-900">{title}</span>
          <span className="text-gray-400 group-hover:text-blue-600 font-bold transition-colors">Détails →</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1 overflow-hidden">
          <div className={`h-full ${barColor[color] || barColor.blue} rounded-full transition-all duration-1000`} style={{ width: value }} />
        </div>
      </div>
    </Link>
  )
}

interface AlertSummaryCardProps {
  label: string
  count: number
  type: 'critique' | 'attention' | 'info'
  icon: React.ReactNode
}

function AlertSummaryCard({ label, count, type, icon }: AlertSummaryCardProps) {
  return (
    <div className={`p-4 rounded-xl border flex items-center gap-4 transition-transform hover:scale-[1.02] cursor-default ${ALERT_COLORS[type]}`}>
      <div className="p-3 bg-white rounded-full shadow-sm text-gray-700">
        {icon}
      </div>
      <div>
        <div className="text-2xl font-black">{count}</div>
        <div className="text-xs font-bold opacity-80 uppercase tracking-tighter">{label}</div>
      </div>
    </div>
  )
}

interface TimelineItemProps {
  icon: React.ReactNode
  title: string
  date: string
  color: 'orange' | 'blue' | 'red'
}

function TimelineItem({ icon, title, date, color }: TimelineItemProps) {
  const colors: Record<string, string> = {
    orange: 'bg-orange-100 text-orange-600',
    blue: 'bg-blue-100 text-blue-600',
    red: 'bg-red-100 text-red-600',
  }
  return (
    <div className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg transition-colors cursor-default">
      <div className={`p-2 rounded-full ${colors[color]}`}>
        {icon}
      </div>
      <div className="flex-1">
        <div className="text-xs font-bold text-gray-800">{title}</div>
        <div className="text-[10px] text-gray-400 font-medium">{date}</div>
      </div>
    </div>
  )
}
