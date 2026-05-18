import { useState, useRef, useCallback } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

function UploadBox({ label, icon, spec, file, onChange, onRemove }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef()

  const handleDrop = useCallback(e => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) onChange(f)
  }, [onChange])

  const fileSize = file
    ? file.size > 1024 * 1024
      ? (file.size / 1024 / 1024).toFixed(1) + ' MB'
      : (file.size / 1024).toFixed(0) + ' KB'
    : ''
  const shortName = file
    ? file.name.length > 22 ? file.name.slice(0, 19) + '…' : file.name
    : ''

  return (
    <div
      className={`upload-box rounded-[18px] min-h-[240px] flex flex-col items-center justify-center gap-3.5 overflow-hidden ${file ? 'has-image p-0 cursor-default' : 'p-9 cursor-pointer'} ${dragOver ? 'dragover' : ''}`}
      onDragOver={e => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !file && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={e => e.target.files[0] && onChange(e.target.files[0])}
      />

      {file ? (
        <div className="relative w-full h-full min-h-[240px]">
          <img src={URL.createObjectURL(file)} alt="preview"
               className="w-full h-full object-cover min-h-[240px] block" />

          {/* Overlay with gradient via inline style since it's a complex multi-stop gradient */}
          <div
            className="absolute inset-0 flex flex-col justify-between p-3.5"
            style={{ background: 'linear-gradient(180deg, rgba(5,9,18,0.1) 0%, transparent 30%, rgba(5,9,18,0.9) 100%)' }}
          >
            <span
              className="self-start inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-[0.04em] text-teal-300"
              style={{ background: 'rgba(10,15,30,0.7)', backdropFilter: 'blur(8px)', border: '1px solid rgba(20,184,166,0.4)' }}
            >
              ✓ {label}
            </span>
            <div className="flex justify-between items-end">
              <span className="font-mono text-[11.5px] text-slate-400">{shortName}</span>
              <span className="text-[11px] text-slate-500">{fileSize}</span>
            </div>
          </div>

          <button
            className="absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center text-white border border-slate-400/[0.18] cursor-pointer hover:bg-red-500 hover:border-red-500 hover:scale-[1.08] transition-all"
            style={{ background: 'rgba(10,15,30,0.7)', backdropFilter: 'blur(8px)' }}
            onClick={e => { e.stopPropagation(); onRemove() }}
            aria-label="Hapus gambar"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      ) : (
        <>
          <div className="upload-icon w-[78px] h-[78px] rounded-full border border-teal-500/30 flex items-center justify-center text-[38px]">
            {icon}
          </div>
          <div className="text-base font-semibold text-slate-100">{label}</div>
          <div className="text-[12.5px] text-slate-500 text-center">
            Letakkan gambar di sini atau{' '}
            <span className="text-teal-300 underline underline-offset-2">klik untuk pilih</span>
          </div>
          <div className="font-mono text-[10.5px] text-slate-600 px-[9px] py-1 rounded bg-slate-400/[0.08] border border-slate-400/10">
            {spec}
          </div>
        </>
      )}
    </div>
  )
}

