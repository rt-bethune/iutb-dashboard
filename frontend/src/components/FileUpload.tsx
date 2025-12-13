import { useState, useRef, useCallback } from 'react'
import { Upload, X, File, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

export type FileType = 'budget' | 'edt' | 'parcoursup' | 'etudiants' | 'notes' | 'other'

interface FileUploadProps {
  type: FileType
  onUpload: (file: File, type: FileType, description?: string) => Promise<void>
  accept?: string
  maxSize?: number // in MB
  disabled?: boolean
}

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error'
  message?: string
  progress?: number
}

const fileTypeConfig: Record<FileType, { label: string; extensions: string[]; icon: string }> = {
  budget: { 
    label: 'Budget', 
    extensions: ['.xlsx', '.xls'],
    icon: '💰'
  },
  edt: { 
    label: 'Emploi du temps / Charges', 
    extensions: ['.xlsx', '.xls'],
    icon: '📅'
  },
  parcoursup: { 
    label: 'Parcoursup (Candidatures)', 
    extensions: ['.csv'],
    icon: '🎓'
  },
  etudiants: { 
    label: 'Liste étudiants', 
    extensions: ['.csv', '.xlsx'],
    icon: '👥'
  },
  notes: { 
    label: 'Notes / Résultats', 
    extensions: ['.csv', '.xlsx'],
    icon: '📝'
  },
  other: { 
    label: 'Autre fichier', 
    extensions: ['.xlsx', '.xls', '.csv', '.pdf'],
    icon: '📄'
  },
}

export default function FileUpload({ 
  type, 
  onUpload, 
  accept,
  maxSize = 10,
  disabled = false 
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [description, setDescription] = useState('')
  const [uploadState, setUploadState] = useState<UploadState>({ status: 'idle' })
  const inputRef = useRef<HTMLInputElement>(null)

  const config = fileTypeConfig[type]
  const acceptedExtensions = accept || config.extensions.join(',')

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const validateFile = (file: File): string | null => {
    // Check extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!config.extensions.includes(ext)) {
      return `Extension non acceptée. Extensions valides: ${config.extensions.join(', ')}`
    }
    
    // Check size
    const sizeMB = file.size / (1024 * 1024)
    if (sizeMB > maxSize) {
      return `Fichier trop volumineux (${sizeMB.toFixed(1)}MB). Maximum: ${maxSize}MB`
    }
    
    return null
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (disabled) return

    const file = e.dataTransfer.files?.[0]
    if (file) {
      const error = validateFile(file)
      if (error) {
        setUploadState({ status: 'error', message: error })
      } else {
        setSelectedFile(file)
        setUploadState({ status: 'idle' })
      }
    }
  }, [disabled, maxSize, config.extensions])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const error = validateFile(file)
      if (error) {
        setUploadState({ status: 'error', message: error })
        setSelectedFile(null)
      } else {
        setSelectedFile(file)
        setUploadState({ status: 'idle' })
      }
    }
  }

  const handleSubmit = async () => {
    if (!selectedFile) return

    setUploadState({ status: 'uploading', progress: 0 })
    
    try {
      await onUpload(selectedFile, type, description || undefined)
      setUploadState({ status: 'success', message: 'Fichier uploadé avec succès!' })
      setSelectedFile(null)
      setDescription('')
      
      // Reset after 3 seconds
      setTimeout(() => {
        setUploadState({ status: 'idle' })
      }, 3000)
    } catch (error: any) {
      setUploadState({ 
        status: 'error', 
        message: error.response?.data?.detail || error.message || 'Erreur lors de l\'upload' 
      })
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setUploadState({ status: 'idle' })
    setDescription('')
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">{config.icon}</span>
        <div>
          <h3 className="font-semibold text-gray-900">{config.label}</h3>
          <p className="text-sm text-gray-500">
            Formats acceptés: {config.extensions.join(', ')} (max {maxSize}MB)
          </p>
        </div>
      </div>

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200
          ${dragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          ${uploadState.status === 'success' ? 'border-green-500 bg-green-50' : ''}
          ${uploadState.status === 'error' ? 'border-red-500 bg-red-50' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptedExtensions}
          onChange={handleChange}
          disabled={disabled}
          className="hidden"
        />

        {uploadState.status === 'uploading' ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
            <p className="text-gray-600">Upload en cours...</p>
          </div>
        ) : uploadState.status === 'success' ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle className="w-12 h-12 text-green-500" />
            <p className="text-green-600 font-medium">{uploadState.message}</p>
          </div>
        ) : selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            <File className="w-12 h-12 text-primary-500" />
            <div>
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className={`w-12 h-12 ${dragActive ? 'text-primary-500' : 'text-gray-400'}`} />
            <div>
              <p className="text-gray-600">
                <span className="font-medium text-primary-600">Cliquez pour sélectionner</span>
                {' '}ou glissez-déposez
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {config.extensions.join(', ')} jusqu'à {maxSize}MB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {uploadState.status === 'error' && (
        <div className="mt-4 flex items-center gap-2 text-red-600">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{uploadState.message}</p>
        </div>
      )}

      {/* Description field and actions */}
      {selectedFile && uploadState.status === 'idle' && (
        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (optionnel)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex: Budget 2024-2025 version finale"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleSubmit}
              disabled={disabled}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              Uploader
            </button>
            <button
              onClick={handleClear}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
