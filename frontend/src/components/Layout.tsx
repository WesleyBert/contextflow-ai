import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navLinkClass = ({ isActive }: { isActive: boolean }): string =>
  `rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
  }`

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="text-lg font-semibold text-slate-900">ContextFlow AI</span>
            <nav className="flex gap-1">
              <NavLink to="/documents" className={navLinkClass}>
                Documentos
              </NavLink>
              <NavLink to="/conversations" className={navLinkClass}>
                Conversas
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span>{user?.email}</span>
            <button
              type="button"
              onClick={logout}
              className="rounded-md px-3 py-1.5 font-medium text-slate-600 hover:bg-slate-100"
            >
              Sair
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
