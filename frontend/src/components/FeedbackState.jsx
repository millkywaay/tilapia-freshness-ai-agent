export function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <div><strong>Menganalisis kedua citra</strong><span>Model mata dan insang sedang bekerja secara terpisah.</span></div>
    </div>
  )
}

export function ErrorState({ message }) {
  return (
    <div className="error-state" role="alert">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/></svg>
      <span>{message}</span>
    </div>
  )
}
