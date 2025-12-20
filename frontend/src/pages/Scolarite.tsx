import { useMemo, useState, useCallback, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  useSearchParams
} from 'react-router-dom'
import {
  GraduationCap,
  TrendingUp,
  AlertCircle,
  BarChart3,
  Users,
  TrendingDown,
  FileText,
  AlertTriangle
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, LabelList,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import ProgressBar from '@/components/ProgressBar'
import FilterBar, { FilterConfig, FilterValues, YearSelector, PeriodSelector } from '@/components/FilterBar'
import PermissionGate from '@/components/PermissionGate'
import api, { scolariteApi, indicateursApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
const MENTION_COLORS = ['#10b981', '#34d399', '#6ee7b7', '#fbbf24', '#f97316', '#ef4444']
const TREND_COLORS = { hausse: 'text-green-600', baisse: 'text-red-600', stable: 'text-gray-600' }

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

export default function Scolarite() {
  const { department } = useDepartment()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = searchParams.get('active') === 'indicators' || searchParams.get('tab') === 'indicators'
    ? 'indicators'
    : 'overview'
  const [activeTab, setActiveTab] = useState<'overview' | 'indicators'>(initialTab)

  // Sync activeTab with URL params
  useEffect(() => {
    const tabParam = searchParams.get('active') || searchParams.get('tab')
    if (tabParam === 'indicators' && activeTab !== 'indicators') {
      setActiveTab('indicators')
    } else if (tabParam === 'overview' && activeTab !== 'overview') {
      setActiveTab('overview')
    }
  }, [searchParams])

  const handleTabChange = (tab: 'overview' | 'indicators') => {
    setActiveTab(tab)
    setSearchParams(prev => {
      prev.set('tab', tab)
      prev.delete('active') // Clean up old param if present
      return prev
    })
  }
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
    enabled: activeTab === 'overview',
  })
  const semestresStats = indicators?.semestres_stats ?? []

  const { data: effectifs } = useQuery({
    queryKey: ['scolarite', 'effectifs', department],
    queryFn: () => scolariteApi.getEffectifs(department),
    enabled: activeTab === 'overview' && !!indicators,
  })

  // Indicators Tab Data Logic
  const cohortParams = useMemo(() => ({
    semestre: Array.isArray(filters.semestre) ? (filters.semestre[0] as string) : (filters.semestre as string),
    formation: Array.isArray(filters.formation) ? (filters.formation[0] as string) : (filters.formation as string),
    modalite: (filters.modalite as string)?.toUpperCase(),
    annee: year || undefined,
    periode: period !== 'all' ? period : undefined
  }), [filters, year, period])

  const { data: tableau, isLoading: tableauLoading } = useQuery({
    queryKey: ['tableau-bord', department, cohortParams],
    queryFn: () => indicateursApi.getTableauBord(department, cohortParams as any),
    enabled: activeTab === 'indicators',
  })

  const { data: comparaison, isLoading: comparaisonLoading } = useQuery({
    queryKey: ['comparaison-inter', department, cohortParams],
    queryFn: () => api.get<ComparaisonInterannuelle>(`/${department}/indicateurs/comparaison-interannuelle`, { params: cohortParams }).then(res => res.data),
    enabled: activeTab === 'indicators',
  })

  const { data: typeBac, isLoading: typeBacLoading } = useQuery({
    queryKey: ['type-bac', department, cohortParams],
    queryFn: () => api.get<AnalyseTypeBac>(`/${department}/indicateurs/analyse-type-bac`, { params: cohortParams }).then(res => res.data),
    enabled: activeTab === 'indicators',
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

  if (isLoading && activeTab === 'overview') {
    return <div className="flex items-center justify-center h-64">Chargement...</div>
  }

  // Helper functions
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

  const filterByPeriod = (semCode: string): boolean => {
    if (!period || period === 'all') return true
    const semNum = parseInt(semCode.replace(/\D/g, '')) || 0
    if (period === 'current') return semNum <= 2 || semNum >= 5
    if (period === 's1') return semNum === 1 || semNum === 2
    if (period === 's2') return semNum === 3 || semNum === 4
    return true
  }

  const getFormationFromSemesterName = (semName: string): string => {
    const semNormalized = normalizeText(semName)
    const allNames = indicators?.etudiants_par_formation ? Object.keys(indicators.etudiants_par_formation) : []
    const sortedFormations = [...allNames].sort((a, b) => b.length - a.length)
    const matched = sortedFormations.find((formation) => semNormalized.includes(normalizeText(formation)))
    if (matched) return matched
    return allNames[0] || ''
  }

  const getTrendIcon = (tendance: string) => {
    if (tendance === 'hausse') return <TrendingUp className="h-4 w-4 text-green-600" />
    if (tendance === 'baisse') return <TrendingDown className="h-4 w-4 text-red-600" />
    return null
  }

  // Data preparation for Overview
  const selectedFormations = Array.isArray(filters.formation) ? filters.formation : []
  const selectedSemestres = Array.isArray(filters.semestre) ? filters.semestre : []
  const modaliteFilter = (filters.modalite as string) || ''
  const minReussite = filters.reussite ? Number(filters.reussite) : undefined
  const minEffectif = filters.effectif ? Number(filters.effectif) : undefined
  const maxAbsenteisme = filters.absenteisme ? Number(filters.absenteisme) : undefined

  const allFormationData = indicators?.etudiants_par_formation
    ? Object.entries(indicators.etudiants_par_formation).map(([name, value]) => ({ name, value }))
    : []
  const formationData = selectedFormations.length > 0
    ? allFormationData.filter((f) => selectedFormations.some((sel) => normalizeText(f.name).includes(normalizeText(sel))))
    : allFormationData

  const formationColorMap: Record<string, string> = {}
  allFormationData.forEach((f, index) => { formationColorMap[f.name] = COLORS[index % COLORS.length] })

  const semestreData = indicators?.etudiants_par_semestre
    ? Object.entries(indicators.etudiants_par_semestre)
      .map(([sem, count]) => {
        const matchS = sem.match(/\bS(\d+)\b/)
        const semNum = matchS ? matchS[1] : '?'
        const formation = getFormationFromSemesterName(sem)
        const isFA = /\bfa\b/i.test(sem) || sem.toLowerCase().includes('apprentissage')
        const shortName = `S${semNum}${isFA ? ' FA' : ''}`
        return {
          semestre: shortName,
          fullName: sem,
          etudiants: count as number,
          formation,
          semNum,
          isFA,
          color: formationColorMap[formation] || COLORS[0]
        }
      })
      .filter(s => {
        if (!filterByPeriod(s.semestre)) return false
        if (selectedFormations.length > 0 && !selectedFormations.some(sel => normalizeText(sel) === normalizeText(s.formation))) return false
        if (selectedSemestres.length > 0 && !selectedSemestres.some(sel => sel.replace('S', '') === s.semNum)) return false
        if (modaliteFilter === 'fa' && !s.isFA) return false
        if (modaliteFilter === 'fi' && s.isFA) return false
        return true
      })
    : []

  const evolutionData = effectifs?.evolution ? Object.entries(effectifs.evolution).map(([y, c]) => ({ annee: y, effectif: c })) : []

  // Data preparation for Indicators
  const mentionsData = tableau ? [
    { name: 'Très Bien', value: tableau.mentions.tres_bien },
    { name: 'Bien', value: tableau.mentions.bien },
    { name: 'Assez Bien', value: tableau.mentions.assez_bien },
    { name: 'Passable', value: tableau.mentions.passable },
    { name: 'Insuffisant', value: tableau.mentions.insuffisant },
    { name: 'Éliminatoire', value: tableau.mentions.eliminatoire },
  ] : []

  const interannuelleData = comparaison ? comparaison.annees.map((year: string, i: number) => ({
    annee: year,
    moyenne: comparaison.moyennes[i],
    taux_reussite: (comparaison.taux_reussite[i] * 100).toFixed(1),
    effectif: comparaison.effectifs[i],
  })) : []

  const typeBacData = typeBac ? Object.entries(typeBac.par_type).map(([type, data]) => ({
    type,
    moyenne: data.moyenne,
    effectif: data.effectif,
    taux_reussite: (data.taux_reussite * 100).toFixed(1),
  })) : []

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scolarité</h1>
          <div className="flex items-center gap-6 mt-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'overview' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Vue d'ensemble
            </button>
            <button
              onClick={() => setActiveTab('indicators')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'indicators' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Indicateurs de cohorte
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <YearSelector value={year} onChange={setYear} />
          <PeriodSelector value={period} onChange={setPeriod} />
        </div>
      </div>

      {/* Filters */}
      <FilterBar filters={filterConfigs} values={filters} onChange={setFilters} />

      {activeTab === 'overview' ? (
        <>
          {/* Stats overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard title="Total étudiants" value={indicators?.total_etudiants ?? 0} icon={<GraduationCap className="w-6 h-6" />} color="blue" />
            <StatCard title="Moyenne générale" value={indicators?.moyenne_generale.toFixed(2) ?? '-'} icon={<TrendingUp className="w-6 h-6" />} color="green" />
            <StatCard title="Taux de réussite" value={`${(indicators?.taux_reussite_global ?? 0).toFixed(1)}%`} color="blue" />
            <StatCard title="Taux d'absentéisme" value={`${(indicators?.taux_absenteisme ?? 0).toFixed(1)}%`} icon={<AlertCircle className="w-6 h-6" />} color="yellow" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartContainer title="Effectifs par semestre">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={semestreData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="semestre" stroke="#6b7280" fontSize={12} />
                  <YAxis stroke="#6b7280" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="etudiants" radius={[4, 4, 0, 0]}>
                    {semestreData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                    <LabelList dataKey="etudiants" position="top" fill="#374151" fontSize={12} fontWeight={600} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>

            <ChartContainer title="Répartition par formation">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={formationData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                    {formationData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <Legend /><Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Résultats par semestre</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {semestresStats
                .filter((sem: any) => {
                  if (!filterByPeriod(sem.code)) return false
                  if (selectedFormations.length > 0 && !selectedFormations.some((sel: string) => normalizeText(sel) === normalizeText(getFormationFromSemesterName(sem.nom)))) return false
                  if (selectedSemestres.length > 0 && !selectedSemestres.some((sel: string) => sel.replace('S', '') === sem.code.replace('S', ''))) return false
                  const isFA = /\bfa\b/i.test(sem.nom) || sem.nom.toLowerCase().includes('apprentissage')
                  if (modaliteFilter === 'fa' && !isFA) return false
                  if (modaliteFilter === 'fi' && isFA) return false
                  if (minEffectif !== undefined && sem.nb_etudiants < minEffectif) return false
                  if (minReussite !== undefined && toPercent(sem.taux_reussite) < minReussite) return false
                  if (maxAbsenteisme !== undefined && sem.taux_absenteisme > maxAbsenteisme) return false
                  return true
                })
                .map((sem: any, index: number) => {
                  const isFA = /\bfa\b/i.test(sem.nom) || sem.nom.toLowerCase().includes('apprentissage')
                  const suffix = isFA ? ' FA' : ''
                  const shortName = `${sem.code}${suffix}`
                  const tauxReussitePct = toPercent(sem.taux_reussite)
                  return (
                    <div key={`${sem.code}-${index}`} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-semibold text-gray-900">{shortName}</h4>
                          <p className="text-sm text-gray-500 truncate w-32" title={sem.nom}>{sem.nom}</p>
                        </div>
                        <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">{sem.nb_etudiants} étudiants</span>
                      </div>
                      <div className="space-y-2">
                        <ProgressBar value={tauxReussitePct} label="Réussite" color={tauxReussitePct >= 70 ? 'green' : 'yellow'} />
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Moyenne</span>
                          <span className="font-medium">{sem.moyenne_generale.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>

          <ChartContainer title="Évolution des effectifs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={evolutionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="annee" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} /><Tooltip />
                <Line type="monotone" dataKey="effectif" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6' }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </>
      ) : (
        <>
          {/* Indicators Tab Content */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <StatCard title="Effectif" value={tableau?.statistiques.effectif_total || 0} icon={<Users className="h-6 w-6" />} loading={tableauLoading} />
            <StatCard title="Moyenne promo" value={tableau?.statistiques.moyenne_promo.toFixed(1) || '0'} suffix="/20" icon={<BarChart3 className="h-6 w-6" />} loading={tableauLoading} />
            <StatCard title="Taux réussite" value={tableau ? (tableau.statistiques.taux_reussite * 100).toFixed(0) : '0'} suffix="%" icon={<GraduationCap className="h-6 w-6" />} color="green" loading={tableauLoading} />
            <StatCard title="En difficulté" value={tableau ? (tableau.statistiques.taux_difficulte * 100).toFixed(0) : '0'} suffix="%" icon={<AlertTriangle className="h-6 w-6" />} color="red" loading={tableauLoading} />
            <StatCard title="Excellence" value={tableau ? (tableau.statistiques.taux_excellence * 100).toFixed(0) : '0'} suffix="%" icon={<TrendingUp className="h-6 w-6" />} color="green" loading={tableauLoading} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ChartContainer title="Évolution interannuelle" loading={comparaisonLoading}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={interannuelleData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="annee" />
                  <YAxis yAxisId="left" domain={[8, 14]} />
                  <YAxis yAxisId="right" orientation="right" domain={[60, 100]} />
                  <Tooltip /><Legend />
                  <Line yAxisId="left" type="monotone" dataKey="moyenne" name="Moyenne" stroke="#3b82f6" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="taux_reussite" name="Taux réussite (%)" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>

            <ChartContainer title="Réussite par type de bac" loading={typeBacLoading}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={typeBacData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis /><Tooltip /><Legend />
                  <Bar dataKey="moyenne" name="Moyenne" fill="#3b82f6" />
                  <Bar dataKey="taux_reussite" name="Taux réussite (%)" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </div>

          {tableau?.indicateurs_cles && (
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <h3 className="text-lg font-medium mb-4">Indicateurs clés vs année précédente</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(tableau.indicateurs_cles).map(([key, data]) => {
                  const typedData = data as { valeur: number; tendance: string; vs_annee_prec: number }
                  return (
                    <div key={key} className="border rounded-lg p-4">
                      <p className="text-sm text-gray-500 capitalize">{key.replace(/_/g, ' ')}</p>
                      <div className="flex items-center mt-1">
                        <span className="text-xl font-bold">
                          {typeof typedData.valeur === 'number' && typedData.valeur < 1 ? (typedData.valeur * 100).toFixed(0) + '%' : typedData.valeur}
                        </span>
                        <span className={`ml-2 flex items-center text-xs ${TREND_COLORS[typedData.tendance as keyof typeof TREND_COLORS] || 'text-gray-500'}`}>
                          {getTrendIcon(typedData.tendance)}
                          {typedData.vs_annee_prec > 0 ? '+' : ''}
                          {typeof typedData.vs_annee_prec === 'number' && Math.abs(typedData.vs_annee_prec) < 1 ? (typedData.vs_annee_prec * 100).toFixed(0) + '%' : typedData.vs_annee_prec}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
