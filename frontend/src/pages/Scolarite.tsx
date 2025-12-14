import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GraduationCap, TrendingUp, AlertCircle } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, LabelList
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import DataTable from '@/components/DataTable'
import ProgressBar from '@/components/ProgressBar'
import FilterBar, { FilterConfig, FilterValues, YearSelector, PeriodSelector } from '@/components/FilterBar'
import { scolariteApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'
import type { ModuleStats } from '@/types'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

// Filter configuration
const filterConfigs: FilterConfig[] = [
  {
    key: 'formation',
    label: 'Formation',
    type: 'select',
    options: [
      { value: '', label: 'Toutes' },
      { value: 'BUT', label: 'BUT' },
      { value: 'LP', label: 'Licence Pro' },
      { value: 'apprentissage', label: 'Apprentissage' },
    ]
  },
  {
    key: 'semestre',
    label: 'Semestre',
    type: 'multiselect',
    options: [
      { value: 'S1', label: 'Semestre 1' },
      { value: 'S2', label: 'Semestre 2' },
      { value: 'S3', label: 'Semestre 3' },
      { value: 'S4', label: 'Semestre 4' },
      { value: 'S5', label: 'Semestre 5' },
      { value: 'S6', label: 'Semestre 6' },
    ]
  },
  {
    key: 'search',
    label: 'Recherche',
    type: 'search',
    placeholder: 'Nom, module...'
  }
]

export default function Scolarite() {
  const { department } = useDepartment()
  const [filters, setFilters] = useState<FilterValues>({})
  const [year, setYear] = useState<string>('')
  const [period, setPeriod] = useState<string>('all')

  const { data: indicators, isLoading } = useQuery({
    queryKey: ['scolarite', 'indicators', department, year],
    queryFn: () => scolariteApi.getIndicators(department, year || undefined),
  })

  const { data: effectifs } = useQuery({
    queryKey: ['scolarite', 'effectifs', department],
    queryFn: () => scolariteApi.getEffectifs(department),
  })

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Chargement...</div>
  }
  // Helper: filter semesters by period
  const filterByPeriod = (semCode: string): boolean => {
    if (!period || period === 'all') return true
    const semNum = parseInt(semCode.replace(/\D/g, '')) || 0
    if (period === 'current') {
      // Current: S1-S2 (first year) or latest semesters
      return semNum <= 2 || semNum >= 5
    }
    if (period === 's1') return semNum === 1 || semNum === 2 // Semester 1 = S1+S2
    if (period === 's2') return semNum === 3 || semNum === 4 // Semester 2 = S3+S4  
    return true
  }
  // Build formation data first to create color mapping
  const allFormationData = indicators?.etudiants_par_formation
    ? Object.entries(indicators.etudiants_par_formation).map(([name, value]) => ({
        name,
        value
      }))
    : []
  
  // Apply formation filter (partial match)
  const formationFilter = filters.formation as string | undefined
  const formationData = formationFilter && formationFilter.length > 0
    ? allFormationData.filter(f => f.name.toLowerCase().includes(formationFilter.toLowerCase()))
    : allFormationData

  // Create a mapping from formation name to color
  const formationColorMap: Record<string, string> = {}
  formationData.forEach((f, index) => {
    formationColorMap[f.name] = COLORS[index % COLORS.length]
  })

  // Helper to find which formation a semester belongs to
  const getFormationFromSemesterName = (semName: string): string => {
    // The semester name contains the formation name (e.g., "BUT Réseaux et Télécommunications semestre 1")
    // Check for "apprentissage" first since it's more specific
    const semLower = semName.toLowerCase()
    const isApprentissage = semLower.includes('apprentissage')
    
    // Find matching formation - prioritize apprentissage match if semester is apprentissage
    const formations = Object.keys(formationColorMap)
    
    if (isApprentissage) {
      const appFormation = formations.find(f => f.toLowerCase().includes('apprentissage'))
      if (appFormation) return appFormation
    } else {
      // For non-apprentissage semesters, find a formation that does NOT contain "apprentissage"
      const nonAppFormation = formations.find(f => !f.toLowerCase().includes('apprentissage'))
      if (nonAppFormation) return nonAppFormation
    }
    
    // Fallback: return first formation
    return formations[0] || ''
  }

  // Prepare chart data - extract short semester name (e.g., "S1", "S3 App")
  const allSemestreData = indicators?.etudiants_par_semestre
    ? Object.entries(indicators.etudiants_par_semestre).map(([sem, count]) => {
        // Extract semester number from full name like "BUT Réseaux et Télécommunications semestre 1"
        const match = sem.match(/semestre\s*(\d+)/i)
        const semNum = match ? match[1] : '?'
        const isApprentissage = sem.toLowerCase().includes('apprentissage')
        const shortName = isApprentissage ? `S${semNum} App` : `S${semNum}`
        const formation = getFormationFromSemesterName(sem)
        return {
          semestre: shortName,
          fullName: sem,
          etudiants: count,
          formation,
          semNum,
          color: formationColorMap[formation] || COLORS[0]
        }
      })
    : []
  
  // Apply filters to semester data
  const semestreData = allSemestreData.filter(s => {
    // Filter by period
    if (!filterByPeriod(s.semestre)) return false
    // Filter by formation if set
    if (formationFilter && formationFilter.length > 0) {
      if (!s.fullName.toLowerCase().includes(formationFilter.toLowerCase()) &&
          !s.formation.toLowerCase().includes(formationFilter.toLowerCase())) {
        return false
      }
    }
    // Filter by semestre if set
    if (filters.semestre && Array.isArray(filters.semestre) && filters.semestre.length > 0) {
      const matchesSemestre = filters.semestre.some((sel: string) => {
        const selNum = sel.replace('S', '')
        return s.semNum === selNum
      })
      if (!matchesSemestre) return false
    }
    return true
  })

  const evolutionData = effectifs?.evolution
    ? Object.entries(effectifs.evolution).map(([year, count]) => ({
        annee: year,
        effectif: count
      }))
    : []

  const moduleColumns = [
    { key: 'code', header: 'Code' },
    { key: 'nom', header: 'Module' },
    { 
      key: 'moyenne', 
      header: 'Moyenne',
      align: 'right' as const,
      render: (item: ModuleStats) => item.moyenne.toFixed(2)
    },
    {
      key: 'taux_reussite',
      header: 'Réussite',
      align: 'right' as const,
      render: (item: ModuleStats) => (
        <span className={item.taux_reussite >= 70 ? 'text-green-600' : 'text-orange-600'}>
          {item.taux_reussite.toFixed(0)}%
        </span>
      )
    },
    { 
      key: 'nb_etudiants', 
      header: 'Étudiants',
      align: 'right' as const
    },
  ]

  // Apply filters to modules
  const filteredModules = indicators?.modules_stats.filter((mod: ModuleStats) => {
    if (filters.search && typeof filters.search === 'string') {
      const search = filters.search.toLowerCase()
      if (!mod.code.toLowerCase().includes(search) && !mod.nom.toLowerCase().includes(search)) {
        return false
      }
    }
    if (filters.semestre && Array.isArray(filters.semestre) && filters.semestre.length > 0) {
      const semNum = mod.code.charAt(1) // R1xxx -> 1 = S1, S2
      if (!filters.semestre.some(s => s.includes(semNum))) {
        return false
      }
    }
    return true
  }) ?? []

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scolarité</h1>
          <p className="text-gray-500 mt-1">Indicateurs de la vie étudiante et résultats académiques</p>
        </div>
        <div className="flex items-center gap-4">
          <YearSelector value={year} onChange={setYear} />
          <PeriodSelector value={period} onChange={setPeriod} />
        </div>
      </div>

      {/* Filters */}
      <FilterBar 
        filters={filterConfigs}
        values={filters}
        onChange={setFilters}
      />

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total étudiants"
          value={indicators?.total_etudiants ?? 0}
          icon={<GraduationCap className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Moyenne générale"
          value={indicators?.moyenne_generale.toFixed(2) ?? '-'}
          subtitle="Tous modules confondus"
          icon={<TrendingUp className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Taux de réussite"
          value={`${(indicators?.taux_reussite_global ?? 0).toFixed(1)}%`}
          subtitle="Global"
          color="blue"
        />
        <StatCard
          title="Taux d'absentéisme"
          value={`${(indicators?.taux_absenteisme ?? 0).toFixed(1)}%`}
          icon={<AlertCircle className="w-6 h-6" />}
          color="yellow"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer
          title="Effectifs par semestre"
          subtitle="Distribution des étudiants"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={semestreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="semestre" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip 
                formatter={(value: number) => [`${value} étudiants`, 'Effectif']}
                labelFormatter={(label) => semestreData.find(d => d.semestre === label)?.fullName || label}
              />
              <Bar dataKey="etudiants" radius={[4, 4, 0, 0]}>
                {semestreData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
                <LabelList dataKey="etudiants" position="top" fill="#374151" fontSize={12} fontWeight={600} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer
          title="Répartition par formation"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={formationData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {formationData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      

      {/* Semestres stats */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Résultats par semestre</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {indicators?.semestres_stats
            .filter((sem: { code: string; nom: string }) => {
              // Apply period filter
              if (!filterByPeriod(sem.code)) return false
              // Apply formation filter
              if (formationFilter && formationFilter.length > 0) {
                if (!sem.nom.toLowerCase().includes(formationFilter.toLowerCase())) {
                  return false
                }
              }
              // Apply semestre filter
              if (filters.semestre && Array.isArray(filters.semestre) && filters.semestre.length > 0) {
                const semNum = sem.code.replace('S', '')
                if (!filters.semestre.some((s: string) => s.replace('S', '') === semNum)) {
                  return false
                }
              }
              return true
            })
            .map((sem: { code: string; nom: string; annee: string; nb_etudiants: number; moyenne_generale: number; taux_reussite: number }, index: number) => {
            const isApprentissage = sem.nom.toLowerCase().includes('apprentissage')
            const shortName = isApprentissage ? `${sem.code} Apprentissage` : sem.code
            const tauxReussitePct = sem.taux_reussite < 1 ? sem.taux_reussite * 100 : sem.taux_reussite
            return (
            <div key={`${sem.code}-${index}`} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold text-gray-900">{shortName}</h4>
                  <p className="text-sm text-gray-500">{sem.annee}</p>
                </div>
                <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  {sem.nb_etudiants} étudiants
                </span>
              </div>
              <div className="space-y-2">
                <ProgressBar 
                  value={tauxReussitePct} 
                  label="Réussite" 
                  color={tauxReussitePct >= 70 ? 'green' : 'yellow'}
                />
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Moyenne</span>
                  <span className="font-medium">{sem.moyenne_generale.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )})}
        </div>
      </div>

      {/* Modules table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Résultats par module</h3>
        <DataTable 
          data={filteredModules}
          columns={moduleColumns}
        />
      </div>

      {/* Evolution chart */}
      <ChartContainer
        title="Évolution des effectifs"
        subtitle="Sur les dernières années"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={evolutionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="annee" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="effectif" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ fill: '#3b82f6' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  )
}
