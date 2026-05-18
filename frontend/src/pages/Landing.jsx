import { useEffect } from 'react'
import { Link } from 'react-router-dom'

const steps = [
  { icon: '📸', title: 'Upload Gambar',     desc: 'Upload foto mata dan insang ikan Nila yang ingin dianalisis.' },
  { icon: '🧠', title: 'Analisis AI',       desc: 'Model deep learning MobileNetV2 memproses gambar dari kedua organ secara terpisah.' },
  { icon: '🔬', title: 'Ensemble Prediksi', desc: 'Hasil prediksi mata dan insang digabungkan untuk menghasilkan keputusan akhir.' },
  { icon: '📋', title: 'Penjelasan',        desc: 'AI menjelaskan hasil analisis secara ilmiah dalam Bahasa Indonesia.' },
]

function useScrollReveal() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in')
          observer.unobserve(e.target)
        }
      }),
      { threshold: 0.12 }
    )
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])
}

function Landing() {
  useScrollReveal()

  return (
    <main>
      {/* Hero */}
      <section className="min-h-screen flex flex-col items-center justify-center text-center px-6 py-20">
        <span className="page-in inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-[12px] font-semibold tracking-[0.05em] mb-7"
              style={{ animationDelay: '0ms' }}>
          🐟 &nbsp;NilaFresh · Deep Learning Classifier
        </span>
        <h1 className="page-in text-[clamp(38px,7vw,72px)] font-extrabold tracking-tight leading-[1.1] text-slate-100 mb-5"
            style={{ animationDelay: '80ms' }}>
          Deteksi Kesegaran<br />
          <span className="text-teal-300">Ikan Nila</span> dengan AI
        </h1>
        <p className="page-in text-[17px] text-slate-500 max-w-[520px] leading-[1.7] mb-10"
           style={{ animationDelay: '160ms' }}>
          Sistem klasifikasi kesegaran ikan berbasis deep learning menggunakan
          citra mata dan insang ikan Nila secara otomatis dan akurat.
        </p>
        <Link
          to="/detect"
          className="page-in inline-flex items-center gap-2.5 px-8 py-4 rounded-[14px] font-bold text-base no-underline transition-all hover:-translate-y-0.5"
          style={{
            animationDelay: '240ms',
            background: 'linear-gradient(135deg, #14b8a6, #0d9488)',
            color: '#052e2b',
            boxShadow: '0 10px 30px rgba(20,184,166,0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          Mulai Deteksi Sekarang
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
          </svg>
        </Link>
      </section>

      {/* Cara Kerja */}
      <section id="cara-kerja" className="py-24 px-6 border-y border-slate-400/10"
               style={{ background: 'rgba(10,15,30,0.5)' }}>
        <div className="reveal text-center mb-14">
          <h2 className="text-[36px] font-bold text-slate-100 tracking-tight mb-3">Cara Kerja</h2>
          <p className="text-[15px] text-slate-500">Empat langkah sederhana untuk mendeteksi kesegaran ikan Nila kamu.</p>
        </div>
        <div className="max-w-[1100px] mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((step, i) => (
            <div key={i}
                 className={`reveal reveal-d${i + 1} p-7 bg-white/[0.03] border border-slate-400/[0.18] rounded-[18px] transition-all duration-200 hover:bg-teal-500/[0.05] hover:border-teal-500/30 hover:-translate-y-[3px]`}>
              <div className="w-[52px] h-[52px] rounded-[14px] bg-teal-500/[0.12] border border-teal-500/25 flex items-center justify-center text-[26px] mb-[18px]">
                {step.icon}
              </div>
              <h3 className="text-[15px] font-bold text-slate-100 mb-2">{step.title}</h3>
              <p className="text-[13px] text-slate-500 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* About */}
      <section id="about" className="py-24 px-6 text-center">
        <div className="reveal max-w-[680px] mx-auto">
          <h2 className="text-[36px] font-bold text-slate-100 tracking-tight mb-5">About</h2>
          <p className="text-[15px] text-slate-500 leading-[1.8] mb-3.5">
            NilaFresh adalah sistem klasifikasi kesegaran ikan Nila berbasis deep learning
            yang dikembangkan sebagai bagian dari penelitian skripsi. Sistem ini menggunakan
            dua model MobileNetV2 terpisah — satu untuk citra mata dan satu untuk citra insang —
            yang digabungkan melalui ensemble probabilitas untuk menghasilkan prediksi akhir.
          </p>
          <div className="font-mono text-[12px] text-slate-600 px-[18px] py-2.5 rounded-lg bg-white/[0.04] border border-slate-400/10 inline-block">
            TensorFlow · FastAPI · ReactJS · MobileNetV2
          </div>
        </div>
      </section>
    </main>
  )
}

export default Landing
