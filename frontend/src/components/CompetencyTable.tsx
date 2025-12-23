import type { UEValidation } from '@/types'

export interface CompetencyTableProps {
  validations: UEValidation[]
}

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toFixed(2)
}

export default function CompetencyTable({ validations }: CompetencyTableProps) {
  if (!validations?.length) {
    return <div className="text-sm text-gray-500">Aucune UE disponible.</div>
  }

  // Sort by UE code
  const sorted = [...validations].sort((a, b) => {
    // Handle both old (competence) and new (UE) format
    const codeA = (a as any).ue_code || (a as any).competence_code || ''
    const codeB = (b as any).ue_code || (b as any).competence_code || ''
    return codeA.localeCompare(codeB)
  })

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="text-left text-gray-600 border-b">
          <tr>
            <th className="py-2 pr-4 font-medium">UE</th>
            <th className="py-2 pr-4 font-medium">Titre</th>
            <th className="py-2 pr-4 font-medium">Semestre</th>
            <th className="py-2 pr-4 font-medium">Moyenne</th>
            <th className="py-2 pr-0 font-medium">Statut</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {sorted.map((v, index) => {
            // Handle both old (competence) and new (UE) format
            const ueCode = (v as any).ue_code || (v as any).competence_code || ''
            const titre = (v as any).ue_titre || (v as any).competence_nom || ''
            const semestre = (v as any).semestre || `BUT${(v as any).annee || '?'}`
            const moyenne = (v as any).moyenne ?? (v as any).rcue

            return (
              <tr key={`${ueCode}-${index}`} className="text-gray-800">
                <td className="py-2 pr-4 font-medium">{ueCode}</td>
                <td className="py-2 pr-4">{titre || '—'}</td>
                <td className="py-2 pr-4">{semestre}</td>
                <td className="py-2 pr-4">{formatNumber(moyenne)}</td>
                <td className="py-2 pr-0">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${v.valide ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                  >
                    {v.valide ? 'Validée' : 'Non validée'}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
