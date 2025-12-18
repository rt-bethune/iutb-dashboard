import { useQuery } from '@tanstack/react-query'
import { useLocation, Link } from 'react-router-dom'
import { useDepartment } from '../contexts/DepartmentContext'
import { alertesApi } from '../services/api'
import ChartContainer from '../components/ChartContainer'
import DataTable from '../components/DataTable'
import { ArrowLeft, User, AlertTriangle, Clock, GraduationCap, Award } from 'lucide-react'

type ListType = 'difficulte' | 'absents' | 'risque' | 'felicitations'

interface ProfilEtudiant {
  id: string
  nom: string
  prenom: string
  email?: string
  formation?: string
  semestre_actuel?: string
  groupe?: string
  type_bac?: string
  mention_bac?: string
  annee_bac?: number
  lycee_origine?: string
  boursier?: boolean
  moyenne_actuelle?: number
  rang_promo?: number
  rang_groupe?: number
  effectif_promo?: number
  ects_valides?: number
  ects_total?: number
  alertes?: any[]
  niveau_alerte_max?: string
}

const LIST_CONFIG: Record<ListType, {
  title: string
  description: string
  icon: React.ElementType
  iconColor: string
  emptyMessage: string
  apiCall: (department: string, params?: any) => Promise<ProfilEtudiant[]>
}> = {
  difficulte: {
    title: 'Étudiants en difficulté',
    description: 'Étudiants avec une moyenne générale inférieure à 8/20',
    icon: GraduationCap,
    iconColor: 'text-red-500',
    emptyMessage: 'Aucun étudiant en difficulté académique',
    apiCall: alertesApi.getEtudiantsEnDifficulte,
  },
  absents: {
    title: 'Étudiants absentéistes',
    description: 'Étudiants avec un taux d\'absences supérieur à 15%',
    icon: Clock,
    iconColor: 'text-orange-500',
    emptyMessage: 'Aucun étudiant avec un taux d\'absentéisme élevé',
    apiCall: alertesApi.getEtudiantsAbsents,
  },
  risque: {
    title: 'Risque de décrochage',
    description: 'Étudiants avec un score de risque supérieur à 0.6',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    emptyMessage: 'Aucun étudiant à risque de décrochage identifié',
    apiCall: alertesApi.getEtudiantsRisqueDecrochage,
  },
  felicitations: {
    title: 'Félicitations',
    description: 'Top 10% des étudiants de la promotion',
    icon: Award,
    iconColor: 'text-green-500',
    emptyMessage: 'Aucun étudiant dans le top 10%',
    apiCall: alertesApi.getFelicitations,
  },
}

// Map URL paths to list types
function getListTypeFromPath(pathname: string): ListType {
  if (pathname.includes('etudiants-en-difficulte')) return 'difficulte'
  if (pathname.includes('etudiants-absents')) return 'absents'
  if (pathname.includes('etudiants-risque-decrochage')) return 'risque'
  if (pathname.includes('felicitations')) return 'felicitations'
  return 'difficulte'
}

export default function EtudiantsListe() {
  const location = useLocation()
  const { department } = useDepartment()
  
  const listType = getListTypeFromPath(location.pathname)
  const config = LIST_CONFIG[listType]
  
  const { data: etudiants, isLoading } = useQuery({
    queryKey: ['etudiants-liste', department, listType],
    queryFn: () => config.apiCall(department),
    enabled: !!department && !!config,
  })

  if (!config) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">Type de liste invalide: {listType}</p>
          <Link to="/alertes" className="text-blue-600 hover:underline mt-2 inline-block">
            ← Retour aux alertes
          </Link>
        </div>
      </div>
    )
  }

  const Icon = config.icon

  const columns = [
    {
      key: 'etudiant',
      header: 'Étudiant',
      render: (row: ProfilEtudiant) => (
        <Link
          to={`/alertes/etudiant/${row.id}`}
          className="flex items-center gap-2 text-blue-600 hover:underline"
        >
          <User className="h-4 w-4" />
          <span className="font-medium">{row.nom} {row.prenom}</span>
        </Link>
      ),
    },
    {
      key: 'semestre_actuel',
      header: 'Semestre',
      render: (row: ProfilEtudiant) => (
        <span className="px-2 py-1 bg-gray-100 rounded text-sm">
          {row.semestre_actuel || '-'}
        </span>
      ),
    },
    {
      key: 'groupe',
      header: 'Groupe',
    },
    {
      key: 'moyenne_actuelle',
      header: 'Moyenne',
      render: (row: ProfilEtudiant) => {
        const moyenne = row.moyenne_actuelle
        if (moyenne === undefined || moyenne === null) return '-'
        const color = moyenne >= 10 ? 'text-green-600' : moyenne >= 8 ? 'text-orange-600' : 'text-red-600'
        return <span className={`font-medium ${color}`}>{moyenne.toFixed(2)}</span>
      },
    },
    {
      key: 'rang_promo',
      header: 'Rang',
      render: (row: ProfilEtudiant) => {
        if (!row.rang_promo) return '-'
        return `${row.rang_promo}/${row.effectif_promo || '?'}`
      },
    },
    {
      key: 'type_bac',
      header: 'Bac',
    },
    {
      key: 'niveau_alerte_max',
      header: 'Alerte',
      render: (row: ProfilEtudiant) => {
        const niveau = row.niveau_alerte_max
        if (!niveau) return '-'
        const colors: Record<string, string> = {
          critique: 'bg-red-100 text-red-800',
          attention: 'bg-orange-100 text-orange-800',
          info: 'bg-blue-100 text-blue-800',
        }
        return (
          <span className={`px-2 py-1 rounded text-xs font-medium ${colors[niveau] || 'bg-gray-100'}`}>
            {niveau}
          </span>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/alertes"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-3">
          <Icon className={`h-8 w-8 ${config.iconColor}`} />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{config.title}</h1>
            <p className="text-gray-500">{config.description}</p>
          </div>
        </div>
      </div>

      {/* Count */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
        <div className={`p-3 rounded-full bg-opacity-10 ${config.iconColor.replace('text-', 'bg-')}`}>
          <Icon className={`h-6 w-6 ${config.iconColor}`} />
        </div>
        <div>
          <p className="text-2xl font-bold">{etudiants?.length || 0}</p>
          <p className="text-sm text-gray-500">étudiants concernés</p>
        </div>
      </div>

      {/* Table */}
      <ChartContainer title="Liste des étudiants" loading={isLoading} height="h-auto">
        <DataTable
          columns={columns}
          data={etudiants || []}
          emptyMessage={config.emptyMessage}
        />
      </ChartContainer>
    </div>
  )
}
