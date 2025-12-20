import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, BarChart3, Target } from 'lucide-react'
import FilterBar, { FilterConfig, FilterValues } from '@/components/FilterBar'
import DataTable from '@/components/DataTable'
import StatCard from '@/components/StatCard'
import PermissionGate from '@/components/PermissionGate'
import { indicateursApi } from '@/services/api'
import { useDepartment } from '../contexts/DepartmentContext'

type ModuleAnalyse = {
  code: string
  nom: string
  semestre?: string
  formation?: string
  annee?: string
  nb_inscrits?: number
  nb_notes?: number
  moyenne: number
  mediane?: number
  ecart_type?: number
  taux_reussite?: number
  taux_validation?: number
  taux_echec?: number
  alerte?: boolean
  alerte_message?: string
  est_module_risque?: boolean
}

const normalizeText = (text: string) =>
  text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()

const toPercent = (value?: number | null) => {
  if (value === undefined || value === null) return 0
  return value > 1 ? value : value * 100
}

const detectModalite = (text?: string) => {
  if (!text) return ''
  const t = text.toLowerCase()
  if (t.includes('fa') || t.includes('apprentissage') || t.includes('alternance')) return 'fa'
  if (t.includes('fi')) return 'fi'
  return ''
}

export default function AnalyseModules() {
  const { department } = useDepartment()
  const [filters, setFilters] = useState<FilterValues>({
    formation: [],
    semestre: [],
    modalite: '',
    reussite: '',
    effectif: '',
    search: '',
  })

  const { data: modules, isLoading, error } = useQuery({
    queryKey: ['modules-analyse', department],
    queryFn: () => indicateursApi.getModules(department, { tri: 'taux_echec' }),
  })

  const formationOptions = useMemo(() => {
    if (!modules) {
      return [
        { value: 'BUT', label: 'BUT' },
        { value: 'Licence Pro', label: 'Licence Pro' },
      ]
    }
    const unique = new Set<string>()
    modules.forEach((m: ModuleAnalyse) => {
      if (m.formation) unique.add(m.formation)
    })
    if (unique.size === 0) unique.add('Autre')
    return Array.from(unique).map((f) => ({ value: f, label: f }))
  }, [modules])

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
        key: 'search',
        label: 'Recherche',
        type: 'search',
        placeholder: 'Code, module...',
      },
    ],
    [formationOptions]
  )

  const selectedFormations = Array.isArray(filters.formation)
    ? filters.formation
    : filters.formation
      ? [String(filters.formation)]
      : []
  const selectedSemestres = Array.isArray(filters.semestre) ? filters.semestre : []
  const modaliteFilter = (filters.modalite as string) || ''
  const minReussite = filters.reussite ? Number(filters.reussite) : undefined
  const minEffectif = filters.effectif ? Number(filters.effectif) : undefined

  const filteredModules = useMemo(() => {
    return (modules || [])
      .map((mod: ModuleAnalyse) => {
        const semCode = mod.semestre || ''
        const moduleModalite = detectModalite(semCode || mod.nom || mod.formation)
        const tauxReussite = toPercent(
          mod.taux_reussite ?? mod.taux_validation ?? (mod.taux_echec !== undefined ? 1 - mod.taux_echec : undefined)
        )
        const tauxEchec = mod.taux_echec !== undefined ? toPercent(mod.taux_echec) : 100 - tauxReussite
        const effectif = mod.nb_inscrits ?? mod.nb_notes ?? 0
        return {
          ...mod,
          _semCode: semCode,
          _modalite: moduleModalite,
          _tauxReussitePct: tauxReussite,
          _tauxEchecPct: tauxEchec,
          _effectif: effectif,
        }
      })
      .filter((mod: any) => {
        const search = typeof filters.search === 'string' ? filters.search.toLowerCase() : ''

        if (search) {
          const inCode = mod.code.toLowerCase().includes(search)
          const inName = mod.nom.toLowerCase().includes(search)
          if (!inCode && !inName) return false
        }

        if (selectedFormations.length > 0) {
          const modFormation = mod.formation || ''
          const matchesFormation = selectedFormations.some(
            (sel) => normalizeText(sel) === normalizeText(modFormation)
          )
          if (!matchesFormation) return false
        }

        if (selectedSemestres.length > 0) {
          const semNum = mod._semCode.replace('S', '')
          if (!selectedSemestres.some((s) => s.replace('S', '') === semNum)) return false
        }

        if (modaliteFilter === 'fa' && mod._modalite !== 'fa') return false
        if (modaliteFilter === 'fi' && mod._modalite === 'fa') return false

        if (minReussite !== undefined && mod._tauxReussitePct < minReussite) return false
        if (minEffectif !== undefined && mod._effectif < minEffectif) return false
        return true
      })
  }, [modules, filters.search, selectedFormations, selectedSemestres, modaliteFilter, minReussite, minEffectif])

  const sortedModules = useMemo(() => {
    return [...filteredModules].sort((a, b) => {
      const aEchec = (a as ModuleAnalyse & { _tauxEchecPct?: number })._tauxEchecPct ?? 0
      const bEchec = (b as ModuleAnalyse & { _tauxEchecPct?: number })._tauxEchecPct ?? 0
      return bEchec - aEchec
    })
  }, [filteredModules])

  const modulesAtRisk = sortedModules.filter(
    (m) =>
      m.est_module_risque ||
      ((m as ModuleAnalyse & { _tauxEchecPct?: number })._tauxEchecPct ?? 0) >= 30
  ).length
  const avgReussite =
    sortedModules.reduce(
      (acc, m) => acc + ((m as ModuleAnalyse & { _tauxReussitePct?: number })._tauxReussitePct ?? 0),
      0
    ) / (sortedModules.length || 1)
  const avgEchec =
    sortedModules.reduce(
      (acc, m) => acc + ((m as ModuleAnalyse & { _tauxEchecPct?: number })._tauxEchecPct ?? 0),
      0
    ) / (sortedModules.length || 1)

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
        Erreur lors du chargement des modules
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analyse par module</h1>
          <p className="text-gray-500 mt-1">Zoom sur les modules à risque et leurs performances</p>
        </div>
      </div>

      <FilterBar filters={filterConfigs} values={filters} onChange={setFilters} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Modules analysés"
          value={sortedModules.length}
          icon={<Target className="w-6 h-6" />}
          color="blue"
          loading={isLoading}
        />
        <StatCard
          title="Modules à risque"
          value={modulesAtRisk}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          loading={isLoading}
        />
        <StatCard
          title="Réussite moyenne"
          value={`${avgReussite.toFixed(0)}%`}
          icon={<BarChart3 className="w-6 h-6" />}
          color="green"
          loading={isLoading}
        />
        <StatCard
          title="Taux d'échec moyen"
          value={`${avgEchec.toFixed(0)}%`}
          icon={<BarChart3 className="w-6 h-6" />}
          color="yellow"
          loading={isLoading}
        />
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Liste des modules</h3>
        <DataTable
          data={sortedModules}
          emptyMessage="Aucun module ne correspond aux filtres"
          columns={[
            { key: 'code', header: 'Code' },
            { key: 'nom', header: 'Module' },
            { key: 'formation', header: 'Formation' },
            { key: 'semestre', header: 'Semestre' },
            {
              key: 'moyenne',
              header: 'Moyenne',
              align: 'right',
              render: (row: ModuleAnalyse) => (row.moyenne !== undefined ? row.moyenne.toFixed(1) : '-'),
            },
            {
              key: 'taux_reussite',
              header: 'Réussite',
              align: 'right',
              render: (row: ModuleAnalyse) => {
                const taux = (row as ModuleAnalyse & { _tauxReussitePct?: number })._tauxReussitePct ?? 0
                return <span className={taux >= 70 ? 'text-green-600' : 'text-orange-600'}>{taux.toFixed(0)}%</span>
              },
            },
            {
              key: 'taux_echec',
              header: 'Échec',
              align: 'right',
              render: (row: ModuleAnalyse) => {
                const taux = (row as ModuleAnalyse & { _tauxEchecPct?: number })._tauxEchecPct ?? 0
                return <span className={taux >= 30 ? 'text-red-600 font-medium' : 'text-gray-700'}>{taux.toFixed(0)}%</span>
              },
            },
            {
              key: 'nb_inscrits',
              header: 'Inscrits',
              align: 'right',
              render: (row: ModuleAnalyse) => row.nb_inscrits ?? row.nb_notes ?? '-',
            },
            {
              key: 'alerte',
              header: 'Alerte',
              align: 'center',
              render: (row: ModuleAnalyse) =>
                row.alerte || row.est_module_risque ? (
                  <span className="text-red-600" title={row.alerte_message || 'Module à surveiller'}>
                    ⚠️
                  </span>
                ) : (
                  <span className="text-green-600">✓</span>
                ),
            },
          ]}
        />
      </div>
    </div>
  )
}
