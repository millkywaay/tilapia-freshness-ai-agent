import { useEffect, useId, useRef, useState } from 'react'

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  )
}

function ImagePreview({ file, label, onRemove }) {
  const [previewUrl, setPreviewUrl] = useState('')

  useEffect(() => {
    let isMounted = true
    const reader = new FileReader()

    reader.onload = () => {
      if (isMounted) setPreviewUrl(reader.result || '')
    }
    reader.onerror = () => {
      if (isMounted) setPreviewUrl('')
    }
    reader.readAsDataURL(file)

    return () => {
      isMounted = false
      if (reader.readyState === FileReader.LOADING) reader.abort()
    }
  }, [file])

  return (
    <div className="image-preview">
      {previewUrl
        ? <img className="preview-image" src={previewUrl} alt={`Pratinjau ${label.toLowerCase()}`} />
        : null}
      <div className="preview-meta">
        <span title={file.name}>{file.name}</span>
        <button type="button" onClick={onRemove}>Hapus</button>
      </div>
    </div>
  )
}

function UploadCard({ label, description, hint, file, onChange, onRemove }) {
  const inputId = useId()
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const selectFile = (nextFile) => {
    const hasImageType = nextFile?.type?.startsWith('image/')
    const hasImageExtension = /\.(jpe?g|png|webp)$/i.test(nextFile?.name || '')
    if (hasImageType || hasImageExtension) onChange(nextFile)
  }

  const removeFile = () => {
    if (inputRef.current) inputRef.current.value = ''
    onRemove()
  }

  return (
    <section className={`upload-card ${dragging ? 'is-dragging' : ''} ${file ? 'has-file' : ''}`}>
      <div className="upload-card-heading">
        <div>
          <span className="eyebrow">Input citra</span>
          <h2>{label}</h2>
        </div>
        {file && <span className="ready-badge">Siap</span>}
      </div>

      {file ? (
        <ImagePreview file={file} label={label} onRemove={removeFile} />
      ) : (
        <button
          type="button"
          className="drop-zone"
          onClick={() => inputRef.current?.click()}
          onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragging(false)
            selectFile(event.dataTransfer.files[0])
          }}
        >
          <span className="upload-icon"><UploadIcon /></span>
          <strong>Pilih atau letakkan foto</strong>
          <span>{description}</span>
          <span className="file-hint">JPG · PNG · WEBP</span>
        </button>
      )}

      {hint && (
        <p className="upload-hint">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9"/>
            <path d="M12 11v5M12 8h.01"/>
          </svg>
          {hint}
        </p>
      )}

      <input
        id={inputId}
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        hidden
        onChange={(event) => selectFile(event.target.files[0])}
      />
    </section>
  )
}

export default UploadCard
