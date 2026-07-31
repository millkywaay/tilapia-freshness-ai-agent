import { motion, useReducedMotion } from 'framer-motion'
import { formatConfidence, LABELS } from '../utils/prediction'

/* ── Helpers ─────────────────────────────────────────────────────── */
function statusClass(label) {
  if (label === LABELS.FRESH) return 'fresh'
  if (label === LABELS.STALE) return 'stale'
  return 'review'
}

function statusLabel(label) {
  if (label === LABELS.FRESH) return 'Segar'
  if (label === LABELS.STALE) return 'Tidak Segar'
  return 'Perlu Pemeriksaan'
}

/* ── Organ Prediction Card ───────────────────────────────────────── */
export function PredictionCard({ title, prediction }) {
  const width = Number.isFinite(prediction.confidence) ? prediction.confidence * 100 : 0
  const tone = statusClass(prediction.label)

  return (
    <article className="prediction-card">
      <div className="prediction-heading">
        <span>{title}</span>
        <span className={`status ${tone}`}>{statusLabel(prediction.label)}</span>
      </div>
      <div className="confidence-row">
        <span>Skor prediksi</span>
        <strong>{formatConfidence(prediction.confidence)}</strong>
      </div>
      <div className="confidence-track" aria-hidden="true">
        <span className={tone} style={{ width: `${width}%` }} />
      </div>
      <p className="confidence-label">Keyakinan prediksi model untuk organ ini</p>
    </article>
  )
}

/* ── AI Interpretation Card ──────────────────────────────────────── */
export function AIExplanationCard({ explanation }) {
  const reduceMotion = useReducedMotion()
  const lines = String(explanation || '').split('\n').map((l) => l.trim()).filter(Boolean)

  const parsedSections = lines.map((line) => {
    const match = line.match(/^\*{0,2}(Kondisi organ|Kesimpulan|Rekomendasi)\s*:\*{0,2}\s*(.+)$/i)
    return match ? { label: match[1], content: match[2] } : null
  }).filter(Boolean)

  const sections = parsedSections.length
    ? parsedSections
    : [{ label: 'Analisis', content: explanation }]

  return (
    <motion.article
      className="explanation-card"
      initial={reduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
    >
      <header className="explanation-header">
        <div className="explanation-title">
          <div className="explanation-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M12 3a7 7 0 0 0-4.5 12.36V19h9v-3.64A7 7 0 0 0 12 3Z"/>
              <path d="M9 22h6M9 10.5h.01M15 10.5h.01M9.5 13.5c1.7 1.3 3.3 1.3 5 0"/>
            </svg>
          </div>
          <div className="explanation-title-text">
            <h3>Penjelasan hasil pemeriksaan</h3>
            <small>Analisis berbasis AI · DeepSeek</small>
          </div>
        </div>
        <span className="ai-status">
          <span aria-hidden="true" />
          Analisis selesai
        </span>
      </header>

      <div className="explanation-sections">
        {sections.map((section, index) => {
          const isRecommendation = /rekomendasi/i.test(section.label)
          return (
            <motion.section
              className={`explanation-section${isRecommendation ? ' recommendation-section' : ''}`}
              key={`${section.label}-${index}`}
              initial={reduceMotion ? false : { opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.28 + index * 0.09 }}
            >
              <span className="explanation-index">0{index + 1}</span>
              <div>
                <h4>{section.label}</h4>
                <p>{section.content}</p>
              </div>
            </motion.section>
          )
        })}
      </div>

      <footer className="explanation-note">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9"/>
          <path d="M12 11v5M12 8h.01"/>
        </svg>
        <span>
          Hasil berbasis citra merupakan informasi pendukung.
          Tetap periksa aroma, tekstur, warna, dan kondisi fisik ikan sebelum dikonsumsi.
        </span>
      </footer>
    </motion.article>
  )
}

/* ── Full Result Summary ─────────────────────────────────────────── */
export function ResultSummary({ prediction, onReset }) {
  const tone = statusClass(prediction.final.label)
  const confidencePct = Number.isFinite(prediction.final.confidence)
    ? prediction.final.confidence * 100
    : 0
  const eyeTone = statusClass(prediction.eye.label)
  const gillTone = statusClass(prediction.gill.label)
  const hasConflict = prediction.eye.label !== prediction.gill.label

  return (
    <section className="result-section" aria-live="polite">

      {/* ── Final Result Card ── */}
      <motion.div
        className={`result-summary ${tone}`}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="result-summary-body">
          <span className="eyebrow">Hasil akhir ensemble</span>
          <h2>{statusLabel(prediction.final.label)}</h2>
          <p>Gabungan analisis citra mata dan insang.</p>
        </div>

        <div className="final-confidence">
          <span>Keyakinan prediksi</span>
          <strong>{formatConfidence(prediction.final.confidence)}</strong>
          <div className="final-confidence-bar" aria-hidden="true">
            <span style={{ width: `${confidencePct}%` }} />
          </div>
        </div>
      </motion.div>

      {/* ── Conflict Warning ── */}
      {hasConflict && (
        <motion.div
          className="conflict-warning"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span>
            <strong>Catatan:</strong> Hasil analisis mata dan insang tidak selaras.
            Sistem menggunakan aturan ensemble untuk menentukan keputusan akhir.
            Disarankan untuk melakukan pemeriksaan fisik tambahan.
          </span>
        </motion.div>
      )}

      {/* ── Organ Detail Cards ── */}
      <div className="prediction-grid">
        <PredictionCard title="Analisis mata" prediction={prediction.eye} />
        <PredictionCard title="Analisis insang" prediction={prediction.gill} />
      </div>

      {/* ── AI Interpretation ── */}
      <AIExplanationCard explanation={prediction.explanation} />

      {/* ── Reset ── */}
      <button
        type="button"
        className="button button-secondary reset-button"
        onClick={onReset}
      >
        Mulai analisis baru
      </button>
    </section>
  )
}