function ResultCard({ result, onReset }) {
  const isFresh = result.label === 'Fresh'
  const cls     = isFresh ? 'fresh' : 'stale'
  const confidence = (result.confidence * 100).toFixed(1)

  const eyeIsFresh = result.prob_eyes < 0.5
  const eyeConf    = (eyeIsFresh ? 1 - result.prob_eyes : result.prob_eyes) * 100
  const gillIsFresh = result.prob_gills < 0.5
  const gillConf    = (gillIsFresh ? 1 - result.prob_gills : result.prob_gills) * 100

  const organs = [
    { label: 'Prediksi Mata',   icon: '📷', isFresh: eyeIsFresh,  conf: eyeConf  },
    { label: 'Prediksi Insang', icon: '🫁', isFresh: gillIsFresh, conf: gillConf },
  ]

  return (
    <div
      className={`result-card relative overflow-hidden rounded-[20px] p-8 ${cls}`}
      style={{
        background: isFresh
          ? 'linear-gradient(180deg, rgba(20,184,166,0.08), rgba(20,184,166,0.015))'
          : 'linear-gradient(180deg, rgba(239,68,68,0.08), rgba(239,68,68,0.015))',
        boxShadow: isFresh
          ? '0 0 0 1px rgba(20,184,166,0.45), 0 0 60px rgba(20,184,166,0.18), 0 20px 60px rgba(0,0,0,0.4)'
          : '0 0 0 1px rgba(239,68,68,0.45), 0 0 60px rgba(239,68,68,0.18), 0 20px 60px rgba(0,0,0,0.4)',
      }}
    >
      {/* Verdict */}
      <div className="text-center mb-7 relative z-10">
        <div className="verdict-emoji text-[64px] leading-none inline-block">
          {isFresh ? '✅' : '❌'}
        </div>
        <div className={`text-[42px] font-extrabold tracking-tight mt-3.5 mb-3 leading-none ${isFresh ? 'text-teal-300' : 'text-red-300'}`}>
          {isFresh ? 'SEGAR' : 'TIDAK SEGAR'}
        </div>
        <span
          className={`inline-flex items-center gap-2.5 px-4 py-2 rounded-full text-[13.5px] font-semibold ${isFresh ? 'text-teal-300' : 'text-red-300'}`}
          style={{
            background: isFresh ? 'rgba(20,184,166,0.15)' : 'rgba(239,68,68,0.15)',
            border: `1px solid ${isFresh ? 'rgba(20,184,166,0.4)' : 'rgba(239,68,68,0.4)'}`,
          }}
        >
          <span>Confidence</span>
          <span className="w-px h-3 opacity-40" style={{ background: 'currentColor' }} />
          <span className="tabular-nums text-base font-bold">{confidence}%</span>
        </span>
      </div>

      {/* Mini prediction cards */}
      <div className="grid grid-cols-2 gap-3.5 mb-7 relative z-10 max-sm:grid-cols-1">
        {organs.map((organ, i) => (
          <div key={i}
               className="p-[18px_20px] rounded-[14px] border border-slate-400/[0.18]"
               style={{ background: 'rgba(10,15,30,0.5)' }}>
            <div className="flex items-center justify-between mb-3.5">
              <div className="flex items-center gap-2 text-slate-400 text-[13px] font-semibold">
                <span className="w-[26px] h-[26px] rounded-[7px] bg-slate-400/[0.08] border border-slate-400/10 flex items-center justify-center text-sm">
                  {organ.icon}
                </span>
                {organ.label}
              </div>
              <span
                className={`text-[11px] font-bold tracking-[0.06em] px-[9px] py-[3px] rounded ${organ.isFresh ? 'text-teal-300' : 'text-red-300'}`}
                style={{ background: organ.isFresh ? 'rgba(20,184,166,0.15)' : 'rgba(239,68,68,0.15)' }}
              >
                {organ.isFresh ? 'SEGAR' : 'TDK SEGAR'}
              </span>
            </div>
            <div className="h-2 rounded bg-slate-400/10 overflow-hidden mb-2">
              <div
                className={`bar-fill h-full rounded ${organ.isFresh ? 'shadow-[0_0_12px_rgba(20,184,166,0.5)]' : 'shadow-[0_0_12px_rgba(239,68,68,0.5)]'}`}
                style={{
                  width: `${organ.conf.toFixed(1)}%`,
                  background: organ.isFresh
                    ? 'linear-gradient(90deg, #14b8a6, #5eead4)'
                    : 'linear-gradient(90deg, #ef4444, #fca5a5)',
                }}
              />
            </div>
            <div className="flex justify-between text-[12px] font-mono text-slate-500">
              <span>MobileNetV2</span>
              <span className="text-slate-100 font-semibold tabular-nums">{organ.conf.toFixed(1)}%</span>
            </div>
          </div>
        ))}
      </div>

      {/* Divider */}
      <div className="divider flex items-center gap-3 my-7 text-slate-600 text-[11px] tracking-[0.14em] uppercase relative z-10">
        Penjelasan AI
      </div>

      {/* AI explanation */}
      <div
        className="flex gap-4 p-[22px] rounded-[14px] border border-slate-400/[0.18] relative z-10"
        style={{ background: 'rgba(10,15,30,0.5)' }}
      >
        <div
          className="ai-avatar relative flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center text-[22px]"
          style={{ background: 'linear-gradient(135deg, #9333ea, #6366f1)', boxShadow: '0 4px 16px rgba(147,51,234,0.4)' }}
        >
          🤖
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-[13px] font-semibold text-slate-100 mb-1">
            Agent
            <span className="text-[10.5px] font-semibold text-slate-600 bg-slate-400/10 px-[7px] py-[2px] rounded tracking-[0.06em] uppercase">
              AI Explainer
            </span>
          </div>
          <div
            className="p-[14px_16px] text-[14px] leading-[1.7] text-slate-400 rounded-[14px] rounded-tl-[4px] border border-slate-400/10"
            style={{ background: 'rgba(255,255,255,0.04)' }}
          >
            {result.explanation}
          </div>
        </div>
      </div>

      {/* Meta strip */}
      <div className="flex justify-between items-center mt-[22px] pt-[18px] border-t border-slate-400/10 font-mono text-[11.5px] text-slate-600 relative z-10 flex-wrap gap-3">
        <div className="flex gap-4 flex-wrap">
          <span className="flex gap-1.5">
            <span>verdict:</span>
            <span className="text-slate-400">{isFresh ? 'SEGAR' : 'TIDAK SEGAR'}</span>
          </span>
          <span className="flex gap-1.5">
            <span>ensemble:</span>
            <span className="text-slate-400">weighted_avg</span>
          </span>
          <span className="flex gap-1.5">
            <span>model:</span>
            <span className="text-slate-400">MobileNetV2</span>
          </span>
        </div>
        <button
          onClick={onReset}
          className="px-3 py-1.5 rounded-md bg-white/[0.04] border border-slate-400/[0.18] text-slate-400 font-mono text-[11.5px] font-medium cursor-pointer inline-flex items-center gap-1.5 hover:bg-white/[0.08] hover:text-slate-100 hover:border-teal-500/40 transition-all"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
          </svg>
          Reset
        </button>
      </div>
    </div>
  )
}

