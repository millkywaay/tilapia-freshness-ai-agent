import { useRef, useState } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import UploadCard from '../components/UploadCard'
import { ErrorState, LoadingState } from '../components/FeedbackState'
import { ResultSummary } from '../components/PredictionResult'
import { normalizePrediction } from '../utils/prediction'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function Detect() {
  const [eyeFile, setEyeFile] = useState(null)
  const [gillFile, setGillFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const resultRef = useRef(null)
  const bothReady = Boolean(eyeFile && gillFile)

  const handleSubmit = async () => {
    if (!bothReady) {
      setError('Unggah foto mata dan insang terlebih dahulu.')
      return
    }

    setError('')
    setResult(null)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('eye_image', eyeFile)
      formData.append('gill_image', gillFile)
      const response = await axios.post(`${API_URL}/predict`, formData)
      setResult(normalizePrediction(response.data))
      window.setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Analisis gagal. Pastikan backend berjalan dan coba kembali.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setEyeFile(null)
    setGillFile(null)
    setResult(null)
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <main className="detect-page page-container">
      <div className="page-heading">
        <Link to="/" className="back-link">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>
          Beranda
        </Link>
        <span className="eyebrow">Analisis kesegaran</span>
        <h1>Periksa mata dan insang ikan</h1>
        <p>Gunakan dua foto yang terang dan fokus. Setiap organ dianalisis secara terpisah sebelum hasilnya digabungkan.</p>
      </div>

      <div className="upload-grid">
        <UploadCard
          label="Foto mata"
          description="Pastikan area mata terlihat jelas dan tidak terpotong."
          file={eyeFile}
          onChange={(file) => { setEyeFile(file); setError(''); setResult(null) }}
          onRemove={() => { setEyeFile(null); setResult(null) }}
        />
        <UploadCard
          label="Foto insang"
          description="Buka insang dan ambil warna permukaannya dengan jelas."
          file={gillFile}
          onChange={(file) => { setGillFile(file); setError(''); setResult(null) }}
          onRemove={() => { setGillFile(null); setResult(null) }}
        />
      </div>

      <div className="analysis-panel">
        <div><strong>{bothReady ? 'Kedua foto siap dianalisis' : 'Diperlukan dua foto'}</strong><span>Format gambar akan disiapkan otomatis oleh sistem.</span></div>
        <button type="button" className="button" disabled={!bothReady || loading} onClick={handleSubmit}>
          {loading ? 'Sedang menganalisis…' : 'Mulai deteksi'}
        </button>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} />}
      <div ref={resultRef}>{result && <ResultSummary prediction={result} onReset={handleReset} />}</div>
    </main>
  )
}

export default Detect
