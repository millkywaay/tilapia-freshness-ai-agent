import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <nav
      className="fixed top-0 w-full z-50 border-b border-slate-400/[0.18] backdrop-blur-md"
      style={{ background: 'rgba(5,9,18,0.85)' }}
    >
      <div className="max-w-[1100px] mx-auto px-6 h-[60px] flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 no-underline">
          <span className="text-[22px]">🐟</span>
          <span className="font-bold text-[17px] text-slate-100">NilaFresh</span>
          <span className="text-[10px] font-bold tracking-widest uppercase px-[7px] py-[2px] rounded bg-teal-500/[0.15] border border-teal-500/40 text-teal-300">
            beta
          </span>
        </Link>

        <div className="flex items-center gap-7">
          <a href="/#cara-kerja"
             className="hidden sm:block text-slate-500 hover:text-slate-100 no-underline text-sm font-medium transition-colors">
            Cara Kerja
          </a>
          <a href="/#about"
             className="hidden sm:block text-slate-500 hover:text-slate-100 no-underline text-sm font-medium transition-colors">
            About
          </a>
          <Link
            to="/detect"
            className="px-[18px] py-2 rounded-lg font-semibold text-[13.5px] no-underline transition-all hover:-translate-y-px"
            style={{
              background: 'linear-gradient(135deg, #14b8a6, #0d9488)',
              color: '#052e2b',
              boxShadow: '0 4px 14px rgba(20,184,166,0.3)',
            }}
          >
            Mulai Deteksi
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
