import { useCallback, useRef, useState } from 'react'
import { Download, FileImage, FileText, Loader2 } from 'lucide-react'

interface ExportButtonProps {
  chartRef: React.RefObject<HTMLDivElement>
  filename?: string
  title?: string
}

export default function ExportButton({ chartRef, filename = 'chart', title }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const exportToPNG = useCallback(async () => {
    if (!chartRef.current) return
    setIsExporting(true)

    try {
      // Dynamic import for html2canvas
      const html2canvas = (await import('html2canvas')).default
      
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2, // Higher resolution
        logging: false,
        useCORS: true,
      })

      // Create download link
      const link = document.createElement('a')
      link.download = `${filename}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } catch (error) {
      console.error('Export PNG failed:', error)
      alert('Erreur lors de l\'export PNG')
    } finally {
      setIsExporting(false)
      setShowMenu(false)
    }
  }, [chartRef, filename])

  const exportToPDF = useCallback(async () => {
    if (!chartRef.current) return
    setIsExporting(true)

    try {
      // Dynamic imports
      const html2canvas = (await import('html2canvas')).default
      const { jsPDF } = await import('jspdf')

      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        logging: false,
        useCORS: true,
      })

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({
        orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
        unit: 'px',
        format: [canvas.width, canvas.height]
      })

      // Add title if provided
      if (title) {
        pdf.setFontSize(16)
        pdf.text(title, 20, 30)
      }

      pdf.addImage(imgData, 'PNG', 0, title ? 40 : 0, canvas.width, canvas.height)
      pdf.save(`${filename}.pdf`)
    } catch (error) {
      console.error('Export PDF failed:', error)
      alert('Erreur lors de l\'export PDF')
    } finally {
      setIsExporting(false)
      setShowMenu(false)
    }
  }, [chartRef, filename, title])

  const exportToSVG = useCallback(() => {
    if (!chartRef.current) return
    
    // Find SVG element inside the chart
    const svgElement = chartRef.current.querySelector('svg')
    if (!svgElement) {
      alert('Aucun graphique SVG trouvé')
      return
    }

    try {
      // Clone and prepare SVG
      const clonedSvg = svgElement.cloneNode(true) as SVGElement
      clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
      
      // Serialize to string
      const serializer = new XMLSerializer()
      const svgString = serializer.serializeToString(clonedSvg)
      
      // Create blob and download
      const blob = new Blob([svgString], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.download = `${filename}.svg`
      link.href = url
      link.click()
      
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export SVG failed:', error)
      alert('Erreur lors de l\'export SVG')
    }
    
    setShowMenu(false)
  }, [chartRef, filename])

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={isExporting}
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        Exporter
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          <button
            onClick={exportToPNG}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 first:rounded-t-lg"
          >
            <FileImage className="w-4 h-4" />
            Export PNG
          </button>
          <button
            onClick={exportToPDF}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            <FileText className="w-4 h-4" />
            Export PDF
          </button>
          <button
            onClick={exportToSVG}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 last:rounded-b-lg"
          >
            <FileImage className="w-4 h-4" />
            Export SVG
          </button>
        </div>
      )}
    </div>
  )
}

// Hook for creating chart ref and export functionality
export function useChartExport(filename?: string) {
  const chartRef = useRef<HTMLDivElement>(null)
  
  return {
    chartRef,
    ExportButton: () => <ExportButton chartRef={chartRef} filename={filename} />
  }
}
