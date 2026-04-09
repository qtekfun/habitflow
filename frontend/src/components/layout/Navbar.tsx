import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'

export function Navbar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  async function handleLogout() {
    try {
      await api.post('/api/v1/auth/logout')
    } finally {
      logout()
      navigate('/login')
    }
  }

  return (
    <nav className="border-b border-gray-200 bg-white px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link to="/" className="text-lg font-bold text-indigo-600">
          HabitFlow
        </Link>

        {user && (
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
              Dashboard
            </Link>
            <Link to="/habits" className="text-sm text-gray-600 hover:text-gray-900">
              Habits
            </Link>
            <Link to="/stats" className="text-sm text-gray-600 hover:text-gray-900">
              Stats
            </Link>
            <Link to="/settings" className="text-sm text-gray-600 hover:text-gray-900">
              Settings
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
