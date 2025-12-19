import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GraduationCap, TrendingUp, AlertCircle } from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, LabelList
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import ProgressBar from '@/components/ProgressBar'
import FilterBar, { FilterConfig, FilterValues, YearSelector, PeriodSelector } from '@/components/FilterBar'
import PermissionGate from '@/components/PermissionGate'
import { scolariteApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Scolarite() {
  const { department } = useDepartment()
  const [filters, setFilters] = useState<FilterValues>({
    formation: [],
    semestre: [],
    modalite: '',
    reussite: '',
    effectif: '',
    absenteisme: '',
    search: '',
  })
  const [year, setYear] = useState<string>('')
  const [period, setPeriod] = useState<string>('all')

  const { data: indicators, isLoading, error } = useQuery({
    queryKey: ['scolarite', 'indicators', department, year],
    queryFn: () => scolariteApi.getIndicators(department, year || undefined),
  })
  const semestresStats = indicators?.semestres_stats ?? []

  const { data: effectifs } = useQuery({
    queryKey: ['scolarite', 'effectifs', department],
    queryFn: () => scolariteApi.getEffectifs(department),
    enabled: !!indicators, // Only fetch if indicators loaded successfully
  })

  const formationOptions = useMemo(
    () =>
      indicators?.etudiants_par_formation
        ? Object.keys(indicators.etudiants_par_formation).map((name) => ({ value: name, label: name }))
        : [
            { value: 'BUT', label: 'BUT' },
            { value: 'Licence Pro', label: 'Licence Pro' },
            { value: 'Apprentissage', label: 'Apprentissage' },
          ],
    [indicators]
  )

  const filterConfigs: FilterConfig[] = useMemo(
    () => [
      {
        key: 'formation',
        label: 'Formation',
        type: 'multiselect',
        options: formationOptions,
      },
      {
        key: 'modalite',
        label: 'Modalité',
        type: 'select',
        options: [
          { value: '', label: 'FI + FA' },
          { value: 'fi', label: 'Formation initiale' },
          { value: 'fa', label: 'Apprentissage / FA' },
        ],
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
        ],
      },
      {
        key: 'reussite',
        label: 'Réussite min.',
        type: 'select',
        options: [
          { value: '', label: 'Toutes' },
          { value: '50', label: '50%+' },
          { value: '60', label: '60%+' },
          { value: '70', label: '70%+' },
          { value: '80', label: '80%+' },
          { value: '90', label: '90%+' },
        ],
      },
      {
        key: 'effectif',
        label: 'Effectif min.',
        type: 'select',
        options: [
          { value: '', label: 'Tous' },
          { value: '10', label: '10+' },
          { value: '20', label: '20+' },
          { value: '30', label: '30+' },
          { value: '50', label: '50+' },
        ],
      },
      {
        key: 'absenteisme',
        label: 'Absentéisme max.',
        type: 'select',
        options: [
          { value: '', label: 'Tous' },
          { value: '15', label: '15% max' },
          { value: '10', label: '10% max' },
          { value: '5', label: '5% max' },
        ],
      },
      {
        key: 'search',
        label: 'Recherche',
        type: 'search',
        placeholder: 'Nom, module...'
      }
    ],
    [formationOptions]
  )

  // Handle permission errors
  if (error) {
    const axiosError = error as any
    if (axiosError?.response?.status === 403) {
      return (
        <PermissionGate domain="scolarite" action="view">
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
  // Helpers for filter values
  const selectedFormations = Array.isArray(filters.formation)
    ? filters.formation
    : filters.formation
    ? [String(filters.formation)]
    : []
  const selectedSemestres = Array.isArray(filters.semestre) ? filters.semestre : []
  const modaliteFilter = (filters.modalite as string) || ''
  const minReussite = filters.reussite ? Number(filters.reussite) : undefined
  const minEffectif = filters.effectif ? Number(filters.effectif) : undefined
  const maxAbsenteisme = filters.absenteisme ? Number(filters.absenteisme) : undefined

  const toPercent = (value: number | undefined) => {
    if (value === undefined || value === null) return 0
    return value > 1 ? value : value * 100
  }

  const normalizeText = (text: string) => text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()

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
  const allFormationNames = allFormationData.map((f) => f.name)
  
  // Apply formation filter (multi)
  const formationData = selectedFormations.length > 0
    ? allFormationData.filter((f) =>
        selectedFormations.some((sel) => normalizeText(f.name).includes(normalizeText(sel)))
      )
    : allFormationData

  // Create a mapping from formation name to color
  const formationColorMap: Record<string, string> = {}
  allFormationNames.forEach((name, index) => {
    formationColorMap[name] = COLORS[index % COLORS.length]
  })

  // Helper to find which formation a semester belongs to
  const getFormationFromSemesterName = (semName: string): string => {
    const semNormalized = normalizeText(semName)
    const sortedFormations = [...allFormationNames].sort((a, b) => b.length - a.length)

    const matched = sortedFormations.find((formation) => semNormalized.includes(normalizeText(formation)))
    if (matched) return matched

    if (semNormalized.includes('appren')) {
      const appFormation = sortedFormations.find((formation) => normalizeText(formation).includes('appren'))
      if (appFormation) return appFormation
    }

    return allFormationNames[0] || ''
  }

  // Prepare chart data - extract short semester name (e.g., "S1 FI", "S3 FA")
  const allSemestreData = indicators?.etudiants_par_semestre
    ? Object.entries(indicators.etudiants_par_semestre).map(([sem, count]) => {
        // Extract semester number from full name
        // Try multiple patterns: "semestre 1", "S1", "Semestre1", etc.
        const matchSemestre = sem.match(/semestre\s*(\d+)/i)
        const matchS = sem.match(/\bS(\d+)\b/)
        const semNum = matchSemestre ? matchSemestre[1] : (matchS ? matchS[1] : '?')
        
        // Detect formation type: FA (Apprentissage/Alternance) vs FI (Formation Initiale)
        const semLower = sem.toLowerCase()
        const isFA = semLower.includes(' fa ') || semLower.includes(' fa') || 
                     semLower.endsWith(' fa') || /\bfa\b/i.test(sem) ||
                     semLower.includes('apprentissage') || semLower.includes('alternance')
        const isFI = semLower.includes(' fi ') || semLower.includes(' fi') || 
                     semLower.endsWith(' fi') || /\bfi\b/i.test(sem)
        
        const formation = getFormationFromSemesterName(sem)
        
        // Create short name: "S1 FI" or "S3 FA"
        let shortName = `S${semNum}`
        if (isFA) {
          shortName = `S${semNum} FA`
        } else if (isFI) {
          shortName = `S${semNum} FI`
        }



        if (formation) {
          // Extract formation type (BUT, LP, etc.) for shorter label
          const formType = formation.match(/\b(BUT|LP|DUT|Licence)\b/i)?.[1]?.toUpperCase()
          if (formType && allFormationNames.length > 1) {
            shortName = `${formType} ${shortName}`
          }
        }
        
        const colorIndex = Math.max(allFormationNames.indexOf(formation), 0)
        const color = formationColorMap[formation] ?? COLORS[colorIndex % COLORS.length] ?? COLORS[0]
        return {
          semestre: shortName,
          fullName: sem,
          etudiants: count,
          formation,
          semNum,
          isFA,
          color
        }
      })
    : []

  // Apply filters to semester data
  const semestreData = allSemestreData.filter(s => {
    // Filter by period
    if (!filterByPeriod(s.semestre)) return false
    // Filter by formation if set
    if (selectedFormations.length > 0) {
      const matchesFormation = selectedFormations.some((sel) =>
        normalizeText(sel) === normalizeText(s.formation) ||
        normalizeText(s.fullName).includes(normalizeText(sel))
      )
      if (!matchesFormation) return false
    }
    // Filter by semestre if set
    if (selectedSemestres.length > 0) {
      const matchesSemestre = selectedSemestres.some((sel: string) => {
        const selNum = sel.replace('S', '')
        return s.semNum === selNum
      })
      if (!matchesSemestre) return false
    }
    // Filter by modalité
    if (modaliteFilter === 'fa' && !s.isFA) return false
    if (modaliteFilter === 'fi' && s.isFA) return false

    // Effectif threshold
    if (minEffectif && s.etudiants < minEffectif) return false

    return true
  })

  const evolutionData = effectifs?.evolution
    ? Object.entries(effectifs.evolution).map(([year, count]) => ({
        annee: year,
        effectif: count
      }))
    : []

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
                outerRadius={80}
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
          {semestresStats
            .filter((sem: { code: string; nom: string; taux_absenteisme: number; taux_reussite: number }) => {
              // Apply period filter
              if (!filterByPeriod(sem.code)) return false
              // Apply formation filter
              if (selectedFormations.length > 0) {
                const semFormation = getFormationFromSemesterName(sem.nom)
                const matchesFormation = selectedFormations.some((sel) => normalizeText(sel) === normalizeText(semFormation))
                if (!matchesFormation) return false
              }
              // Apply semestre filter
              if (selectedSemestres.length > 0) {
                const semNum = sem.code.replace('S', '')
                if (!selectedSemestres.some((s: string) => s.replace('S', '') === semNum)) {
                  return false
                }
              }
              // Modalité filter
              const semLower = sem.nom.toLowerCase()
              const isFA = /\bfa\b/i.test(sem.nom) || semLower.includes('apprentissage') || semLower.includes('alternance')
              if (modaliteFilter === 'fa' && !isFA) return false
              if (modaliteFilter === 'fi' && isFA) return false

              if (minEffectif !== undefined && sem.nb_etudiants < minEffectif) return false
              if (minReussite !== undefined && toPercent(sem.taux_reussite) < minReussite) return false
              if (maxAbsenteisme !== undefined && sem.taux_absenteisme > maxAbsenteisme) return false
              return true
            })
            .map((sem: { code: string; nom: string; annee: string; nb_etudiants: number; moyenne_generale: number; taux_reussite: number; taux_absenteisme: number }, index: number) => {
            const semLower = sem.nom.toLowerCase()
            const isFA = /\bfa\b/i.test(sem.nom) || semLower.includes('apprentissage') || semLower.includes('alternance')
            const isFI = /\bfi\b/i.test(sem.nom)
            const suffix = isFA ? ' FA' : (isFI ? ' FI' : '')
            const shortName = `${sem.code}${suffix}`
            const tauxReussitePct = toPercent(sem.taux_reussite)
            return (
            <div key={`${sem.code}-${index}`} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold text-gray-900">{shortName}</h4>
                  <p className="text-sm text-gray-500" title={sem.nom}>{sem.nom}</p>
                  <p className="text-xs text-gray-400">{sem.annee}</p>
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
