import { ReactNode, useRef } from 'react'
import ExportButton from './ExportButton'

interface ChartContainerProps {
  title: string
  subtitle?: string
  children: ReactNode
  actions?: ReactNode
  exportFilename?: string
  showExport?: boolean
}

export default function ChartContainer({ 
  title, 
  subtitle, 
  children, 
  actions,
  exportFilename,
  showExport = true
}: ChartContainerProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {actions}
          {showExport && (
            <ExportButton 
              chartRef={chartRef} 
              filename={exportFilename || title.toLowerCase().replace(/\s+/g, '-')} 
              title={title}
            />
          )}
        </div>
      </div>
      <div className="h-72" ref={chartRef}>
        {children}
      </div>
    </div>
  )
}
