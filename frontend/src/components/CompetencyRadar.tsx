import { useMemo } from 'react'
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from 'recharts'

export interface CompetencyRadarDatum {
  competence: string
  taux: number // 0..1
}

export interface CompetencyRadarProps {
  data: CompetencyRadarDatum[]
}

export default function CompetencyRadar({ data }: CompetencyRadarProps) {
  const chartData = useMemo(
    () =>
      (data || []).map((d) => ({
        competence: d.competence,
        taux: Math.round(Math.max(0, Math.min(1, d.taux || 0)) * 100),
      })),
    [data]
  )

  if (!chartData.length) {
    return <div className="h-full flex items-center justify-center text-sm text-gray-500">Aucune donnée</div>
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={chartData}>
        <PolarGrid />
        <PolarAngleAxis dataKey="competence" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
        <Tooltip formatter={(v) => `${v}%`} />
        <Radar
          name="Validation"
          dataKey="taux"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.35}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
