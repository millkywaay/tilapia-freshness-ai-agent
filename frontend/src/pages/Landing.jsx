import { motion, useReducedMotion } from 'framer-motion'
import { Link } from 'react-router-dom'

const steps = [
  {
    number: '01',
    icon: 'camera',
    title: 'Ambil dua citra',
    description: 'Foto mata dan insang secara dekat, terang, dan fokus agar karakter visual keduanya terbaca jelas.',
    detail: 'Dua organ · dua input',
  },
  {
    number: '02',
    icon: 'scan',
    title: 'Analisis per organ',
    description: 'Model khusus memeriksa mata dan insang secara terpisah, lengkap dengan label serta confidence masing-masing.',
    detail: 'Model mata + model insang',
  },
  {
    number: '03',
    icon: 'merge',
    title: 'Gabungkan hasil',
    description: 'Kedua prediksi disatukan dengan aturan keputusan yang konsisten untuk menghasilkan kesimpulan akhir.',
    detail: 'Ensemble · hasil akhir',
  },
]

function StepIcon({ name }) {
  if (name === 'camera') {
    return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7.5A2.5 2.5 0 0 1 6.5 5h2l1.2-1.5h4.6L15.5 5h2A2.5 2.5 0 0 1 20 7.5v9a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5v-9Z"/><circle cx="12" cy="12" r="3.5"/></svg>
  }
  if (name === 'scan') {
    return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M7 12h10M9 9.5h6M9 14.5h6"/></svg>
  }
  return <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="12" r="2.5"/><path d="M8.5 6c5 0 4 6 7 6M8.5 18c5 0 4-6 7-6"/></svg>
}

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.14, delayChildren: 0.08 } },
}

const cardVariants = {
  hidden: { opacity: 0, y: 28, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', stiffness: 120, damping: 18 } },
}

function Landing() {
  const reduceMotion = useReducedMotion()

  return (
    <main>
      <section className="hero page-container">
        <motion.div className="hero-copy" initial={reduceMotion ? false : { opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}>
          <span className="eyebrow">Klasifikasi visual ikan nila</span>
          <h1>Nilai kesegaran ikan dengan bukti dari dua organ.</h1>
          <p>NilaFresh menganalisis citra mata dan insang secara terpisah, lalu merangkum keduanya menjadi hasil yang mudah dipahami.</p>
          <div className="hero-actions">
            <Link to="/detect" className="button">Mulai deteksi</Link>
            <a href="#cara-kerja" className="text-link">Pelajari cara kerja <span aria-hidden="true">→</span></a>
          </div>
        </motion.div>
        <motion.aside className="hero-panel" aria-label="Ringkasan proses NilaFresh" initial={reduceMotion ? false : { opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}>
          <div className="panel-top"><span>Alur pemeriksaan</span><span className="live-dot">Siap digunakan</span></div>
          <div className="organ-row"><span className="organ-index">A</span><div><strong>Citra mata</strong><span>Kejernihan dan karakter visual</span></div><span className="organ-status">Model 01</span></div>
          <div className="organ-row"><span className="organ-index">B</span><div><strong>Citra insang</strong><span>Warna dan karakter visual</span></div><span className="organ-status">Model 02</span></div>
          <div className="ensemble-row"><span>Hasil akhir</span><strong>Ensemble dua prediksi</strong></div>
        </motion.aside>
      </section>

      <section id="cara-kerja" className="process-section">
        <div className="page-container">
          <motion.div className="section-heading" initial={reduceMotion ? false : { opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.55 }}>
            <span className="eyebrow">Cara kerja</span><h2>Proses singkat, hasil transparan.</h2><p>Setiap tahap dirancang agar hasil tiap organ tetap dapat dibaca, bukan hanya keputusan akhirnya.</p>
          </motion.div>
          <motion.div className="steps-grid" variants={reduceMotion ? undefined : containerVariants} initial={reduceMotion ? false : 'hidden'} whileInView={reduceMotion ? undefined : 'visible'} viewport={{ once: true, amount: 0.2 }}>
            {steps.map((step) => (
              <motion.article className="step-card" key={step.number} variants={reduceMotion ? undefined : cardVariants} whileHover={reduceMotion ? undefined : { y: -8 }} transition={{ type: 'spring', stiffness: 300, damping: 22 }}>
                <div className="step-card-top"><span className="step-icon"><StepIcon name={step.icon} /></span><span className="step-number">{step.number}</span></div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
                <div className="step-detail"><span>{step.detail}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg></div>
              </motion.article>
            ))}
          </motion.div>
        </div>
      </section>

      <section id="tentang" className="about-section page-container">
        <div><span className="eyebrow">Tentang penelitian</span><h2>Dibangun untuk pemeriksaan yang lebih terukur.</h2></div>
        <div><p>NilaFresh dikembangkan sebagai bagian dari penelitian klasifikasi kesegaran ikan nila. Dua model citra khusus digunakan agar kondisi mata dan insang tidak tercampur dalam satu asumsi visual.</p><p className="tech-line">FastAPI · React · TensorFlow · ResNet50</p></div>
      </section>

      <footer className="site-footer"><div className="page-container"><span>NilaFresh</span><span>Sistem pendukung pemeriksaan kesegaran ikan nila.</span></div></footer>
    </main>
  )
}

export default Landing
