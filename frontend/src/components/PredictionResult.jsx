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

/* ── Section config ──────────────────────────────────────────────── */
const SECTION_CONFIG = {
  'kondisi organ': {
    label: 'Kondisi Organ',
    color: 'interp-blue',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    ),
  },
  'kesimpulan': {
    label: 'Kesimpulan',
    color: 'interp-green',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    ),
  },
  'rekomendasi': {
    label: 'Rekomendasi',
    color: 'interp-amber',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
  },
}

/* Parse bullet points from a section's text content */
function parseBullets(text) {
  return text
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.startsWith('•') || l.startsWith('-') || l.startsWith('*'))
    .map(l => l.replace(/^[•\-*]\s*/, '').trim())
    .filter(Boolean)
}

/* ── Interpretation Section Card ─────────────────────────────────── */
function InterpCard({ config, bullets, index, reduceMotion }) {
  const hasBullets = bullets.length > 0

  return (
    <motion.div
      className={`interp-card interp-card--${config.color}`}
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42, delay: 0.22 + index * 0.1 }}
    >
      <div className="interp-card-header">
        <span className="interp-card-icon">{config.icon}</span>
        <h4 className="interp-card-title">{config.label}</h4>
      </div>

      {hasBullets ? (
        <ul className="interp-bullets">
          {bullets.map((point, i) => (
            <li key={i} className="interp-bullet-item">
              <span className="interp-bullet-dot" aria-hidden="true" />
              <span>{point}</span>
            </li>
          ))}
        </ul>
      ) : (
        /* Fallback: render raw text if no bullet markers found */
        <p className="interp-fallback-text">{bullets[0] || '—'}</p>
      )}
    </motion.div>
  )
}

/* ── AI Explanation Card ─────────────────────────────────────────── */
export function AIExplanationCard({ explanation }) {
  const reduceMotion = useReducedMotion()

  // Multi-line parser: splits into named sections, collects bullet lines
  const rawText = String(explanation || '')
  const lines = rawText.split('\n').map(l => l.trim())

  const sectionMap = {}
  let currentKey = null

  for (const line of lines) {
    if (!line) continue
    // Detect section headers (supports both old and new formats from prompt)
    const headerMatch = line.match(/^\*{0,2}(Kondisi organ|Analisis Organ|Kesimpulan Akhir|Kesimpulan|Rekomendasi Penanganan|Rekomendasi)\s*:?\*{0,2}\s*(.*)$/i)
    if (headerMatch) {
      let rawKey = headerMatch[1].toLowerCase()
      if (rawKey === 'analisis organ') currentKey = 'kondisi organ'
      else if (rawKey === 'kesimpulan akhir') currentKey = 'kesimpulan'
      else if (rawKey === 'rekomendasi penanganan') currentKey = 'rekomendasi'
      else currentKey = rawKey

      if (!sectionMap[currentKey]) sectionMap[currentKey] = []
      if (headerMatch[2].trim()) sectionMap[currentKey].push(headerMatch[2].trim())
    } else if (currentKey) {
      sectionMap[currentKey].push(line)
    }
  }

  // Build ordered sections
  const orderedKeys = ['kondisi organ', 'kesimpulan', 'rekomendasi']
  const sections = orderedKeys
    .filter(k => sectionMap[k] && sectionMap[k].length > 0)
    .map(k => ({
      key: k,
      config: SECTION_CONFIG[k],
      bullets: parseBullets(sectionMap[k].join('\n')),
      rawLines: sectionMap[k],
    }))

  // Fallback if parsing completely fails
  if (sections.length === 0) {
    sections.push({
      key: 'analisis',
      config: { label: 'Analisis', color: 'interp-blue', icon: null },
      bullets: [rawText],
      rawLines: [rawText],
    })
  }

  return (
    <motion.article
      className="explanation-card"
      initial={reduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Card header */}
      <header className="explanation-header">
        <div className="explanation-title">
          <div className="explanation-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3a7 7 0 0 0-4.5 12.36V19h9v-3.64A7 7 0 0 0 12 3Z"/>
              <path d="M9 22h6"/>
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

      {/* 3-section cards */}
      <div className="interp-grid">
        {sections.map((sec, idx) => (
          <InterpCard
            key={sec.key}
            config={sec.config}
            bullets={sec.bullets.length > 0 ? sec.bullets : sec.rawLines}
            index={idx}
            reduceMotion={reduceMotion}
          />
        ))}
      </div>

      {/* Disclaimer footer */}
      <footer className="explanation-note">
        <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"
          strokeWidth="1.7" strokeLinecap="round">
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
  const hasConflict = prediction.eye.label !== prediction.gill.label

  return (
    <section className="result-section" aria-live="polite">

      {/* Final Result Card */}
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

      {/* Conflict Warning */}
      {hasConflict && (
        <motion.div
          className="conflict-warning"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true" fill="none"
            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
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

      {/* Organ Detail Cards */}
      <div className="prediction-grid">
        <PredictionCard title="Analisis mata" prediction={prediction.eye} />
        <PredictionCard title="Analisis insang" prediction={prediction.gill} />
      </div>

      {/* AI Interpretation */}
      <AIExplanationCard explanation={prediction.explanation} />

      {/* Reset */}
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
