import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUp, UploadCloud } from 'lucide-react'
import { Card } from '../components/common/Card'
import { ErrorState } from '../components/common/ErrorState'
import { useUploadDataset } from '../hooks/useDataset'
import { formatBytes } from '../utils/format'

export function UploadPage() {
  const navigate = useNavigate()
  const uploadMutation = useUploadDataset()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [datasetName, setDatasetName] = useState('')
  const [description, setDescription] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (selectedFile && !datasetName.trim()) {
      setDatasetName(selectedFile.name.replace(/\.csv$/i, ''))
    }
  }, [datasetName, selectedFile])

  const fileSummary = useMemo(() => {
    if (!selectedFile) {
      return null
    }

    return {
      name: selectedFile.name,
      size: formatBytes(selectedFile.size),
    }
  }, [selectedFile])

  function validateFile(file: File): string | null {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return 'Only CSV files are supported.'
    }
    return null
  }

  function handleFile(file: File) {
    const error = validateFile(file)
    if (error) {
      setValidationError(error)
      setSelectedFile(null)
      return
    }

    setValidationError(null)
    setSelectedFile(file)
    setProgress(0)
  }

  async function handleUpload() {
    if (!selectedFile) {
      setValidationError('Choose a CSV file before uploading.')
      return
    }

    if (!datasetName.trim()) {
      setValidationError('Provide a dataset name.')
      return
    }

    setValidationError(null)

    try {
      const uploaded = await uploadMutation.mutateAsync({
        input: {
          file: selectedFile,
          name: datasetName.trim(),
          description: description.trim() || undefined,
        },
        onProgress: setProgress,
      })
      navigate(`/datasets/${uploaded.id}`)
    } catch {
      // Error state is handled below.
    }
  }

  return (
    <div className="upload-page">
      <Card
        title="Upload a CSV dataset"
        subtitle="Drop a CSV file or browse your computer. The upload will redirect to the analytics view."
      >
        <div
          className={`upload-dropzone ${dragActive ? 'is-active' : ''}`}
          onDragOver={(event) => {
            event.preventDefault()
            setDragActive(true)
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragActive(false)
            const file = event.dataTransfer.files[0]
            if (file) {
              handleFile(file)
            }
          }}
        >
          <UploadCloud size={34} />
          <div>
            <strong>Drop your CSV here</strong>
            <p>or browse files from your device.</p>
          </div>
          <label className="button button--secondary upload-dropzone__button">
            <FileUp size={16} />
            Browse files
            <input
              hidden
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                const file = event.target.files?.[0]
                if (file) {
                  handleFile(file)
                }
              }}
            />
          </label>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>Dataset name</span>
            <input
              value={datasetName}
              onChange={(event) => setDatasetName(event.target.value)}
              placeholder="Sales summary Q3"
            />
          </label>

          <label className="field field--full">
            <span>Description</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional notes about this dataset"
              rows={4}
            />
          </label>
        </div>

        {validationError ? <div className="form-message form-message--error">{validationError}</div> : null}
        {uploadMutation.error ? (
          <ErrorState title="Upload failed" message={uploadMutation.error.message} onRetry={handleUpload} />
        ) : null}

        {fileSummary ? (
          <div className="file-summary">
            <div>
              <strong>{fileSummary.name}</strong>
              <span>{fileSummary.size}</span>
            </div>
            <button type="button" className="button button--ghost" onClick={() => setSelectedFile(null)}>
              Remove
            </button>
          </div>
        ) : null}

        <div className="upload-progress">
          <div className="upload-progress__bar" style={{ width: `${progress}%` }} />
        </div>

        <div className="upload-footer">
          <span>Only CSV files are accepted.</span>
          <button
            type="button"
            className="button button--primary"
            onClick={() => void handleUpload()}
            disabled={!selectedFile || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Start upload'}
          </button>
        </div>
      </Card>
    </div>
  )
}