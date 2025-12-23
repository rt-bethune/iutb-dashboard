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
  AlertTriangle,
  CheckCircle
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, LabelList,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'
import StatCard from '@/components/StatCard'
import ChartContainer from '@/components/ChartContainer'
import CompetencyRadar from '@/components/CompetencyRadar'
import CompetencyTable from '@/components/CompetencyTable'
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
  type ScolariteTab = 'overview' | 'indicators' | 'competences'
  const tabParam = searchParams.get('tab') || searchParams.get('active')
  const initialTab: ScolariteTab =
    tabParam === 'indicators' || tabParam === 'competences' ? (tabParam as ScolariteTab) : 'overview'
  const [activeTab, setActiveTab] = useState<ScolariteTab>(initialTab)

  // Sync activeTab with URL params
  useEffect(() => {
    const tab = searchParams.get('tab') || searchParams.get('active')
    if (tab === 'overview' || tab === 'indicators' || tab === 'competences') {
      if (tab !== activeTab) setActiveTab(tab)
    }
  }, [searchParams, activeTab])

  const handleTabChange = (tab: ScolariteTab) => {
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
  const [competencesNiveau, setCompetencesNiveau] = useState<number | undefined>(undefined)
  const [competencesParcours, setCompetencesParcours] = useState<string | undefined>(undefined)
  const [selectedEtudiantId, setSelectedEtudiantId] = useState<string | null>(null)

  const { data: indicators, isLoading, error } = useQuery({
    queryKey: ['scolarite', 'indicators', department, year],
    queryFn: () => scolariteApi.getIndicators(department, year || undefined),
    enabled: activeTab === 'overview',
  })
  const semestresStats = indicators?.semestres_stats ?? []

  // Fetch APC validation stats for overview (all students)
  const { data: overviewCompetencesStats } = useQuery({
    queryKey: ['scolarite', 'competences', 'stats', department, 'overview'],
    queryFn: () => scolariteApi.getCompetencesStats(department, {}),
    enabled: activeTab === 'overview',
  })

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

  // Fetch available parcours separately (fast endpoint)
  const { data: parcoursDisponibles, isLoading: parcoursLoading } = useQuery({
    queryKey: ['scolarite', 'competences', 'parcours', department, competencesNiveau],
    queryFn: () => scolariteApi.getCompetencesParcours(department, competencesNiveau),
    enabled: activeTab === 'competences',
    staleTime: 5 * 60 * 1000, // 5 minutes - parcours don't change often
  })

  const { data: competencesStats, isLoading: competencesStatsLoading, error: competencesStatsError } = useQuery({
    queryKey: ['scolarite', 'competences', 'stats', department, competencesNiveau, competencesParcours],
    queryFn: () => scolariteApi.getCompetencesStats(department, { niveau: competencesNiveau, parcours: competencesParcours }),
    enabled: activeTab === 'competences',
  })

  const { data: competencesEtudiants, isLoading: competencesEtudiantsLoading, error: competencesEtudiantsError } = useQuery({
    queryKey: ['scolarite', 'competences', 'etudiants', department, competencesNiveau, competencesParcours],
    queryFn: () => scolariteApi.getCompetencesEtudiants(department, { niveau: competencesNiveau, parcours: competencesParcours }),
    enabled: activeTab === 'competences',
  })

  const { data: selectedEtudiantCompetences, isLoading: selectedEtudiantCompetencesLoading, error: selectedEtudiantCompetencesError } = useQuery({
    queryKey: ['scolarite', 'competences', 'etudiant', department, selectedEtudiantId, competencesNiveau],
    queryFn: () => scolariteApi.getEtudiantCompetences(department, selectedEtudiantId!, competencesNiveau),
    enabled: activeTab === 'competences' && !!selectedEtudiantId,
  })

  useEffect(() => {
    setSelectedEtudiantId(null)
  }, [competencesNiveau, competencesParcours])

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

  if (activeTab === 'competences' && (competencesStatsError || competencesEtudiantsError || selectedEtudiantCompetencesError)) {
    const axiosError = (competencesStatsError || competencesEtudiantsError || selectedEtudiantCompetencesError) as any
    if (axiosError?.response?.status === 403) {
      return (
        <PermissionGate domain="scolarite" action="view">
          <div />
        </PermissionGate>
      )
    }
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        Erreur lors du chargement des compétences
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
              onClick={() => handleTabChange('overview')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'overview' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Vue d'ensemble
            </button>
            <button
              onClick={() => handleTabChange('indicators')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'indicators' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Indicateurs de cohorte
            </button>
            <button
              onClick={() => handleTabChange('competences')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'competences' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Compétences
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <StatCard title="Total étudiants" value={indicators?.total_etudiants ?? 0} icon={<GraduationCap className="w-6 h-6" />} color="blue" />
            <StatCard title="Moyenne générale" value={indicators?.moyenne_generale.toFixed(2) ?? '-'} icon={<TrendingUp className="w-6 h-6" />} color="green" />
            <StatCard title="Taux de réussite" value={`${(indicators?.taux_reussite_global ?? 0).toFixed(1)}%`} color="blue" subtitle="Notes ≥ 10/20" />
            <StatCard
              title="Validation APC"
              value={`${toPercent(overviewCompetencesStats?.taux_validation_global ?? 0).toFixed(0)}%`}
              icon={<CheckCircle className="w-6 h-6" />}
              color="green"
              subtitle=">50% compétences"
            />
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
      ) : activeTab === 'indicators' ? (
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
      ) : (
        <>
          {/* Competences Tab Content */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Niveau</span>
                <select
                  value={competencesNiveau ?? ''}
                  onChange={(e) => setCompetencesNiveau(e.target.value ? Number(e.target.value) : undefined)}
                  className="border border-gray-300 rounded-md px-2 py-1 text-sm"
                >
                  <option value="">Dernier niveau</option>
                  <option value="1">BUT 1</option>
                  <option value="2">BUT 2</option>
                  <option value="3">BUT 3</option>
                </select>
              </div>
              {/* Parcours dropdown - show loading state or dropdown */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Parcours</span>
                {parcoursLoading ? (
                  <span className="text-xs text-gray-400 animate-pulse">Chargement...</span>
                ) : parcoursDisponibles && parcoursDisponibles.length > 0 ? (
                  <select
                    value={competencesParcours ?? ''}
                    onChange={(e) => setCompetencesParcours(e.target.value || undefined)}
                    className="border border-gray-300 rounded-md px-2 py-1 text-sm"
                  >
                    <option value="">Tous les parcours</option>
                    {parcoursDisponibles.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                ) : (
                  <span className="text-xs text-gray-400">Aucun parcours</span>
                )}
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {competencesStats?.total_etudiants ?? 0} étudiant(s) analysé(s)
              {competencesParcours && ` (parcours: ${competencesParcours})`}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              title="Étudiants"
              value={competencesStats?.total_etudiants ?? 0}
              icon={<Users className="h-6 w-6" />}
              loading={competencesStatsLoading}
            />
            <StatCard
              title="Validation globale"
              value={`${toPercent(competencesStats?.taux_validation_global ?? 0).toFixed(0)}%`}
              icon={<FileText className="h-6 w-6" />}
              loading={competencesStatsLoading}
            />
            <StatCard
              title="Niveau"
              value={competencesNiveau ? `BUT ${competencesNiveau}` : 'Dernier'}
              icon={<BarChart3 className="h-6 w-6" />}
              loading={false}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartContainer title="Radar des UEs" loading={competencesStatsLoading}>
              <CompetencyRadar
                data={
                  competencesStats?.par_ue
                    ? Object.entries(competencesStats.par_ue)
                      .map(([competence, taux]) => ({
                        competence,
                        taux: typeof taux === 'number' ? taux : 0,
                      }))
                      .sort((a, b) => a.competence.localeCompare(b.competence))
                    : []
                }
              />
            </ChartContainer>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Détails par UE</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-gray-600 border-b">
                    <tr>
                      <th className="py-2 pr-4 font-medium">UE</th>
                      <th className="py-2 pr-4 font-medium">Taux validé</th>
                      <th className="py-2 pr-0 font-medium">Moyenne</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {competencesStats?.par_ue
                      ? Object.keys(competencesStats.par_ue)
                        .sort((a, b) => a.localeCompare(b))
                        .map((key) => (
                          <tr key={key}>
                            <td className="py-2 pr-4 font-medium">{key}</td>
                            <td className="py-2 pr-4">
                              {toPercent(competencesStats.par_ue[key]).toFixed(0)}%
                            </td>
                            <td className="py-2 pr-0">
                              {competencesStats.moyenne_par_ue?.[key] !== undefined
                                ? competencesStats.moyenne_par_ue[key].toFixed(2)
                                : '—'}
                            </td>
                          </tr>
                        ))
                      : null}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Étudiants</h3>
            {competencesEtudiantsLoading ? (
              <div className="text-sm text-gray-500">Chargement…</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-gray-600 border-b">
                    <tr>
                      <th className="py-2 pr-4 font-medium">Étudiant</th>
                      <th className="py-2 pr-4 font-medium">Parcours</th>
                      <th className="py-2 pr-4 font-medium">Validation</th>
                      <th className="py-2 pr-4 font-medium">UEs</th>
                      <th className="py-2 pr-0 font-medium">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {(competencesEtudiants || [])
                      .filter((e: any) => {
                        const search = (filters.search as string) || ''
                        const searchNorm = search ? normalizeText(search) : ''
                        if (searchNorm) {
                          const name1 = normalizeText(`${e.nom || ''} ${e.prenom || ''}`)
                          const name2 = normalizeText(`${e.prenom || ''} ${e.nom || ''}`)
                          if (!name1.includes(searchNorm) && !name2.includes(searchNorm)) return false
                        }

                        if (selectedFormations.length > 0) {
                          const formation = normalizeText(e.formation || '')
                          const match = selectedFormations.some((sel) => formation.includes(normalizeText(sel)))
                          if (!match) return false
                        }

                        if (selectedSemestres.length > 0) {
                          if (!selectedSemestres.includes(e.semestre)) return false
                        }

                        return true
                      })
                      .map((e: any) => {
                        const isSelected = selectedEtudiantId === e.etudiant_id
                        return (
                          <tr
                            key={e.etudiant_id}
                            onClick={() => setSelectedEtudiantId(e.etudiant_id)}
                            className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
                          >
                            <td className="py-2 pr-4">
                              <div className="font-medium text-gray-900">
                                {[e.nom, e.prenom].filter(Boolean).join(' ') || e.etudiant_id}
                              </div>
                              <div className="text-xs text-gray-500">{e.formation || '—'} • {e.semestre || '—'}</div>
                            </td>
                            <td className="py-2 pr-4">
                              {e.parcours ? (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                                  {e.parcours}
                                </span>
                              ) : (
                                <span className="text-gray-400">—</span>
                              )}
                            </td>
                            <td className="py-2 pr-4">{toPercent(e.taux_validation).toFixed(0)}%</td>
                            <td className="py-2 pr-4">
                              {e.nb_ues_validees ?? e.nb_competences_validees ?? 0}/{e.nb_ues ?? e.nb_competences ?? 0}
                            </td>
                            <td className="py-2 pr-0">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${e.valide ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                  }`}
                              >
                                {e.valide ? 'Admis' : 'Non admis'}
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {selectedEtudiantId && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Détail étudiant{selectedEtudiantCompetences ? ` — ${[selectedEtudiantCompetences.nom, selectedEtudiantCompetences.prenom].filter(Boolean).join(' ')}` : ''}
                </h3>
                <button
                  onClick={() => setSelectedEtudiantId(null)}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Fermer
                </button>
              </div>
              {selectedEtudiantCompetencesLoading ? (
                <div className="text-sm text-gray-500">Chargement…</div>
              ) : selectedEtudiantCompetences ? (
                <CompetencyTable validations={selectedEtudiantCompetences.ue_validations || selectedEtudiantCompetences.rcue_validations || []} />
              ) : (
                <div className="text-sm text-gray-500">Aucune donnée.</div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
