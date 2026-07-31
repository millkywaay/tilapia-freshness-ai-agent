import { Link, useLocation } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

function LogoMark() {
  return (
    <span className="logo-mark" aria-hidden="true">
      <img src="./icon.svg" alt="Logo NilaFresh" />
      {/* <svg viewBox="0 0 32 32"><path d="M5 16c4.8-7 12.3-8.3 19-3.7l3-2v11.4l-3-2C17.3 24.3 9.8 23 5 16Z"/><circle cx="19.5" cy="14" r="1.2"/></svg> */}
    </span>
  )
}

function Navbar() {
  const { pathname } = useLocation()

  return (
    <header className="site-header">
      <nav className="nav-inner" aria-label="Navigasi utama">
        <Link to="/" className="brand" aria-label="NilaFresh beranda">
          <LogoMark />
          <span>NilaFresh</span>
        </Link>
        <div className="nav-actions">
          {pathname === '/' && (
            <div className="nav-links">
              <a href="#cara-kerja">Cara kerja</a>
              <a href="#tentang">Tentang</a>
            </div>
          )}
          <ThemeToggle />
          <Link to="/detect" className="button button-small">Mulai deteksi</Link>
        </div>
      </nav>
    </header>
  )
}

export default Navbar
