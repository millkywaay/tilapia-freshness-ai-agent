import { motion, useReducedMotion } from 'framer-motion'
import { formatConfidence, LABELS } from '../utils/prediction'

function statusClass(label) {
  if (label === LABELS.FRESH) return 'fresh'
  if (label === LABELS.STALE) return 'stale'
  return 'review'
}

export function PredictionCard({ title, prediction }) {
  const width = Number.isFinite(prediction.confidence) ? prediction.confidence * 100 : 0
  return (
    <article className="prediction-card">
      <div className="prediction-heading"><span>{title}</span><span className={`status ${statusClass(prediction.label)}`}>{prediction.label}</span></div>
      <div className="confidence-row"><span>Confidence</span><strong>{formatConfidence(prediction.confidence)}</strong></div>
      <div className="confidence-track" aria-hidden="true"><span className={statusClass(prediction.label)} style={{ width: `${width}%` }} /></div>
    </article>
  )
}

export function AIExplanationCard({ explanation }) {
  const reduceMotion = useReducedMotion()
  const lines = String(explanation || '').split('\n').map((line) => line.trim()).filter(Boolean)
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
          <div className="explanation-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3a7 7 0 0 0-4.5 12.36V19h9v-3.64A7 7 0 0 0 12 3Z"/><path d="M9 22h6M9 10.5h.01M15 10.5h.01M9.5 13.5c1.7 1.3 3.3 1.3 5 0"/></svg></div>
          <div><span className="eyebrow">Penjelasan hasil</span><h3>Interpretasi DeepSeek</h3></div>
        </div>
        <span className="ai-status"><span /> Analisis selesai</span>
      </header>
      <div className="explanation-sections">
        {sections.map((section, index) => (
          <motion.section
            className="explanation-section"
            key={`${section.label}-${index}`}
            initial={reduceMotion ? false : { opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.28 + index * 0.09 }}
          >
            <span className="explanation-index">0{index + 1}</span>
            <div><h4>{section.label}</h4><p>{section.content}</p></div>
          </motion.section>
        ))}
      </div>
      <footer className="explanation-note">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>
        Hasil citra adalah informasi pendukung. Tetap lakukan pemeriksaan aroma, tekstur, dan kondisi fisik ikan.
      </footer>
    </motion.article>
  )
}

export function ResultSummary({ prediction, onReset }) {
  const tone = statusClass(prediction.final.label)
  return (
    <section className="result-section" aria-live="polite">
      <div className={`result-summary ${tone}`}>
        <div><span className="eyebrow">Hasil akhir ensemble</span><h2>{prediction.final.label}</h2><p>Gabungan analisis citra mata dan insang.</p></div>
        <div className="final-confidence"><span>Confidence</span><strong>{formatConfidence(prediction.final.confidence)}</strong></div>
      </div>
      <div className="prediction-grid">
        <PredictionCard title="Prediksi mata" prediction={prediction.eye} />
        <PredictionCard title="Prediksi insang" prediction={prediction.gill} />
      </div>
      <AIExplanationCard explanation={prediction.explanation} />
      <button type="button" className="button button-secondary reset-button" onClick={onReset}>Mulai analisis baru</button>
    </section>
  )
}
