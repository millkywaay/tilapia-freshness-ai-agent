export const LABELS = {
  FRESH: 'SEGAR',
  STALE: 'TIDAK SEGAR',
  REVIEW: 'PERLU PEMERIKSAAN LANJUTAN',
}

export function safeProbability(value, fallback = null) {
  if (value === null || value === undefined || value === '') return fallback
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return fallback
  return Math.min(Math.max(parsed, 0), 1)
}

export function normalizeLabel(value) {
  const label = String(value ?? '').trim().toUpperCase().replaceAll('_', ' ')
  if (['FRESH', 'SEGAR'].includes(label)) return LABELS.FRESH
  if (['NONFRESH', 'NON FRESH', 'TIDAK SEGAR', 'TDK SEGAR'].includes(label)) return LABELS.STALE
  if (label.includes('PEMERIKSAAN') || label === 'REVIEW') return LABELS.REVIEW
  return null
}

export function formatConfidence(value, fallback = '—') {
  const probability = safeProbability(value)
  return probability === null ? fallback : `${(probability * 100).toFixed(1)}%`
}

function organFromResponse(result, key, legacyProbability) {
  const structured = result?.[key]
  const probability = safeProbability(legacyProbability)
  const inferredLabel = probability === null
    ? null
    : probability >= 0.5 ? LABELS.STALE : LABELS.FRESH
  const label = normalizeLabel(structured?.label) || inferredLabel || LABELS.REVIEW
  const inferredConfidence = probability === null
    ? null
    : label === LABELS.STALE ? probability : 1 - probability

  return {
    label,
    confidence: safeProbability(structured?.confidence, inferredConfidence),
  }
}

export function normalizePrediction(result) {
  const rawEyeProbability = safeProbability(result?.prob_nonfresh_eyes ?? result?.prob_eyes)
  const rawGillProbability = safeProbability(result?.prob_nonfresh_gills ?? result?.prob_gills)
  const eye = organFromResponse(
    result,
    'eye',
    rawEyeProbability,
  )
  const gill = organFromResponse(
    result,
    'gill',
    rawGillProbability,
  )
  const disagree = eye.label !== gill.label
  const averageNonfresh = rawEyeProbability !== null && rawGillProbability !== null
    ? (rawEyeProbability + rawGillProbability) / 2
    : null
  const inferredFinalConfidence = averageNonfresh === null
    ? null
    : Math.max(averageNonfresh, 1 - averageNonfresh)
  const legacyFinalConfidence = safeProbability(result?.confidence, inferredFinalConfidence)
  const lowConfidenceConflict = eye.confidence === null || gill.confidence === null
    ? (legacyFinalConfidence ?? 0) < 0.7
    : Math.min(eye.confidence, gill.confidence) < 0.7
  let finalLabel = normalizeLabel(result?.final?.label ?? result?.label)

  if (!finalLabel) {
    if (eye.label === LABELS.REVIEW || gill.label === LABELS.REVIEW) finalLabel = LABELS.REVIEW
    else if (disagree && lowConfidenceConflict) finalLabel = LABELS.REVIEW
    else if (eye.label === LABELS.STALE || gill.label === LABELS.STALE) finalLabel = LABELS.STALE
    else finalLabel = LABELS.FRESH
  }

  return {
    eye,
    gill,
    final: {
      label: finalLabel,
      confidence: safeProbability(result?.final?.confidence, legacyFinalConfidence),
    },
    explanation: result?.explanation || 'Penjelasan belum tersedia. Periksa kondisi fisik dan aroma ikan sebelum dikonsumsi.',
  }
}