function Detect() {
  const [eyeFile,  setEyeFile]  = useState(null)
  const [gillFile, setGillFile] = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)

  const bothReady = eyeFile && gillFile

  const handleSubmit = async () => {
    if (!eyeFile || !gillFile) {
      setError('Upload foto mata dan insang terlebih dahulu.')
      return
    }
    setError(null)
    setLoading(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('eye_image',  eyeFile)
      formData.append('gill_image', gillFile)
      const res = await axios.post('http://127.0.0.1:8000/predict', formData)
      setResult(res.data)
    } catch {
      setError('Gagal menghubungi server. Pastikan backend sudah berjalan.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setEyeFile(null)
    setGillFile(null)
    setResult(null)
    setError(null)
  }

  return (
    <main className="page-in pt-[100px] pb-20 px-5 max-w-[1080px] mx-auto">

      {/* Page header */}
      <div className="text-center relative mb-11">
        <Link
          to="/"
          className="absolute left-0 top-1.5 inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-white/[0.04] border border-slate-400/[0.18] text-slate-400 no-underline text-[13px] font-medium hover:bg-white/[0.08] hover:text-slate-100 hover:border-teal-500/40 transition-all"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Beranda
        </Link>
        <h1 className="text-[clamp(28px,4vw,40px)] font-bold text-slate-100 tracking-tight mb-2.5">
          Deteksi Kesegaran Ikan
        </h1>
        <p className="text-[15px] text-slate-500 max-w-[520px] mx-auto leading-relaxed">
          Unggah dua foto — mata dan insang — lalu jalankan analisis. Sistem akan
          memproses tiap organ dan menggabungkan hasilnya secara otomatis.
        </p>
      </div>

      {/* Sample row */}
      <div className="flex items-center gap-2.5 px-3.5 py-2.5 bg-white/[0.04] border border-slate-400/10 rounded-xl mb-4 text-[12.5px] text-slate-500">
        <span className="flex items-center gap-1.5 text-slate-400">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/>
          </svg>
          Coba contoh:
        </span>
        <button className="inline-flex items-center gap-1.5 py-1 pr-2.5 pl-1 rounded-full bg-white/[0.08] border border-slate-400/[0.18] text-[12px] text-slate-100 font-medium hover:border-teal-500/50 transition-all cursor-pointer">
          <span className="w-5 h-5 rounded-full border border-slate-400/[0.18]" style={{ background: 'rgba(20,184,166,0.35)' }} />
          Sampel Segar
        </button>
        <button className="inline-flex items-center gap-1.5 py-1 pr-2.5 pl-1 rounded-full bg-white/[0.08] border border-slate-400/[0.18] text-[12px] text-slate-100 font-medium hover:border-teal-500/50 transition-all cursor-pointer">
          <span className="w-5 h-5 rounded-full border border-slate-400/[0.18]" style={{ background: 'rgba(239,68,68,0.35)' }} />
          Sampel Tidak Segar
        </button>
        <span className="ml-auto font-mono text-[11px] text-slate-600">2 organ · ensemble</span>
      </div>

      {/* Upload grid */}
      <div className="grid grid-cols-2 gap-[18px] mb-[18px] max-sm:grid-cols-1">
        <UploadBox
          label="Foto Mata"   icon="📷" spec="organ_01 · eye"
          file={eyeFile}   onChange={setEyeFile}   onRemove={() => setEyeFile(null)}
        />
        <UploadBox
          label="Foto Insang" icon="🫁" spec="organ_02 · gill"
          file={gillFile}  onChange={setGillFile}  onRemove={() => setGillFile(null)}
        />
      </div>

      {error && (
        <p className="text-red-300 text-[13px] text-center mt-3">{error}</p>
      )}

      {/* Analyze button */}
      <div className="mt-1">
        <button
          onClick={handleSubmit}
          disabled={!bothReady || loading}
          className={`w-full py-[18px] rounded-2xl font-bold text-base flex items-center justify-center gap-3 border-none transition-all ${bothReady && !loading ? 'cursor-pointer hover:-translate-y-0.5' : 'cursor-not-allowed'}`}
          style={bothReady && !loading ? {
            background: 'linear-gradient(135deg, #14b8a6, #0d9488)',
            color: '#052e2b',
            boxShadow: '0 10px 30px rgba(20,184,166,0.35), inset 0 1px 0 rgba(255,255,255,0.25)',
          } : {
            background: 'rgba(148,163,184,0.1)',
            color: '#475569',
          }}
        >
          <span>{loading ? 'Menganalisis...' : 'Analisis Kesegaran'}</span>
          {!loading && (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
            </svg>
          )}
        </button>
        <div className="flex justify-between mt-3 font-mono text-[11px] text-slate-600">
          <span>{bothReady ? 'Siap untuk dianalisis' : 'Unggah kedua foto untuk mulai'}</span>
          <span>model · MobileNetV2 ensemble</span>
        </div>
      </div>

      {/* Result — fade + slide in when ready */}
      <section
        className={`mt-9 transition-all duration-[600ms] ease-out ${result ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-5 pointer-events-none'}`}
      >
        {result && <ResultCard result={result} onReset={handleReset} />}
      </section>
    </main>
  )
}

export default Detect
