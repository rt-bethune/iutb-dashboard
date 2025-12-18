import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '../contexts/DepartmentContext'
import { useAuth } from '../contexts/AuthContext'
import ChartContainer from '../components/ChartContainer'
import api from '../services/api'
import {
  User,
  AlertTriangle,
  AlertCircle,
  Info,
  TrendingUp,
  TrendingDown,
  CheckCircle,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'

interface FicheEtudiant {
  profil: {
    id: string
    nom: string
    prenom: string
    email: string
    formation: string
    semestre_actuel: string
    groupe: string
    type_bac: string
    mention_bac: string
    annee_bac: number
    lycee_origine: string
    boursier: boolean
    moyenne_actuelle: number
    rang_promo: number
    rang_groupe: number
    effectif_promo: number
    ects_valides: number
    ects_total: number
    niveau_alerte_max: string | null
    notes_modules: Array<{
      code: string
      nom: string
      moyenne: number
      rang: number
    }>
    alertes: Array<{
      type_alerte: string
      niveau: string
      message: string
      date_detection: string
    }>
    statistiques_absences: {
      total_absences: number
      absences_justifiees: number
      absences_non_justifiees: number
      taux_absenteisme: number
      taux_justification: number
      absences_par_module: Record<string, number>
      absences_par_jour_semaine: Record<string, number>
      tendance: string
    }
    score_risque: {
      score_global: number
      facteurs: Record<string, number>
      probabilite_validation: number
      recommandations: string[]
    }
  }
  historique_semestres: Array<{
    semestre: string
    annee: string
    moyenne: number
    rang: number
    decision: string
    ects: number
  }>
  recommandations_personnalisees: string[]
}

const NIVEAU_COLORS = {
  critique: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
  attention: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
  info: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
}

const NiveauIcon = ({ niveau }: { niveau: string }) => {
  switch (niveau) {
    case 'critique':
      return <AlertCircle className="h-5 w-5 text-red-600" />
    case 'attention':
      return <AlertTriangle className="h-5 w-5 text-orange-600" />
    default:
      return <Info className="h-5 w-5 text-blue-600" />
  }
}

export default function FicheEtudiantPage() {
  const { etudiantId } = useParams<{ etudiantId: string }>()
  const { department } = useDepartment()
  const { checkPermission } = useAuth()

  const canView = checkPermission(department, 'can_view_scolarite')

  const { data: fiche, isLoading } = useQuery({
    queryKey: ['fiche-etudiant', department, etudiantId],
    queryFn: () => api.get<FicheEtudiant>(`/${department}/alertes/etudiant/${etudiantId}`).then(res => res.data),
    enabled: canView && !!etudiantId,
  })

  if (!canView) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto text-yellow-500" />
        <p className="mt-4 text-gray-600">Accès non autorisé.</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Chargement...</p>
      </div>
    )
  }

  if (!fiche) {
    return (
      <div className="text-center py-12">
        <User className="h-12 w-12 mx-auto text-gray-400" />
        <p className="mt-4 text-gray-600">Étudiant non trouvé.</p>
      </div>
    )
  }

  const { profil, historique_semestres, recommandations_personnalisees } = fiche
  const { alertes, statistiques_absences, score_risque } = profil

  // Type definitions for array elements
  interface NoteModule {
    code: string
    nom: string
    moyenne: number
    rang: number
  }
  
  interface HistoriqueSemestre {
    semestre: string
    annee: string
    moyenne: number
    rang: number
    decision: string
    ects: number
  }
  
  interface AlerteType {
    type_alerte: string
    niveau: string
    message: string
    date_detection: string
  }

  // Prepare charts data
  const notesChartData = profil.notes_modules 
    ? profil.notes_modules.map((m: NoteModule) => ({
        module: m.code,
        note: m.moyenne,
        rang: m.rang,
      }))
    : []

  const absencesJourData = statistiques_absences?.absences_par_jour_semaine
    ? Object.entries(statistiques_absences.absences_par_jour_semaine).map(
        ([jour, nb]) => ({
          jour: jour.charAt(0).toUpperCase() + jour.slice(1),
          absences: nb as number,
        })
      )
    : []

  const riskFactorsData = score_risque?.facteurs
    ? Object.entries(score_risque.facteurs).map(([facteur, scoreVal]) => ({
        facteur: facteur.replace(/_/g, ' '),
        score: ((scoreVal as number) * 100).toFixed(0),
        fullMark: 100,
      }))
    : []

  const historiqueData = historique_semestres 
    ? historique_semestres.map((s: HistoriqueSemestre) => ({
        semestre: s.semestre,
        moyenne: s.moyenne,
        rang: s.rang,
      }))
    : []

  return (
    <div className="space-y-6">
      {/* Header with student info */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center">
            <div className="h-16 w-16 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="h-8 w-8 text-gray-500" />
            </div>
            <div className="ml-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {profil.nom} {profil.prenom}
              </h1>
              <p className="text-gray-500">
                {profil.formation} - {profil.semestre_actuel} - Groupe {profil.groupe}
              </p>
              <p className="text-sm text-gray-400">{profil.email}</p>
            </div>
          </div>
          {profil.niveau_alerte_max && (
            <div
              className={`px-4 py-2 rounded-lg ${
                NIVEAU_COLORS[profil.niveau_alerte_max as keyof typeof NIVEAU_COLORS]?.bg || 'bg-gray-100'
              } ${NIVEAU_COLORS[profil.niveau_alerte_max as keyof typeof NIVEAU_COLORS]?.text || 'text-gray-800'}`}
            >
              <div className="flex items-center">
                <NiveauIcon niveau={profil.niveau_alerte_max} />
                <span className="ml-2 font-medium capitalize">{profil.niveau_alerte_max}</span>
              </div>
            </div>
          )}
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mt-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{profil.moyenne_actuelle.toFixed(1)}</p>
            <p className="text-sm text-gray-500">Moyenne</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">
              {profil.rang_promo}/{profil.effectif_promo}
            </p>
            <p className="text-sm text-gray-500">Rang promo</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">
              {profil.ects_valides}/{profil.ects_total}
            </p>
            <p className="text-sm text-gray-500">ECTS</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{profil.type_bac}</p>
            <p className="text-sm text-gray-500">Bac {profil.annee_bac}</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{profil.mention_bac}</p>
            <p className="text-sm text-gray-500">Mention bac</p>
          </div>
          <div className="text-center">
            <p className={`text-2xl font-bold ${profil.boursier ? 'text-green-600' : 'text-gray-400'}`}>
              {profil.boursier ? 'Oui' : 'Non'}
            </p>
            <p className="text-sm text-gray-500">Boursier</p>
          </div>
        </div>
      </div>

      {/* Alerts section */}
      {alertes && alertes.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-orange-500" />
            Alertes actives ({alertes.length})
          </h2>
          <div className="space-y-3">
            {alertes.map((alerte: AlerteType, index: number) => {
              const colors = NIVEAU_COLORS[alerte.niveau as keyof typeof NIVEAU_COLORS] || NIVEAU_COLORS.info
              return (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${colors.bg} ${colors.border}`}
                >
                  <div className="flex items-center">
                    <NiveauIcon niveau={alerte.niveau} />
                    <span className={`ml-2 font-medium ${colors.text}`}>
                      {alerte.type_alerte.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-700">{alerte.message}</p>
                  <p className="mt-1 text-xs text-gray-500">Détecté le {alerte.date_detection}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Risk score and recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risk score */}
        {score_risque && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Score de risque</h2>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-4xl font-bold text-gray-900">
                  {(score_risque.score_global * 100).toFixed(0)}%
                </p>
                <p className="text-sm text-gray-500">Score de risque</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-600">
                  {(score_risque.probabilite_validation * 100).toFixed(0)}%
                </p>
                <p className="text-sm text-gray-500">Probabilité validation</p>
              </div>
            </div>
            {riskFactorsData.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={riskFactorsData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="facteur" tick={{ fontSize: 10 }} />
                  <PolarRadiusAxis domain={[0, 100]} />
                  <Radar
                    name="Score"
                    dataKey="score"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.5}
                  />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        {/* Recommendations */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Recommandations</h2>
          {recommandations_personnalisees && recommandations_personnalisees.length > 0 ? (
            <ul className="space-y-3">
              {recommandations_personnalisees.map((rec: string, index: number) => (
                <li key={index} className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Aucune recommandation pour cet étudiant.</p>
          )}
          {score_risque?.recommandations && score_risque.recommandations.length > 0 && (
            <>
              <h3 className="text-sm font-medium text-gray-500 mt-4 mb-2">Actions suggérées :</h3>
              <ul className="space-y-2">
                {score_risque.recommandations.map((rec: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <TrendingUp className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-600">{rec}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      {/* Notes by module */}
      {notesChartData.length > 0 && (
        <ChartContainer title="Notes par module">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={notesChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="module" />
              <YAxis domain={[0, 20]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="note" name="Note" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      )}

      {/* Absences */}
      {statistiques_absences && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Statistiques d'absences</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded">
                <p className="text-2xl font-bold">{statistiques_absences.total_absences}</p>
                <p className="text-sm text-gray-500">Total absences</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded">
                <p className="text-2xl font-bold text-orange-600">
                  {(statistiques_absences.taux_absenteisme * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500">Taux absentéisme</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <p className="text-2xl font-bold text-green-600">
                  {statistiques_absences.absences_justifiees}
                </p>
                <p className="text-sm text-gray-500">Justifiées</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded">
                <p className="text-2xl font-bold text-red-600">
                  {statistiques_absences.absences_non_justifiees}
                </p>
                <p className="text-sm text-gray-500">Non justifiées</p>
              </div>
            </div>
            <div className="mt-4 flex items-center">
              <span className="text-sm text-gray-500">Tendance :</span>
              <span
                className={`ml-2 flex items-center ${
                  statistiques_absences.tendance === 'hausse'
                    ? 'text-red-600'
                    : statistiques_absences.tendance === 'baisse'
                    ? 'text-green-600'
                    : 'text-gray-600'
                }`}
              >
                {statistiques_absences.tendance === 'hausse' ? (
                  <TrendingUp className="h-4 w-4 mr-1" />
                ) : statistiques_absences.tendance === 'baisse' ? (
                  <TrendingDown className="h-4 w-4 mr-1" />
                ) : null}
                {statistiques_absences.tendance}
              </span>
            </div>
          </div>

          {absencesJourData.length > 0 && (
            <ChartContainer title="Absences par jour">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={absencesJourData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="jour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="absences" fill="#f97316" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}
        </div>
      )}

      {/* Historical progression */}
      {historique_semestres && historique_semestres.length > 1 && (
        <ChartContainer title="Progression sur les semestres">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={historiqueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semestre" />
              <YAxis domain={[0, 20]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="moyenne"
                name="Moyenne"
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      )}

      {/* Origin info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Origine scolaire</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Type de bac</p>
            <p className="font-medium">{profil.type_bac}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Mention</p>
            <p className="font-medium">{profil.mention_bac}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Année du bac</p>
            <p className="font-medium">{profil.annee_bac}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Lycée d'origine</p>
            <p className="font-medium">{profil.lycee_origine}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
