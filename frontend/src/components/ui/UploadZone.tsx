import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, CheckCircle, XCircle } from 'lucide-react'
import { uploadCSV } from '../../services/endpoints'

type UploadState = 'idle' | 'uploading' | 'success' | 'error'

export default function UploadZone() {
  const [state, setState] = useState<UploadState>('idle')
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const navigate = useNavigate()

  const processFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setError('Only CSV files are accepted.')
      setState('error')
      return
    }
    setState('uploading')
    setError('')
    try {
      const report = await uploadCSV(file)
      setState('success')
      setTimeout(() => navigate(`/imports/${report.id}`), 1200)
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Upload failed. Please try again.')
      setState('error')
    }
  }, [navigate])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) processFile(file)
  }, [processFile])

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) processFile(file)
  }

  return (
    <div
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      className={`
        border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer
        ${dragging ? 'border-indigo-500 bg-indigo-900/20' : 'border-gray-700 hover:border-gray-500'}
        ${state === 'success' ? 'border-green-600 bg-green-900/10' : ''}
        ${state === 'error' ? 'border-red-600 bg-red-900/10' : ''}
      `}
    >
      <label className="cursor-pointer block">
        <input type="file" accept=".csv" onChange={onFileInput} className="sr-only" id="csv-upload" />

        {state === 'idle' && (
          <>
            <Upload className="mx-auto text-gray-500 mb-4" size={40} />
            <p className="text-gray-300 font-medium">Drop your expense CSV here</p>
            <p className="text-gray-500 text-sm mt-1">or click to browse · max 10 MB</p>
          </>
        )}

        {state === 'uploading' && (
          <>
            <FileText className="mx-auto text-indigo-400 mb-4 animate-pulse" size={40} />
            <p className="text-indigo-300 font-medium">Processing CSV…</p>
            <p className="text-gray-500 text-sm mt-1">Running validation and anomaly detection</p>
          </>
        )}

        {state === 'success' && (
          <>
            <CheckCircle className="mx-auto text-green-400 mb-4" size={40} />
            <p className="text-green-300 font-medium">Import complete!</p>
            <p className="text-gray-500 text-sm mt-1">Redirecting to report…</p>
          </>
        )}

        {state === 'error' && (
          <>
            <XCircle className="mx-auto text-red-400 mb-4" size={40} />
            <p className="text-red-300 font-medium">Upload failed</p>
            <p className="text-gray-500 text-sm mt-1">{error}</p>
            <button
              onClick={(e) => { e.preventDefault(); setState('idle') }}
              className="mt-4 px-4 py-2 bg-gray-700 text-gray-200 rounded-lg text-sm hover:bg-gray-600 transition"
            >
              Try again
            </button>
          </>
        )}
      </label>
    </div>
  )
}
