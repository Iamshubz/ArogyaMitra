import { FormEvent, useEffect, useState } from 'react'
import {
  AuthUser,
  getHealthStatus,
  getProfile,
  loginAccount,
  registerAccount,
  updateProfile,
} from './services/api'

type Connection = 'checking' | 'connected' | 'offline'

type View = 'dashboard' | 'login' | 'register' | 'profile'

export default function App() {
  const [connection, setConnection] = useState<Connection>('checking')
  const [user, setUser] = useState<AuthUser | null>(null)
  const [view, setView] = useState<View>(localStorage.getItem('arogyamitra_token') ? 'dashboard' : 'login')

  useEffect(() => {
    getHealthStatus()
      .then(() => setConnection('connected'))
      .catch(() => setConnection('offline'))
    if (localStorage.getItem('arogyamitra_token')) {
      getProfile().then(setUser).catch(() => {
        localStorage.removeItem('arogyamitra_token')
        setView('login')
      })
    }
  }, [])

  const signOut = () => {
    localStorage.removeItem('arogyamitra_token')
    setUser(null)
    setView('login')
  }

  if (view === 'login') {
    return <AuthPage mode="login" onSwitch={() => setView('register')} onSuccess={(nextUser, token) => {
      localStorage.setItem('arogyamitra_token', token)
      setUser(nextUser)
      setView('dashboard')
    }} />
  }
  if (view === 'register') {
    return <AuthPage mode="register" onSwitch={() => setView('login')} onSuccess={(nextUser, token) => {
      localStorage.setItem('arogyamitra_token', token)
      setUser(nextUser)
      setView('dashboard')
    }} />
  }
  if (!user) {
    return <div className="loading-page">Loading your secure workspace...</div>
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#dashboard" aria-label="ArogyaMitra dashboard" onClick={() => setView('dashboard')}>
          <span className="brand-mark">+</span><span>Arogya<span className="brand-light">Mitra</span></span>
        </a>
        <nav className="top-actions" aria-label="Account navigation">
          <span className={`connection connection-${connection}`}><span className="dot" />{connection === 'connected' ? 'System online' : connection === 'checking' ? 'Checking system' : 'Offline mode'}</span>
          <button className="link-button" onClick={() => setView('profile')}>My profile</button>
          <button className="outline-button small-button" onClick={signOut}>Log out</button>
        </nav>
      </header>

      {view === 'profile' ? <ProfilePage user={user} onUpdated={setUser} onBack={() => setView('dashboard')} /> : <Dashboard user={user} onProfile={() => setView('profile')} />}
      <footer><span>ArogyaMitra · Healthcare in Your Language, Care for Everyone.</span><span>Information support only. Healthcare professionals remain responsible for clinical decisions.</span></footer>
    </main>
  )
}

function AuthPage({ mode, onSwitch, onSuccess }: { mode: 'login' | 'register'; onSwitch: () => void; onSuccess: (user: AuthUser, token: string) => void }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', phone_number: '', age: '', date_of_birth: '', gender: '', address: '', designation: '', facility_name: '', preferred_language: 'en', role: 'patient' as 'patient' | 'healthcare_worker' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setSubmitting(true)
    try {
      const response = mode === 'login' ? await loginAccount(form.email, form.password) : await registerAccount({ ...form, age: form.age ? Number(form.age) : undefined, date_of_birth: form.date_of_birth || undefined })
      onSuccess(response.user, response.access_token)
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'We could not complete that request. Please try again.')
    } finally { setSubmitting(false) }
  }
  return <main className="auth-layout"><section className="auth-intro"><div className="brand"><span className="brand-mark">+</span><span>Arogya<span className="brand-light">Mitra</span></span></div><p className="eyebrow">HEALTHCARE FOR EVERYONE</p><h1>Healthcare in Your Language, <span>Care for Everyone.</span></h1><p>Understand health information clearly, keep your profile up to date, and stay connected with your care team.</p></section><section className="auth-card"><p className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'GET STARTED'}</p><h2>{mode === 'login' ? 'Sign in to ArogyaMitra' : 'Create your account'}</h2><form onSubmit={submit}>{mode === 'register' && <label>Full name<input required minLength={2} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>}<label>Email address<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label><label>Password<input required minLength={8} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>{mode === 'register' && <><div className="form-grid"><label>Phone number<input type="tel" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} /></label><label>Age<input type="number" min="0" max="130" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} /></label></div><div className="form-grid"><label>Date of birth<input type="date" value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} /></label><label>Gender<input value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} /></label></div><label>Address<input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label><div className="form-grid"><label>Preferred language<select value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}><option value="en">English</option><option value="hi">Hindi</option><option value="mr">Marathi</option><option value="bn">Bengali</option><option value="ta">Tamil</option><option value="te">Telugu</option></select></label><label>Account type<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as 'patient' | 'healthcare_worker' })}><option value="patient">Patient</option><option value="healthcare_worker">Healthcare worker</option></select></label></div>{form.role === 'healthcare_worker' && <div className="form-grid"><label>Designation<input value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} /></label><label>Facility name<input value={form.facility_name} onChange={(e) => setForm({ ...form, facility_name: e.target.value })} /></label></div>}</>}{error && <p className="form-error" role="alert">{error}</p>}<button className="primary-button full-width" disabled={submitting}>{submitting ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}</button></form><p className="switch-text">{mode === 'login' ? 'New to ArogyaMitra?' : 'Already have an account?'} <button className="link-button" onClick={onSwitch}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p></section></main>
}

function Dashboard({ user, onProfile }: { user: AuthUser; onProfile: () => void }) {
  const roleTitle = user.role === 'patient' ? 'Patient dashboard' : user.role === 'healthcare_worker' ? 'Healthcare worker dashboard' : 'Administrator dashboard'
  return <section className="dashboard"><div className="welcome-panel"><div><p className="eyebrow">YOUR AROGYAMITRA WORKSPACE</p><h1>Welcome, {user.full_name.split(' ')[0]}.</h1><p>Healthcare in Your Language, Care for Everyone.</p></div><button className="primary-button" onClick={onProfile}>Manage profile <span>→</span></button></div><div className="dashboard-grid"><article className="info-card"><span className="card-icon">◉</span><h3>{roleTitle}</h3><p>Your secure workspace is ready. More care tools will be added in upcoming milestones.</p><span className="status-label">Foundation complete</span></article><article className="info-card"><span className="card-icon blue">文</span><h3>Language preference</h3><p>You are viewing ArogyaMitra in <strong>{user.preferred_language.name}</strong>.</p><span className="status-label blue-label">Personalized access</span></article><article className="info-card"><span className="card-icon orange">✓</span><h3>Care and privacy</h3><p>Your account data is protected. Do not upload or share information that is not yours.</p><span className="status-label orange-label">Safety first</span></article></div><div className="coming-section"><p className="eyebrow">NEXT MILESTONES</p><h2>More support, step by step</h2><div className="coming-grid"><span>Medical document understanding</span><span>Simple explanations and translation</span><span>Voice-enabled assistance</span></div></div></section>
}

function ProfilePage({ user, onUpdated, onBack }: { user: AuthUser; onUpdated: (user: AuthUser) => void; onBack: () => void }) {
  const [form, setForm] = useState({ full_name: user.full_name, phone_number: user.phone_number || '', preferred_language: user.preferred_language.code, age: user.age?.toString() || '', date_of_birth: user.date_of_birth || '', gender: user.gender || '', address: user.address || '', facility_name: user.facility_name || '', specialization: user.specialization || '', designation: user.designation || '' })
  const [message, setMessage] = useState(''); const [error, setError] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); setMessage(''); setError(''); try { const updated = await updateProfile({ ...form, age: form.age ? Number(form.age) : undefined, date_of_birth: form.date_of_birth || undefined }); onUpdated(updated); setMessage('Profile updated successfully.') } catch (requestError: any) { setError(requestError.response?.data?.detail || 'Unable to update your profile.') } }
  return <section className="profile-page"><button className="link-button back-link" onClick={onBack}>← Back to dashboard</button><div className="page-heading"><p className="eyebrow">ACCOUNT SETTINGS</p><h1>Manage your profile</h1><p>Keep your contact details and language preference current.</p></div><form className="profile-card" onSubmit={submit}><div className="form-grid"><label>Full name<input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label><label>Email address<input disabled value={user.email} /></label></div><div className="form-grid"><label>Phone number<input type="tel" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} /></label><label>Preferred language<select value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}><option value="en">English</option><option value="hi">Hindi</option><option value="mr">Marathi</option><option value="bn">Bengali</option><option value="ta">Tamil</option><option value="te">Telugu</option></select></label></div><label>Address<input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label>{user.role === 'patient' && <div className="form-grid"><label>Age<input type="number" min="0" max="130" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} /></label><label>Date of birth<input type="date" value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} /></label></div>}{user.role === 'healthcare_worker' && <><div className="form-grid"><label>Designation<input value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} /></label><label>Facility name<input value={form.facility_name} onChange={(e) => setForm({ ...form, facility_name: e.target.value })} /></label></div><label>Specialization<input value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} /></label></>}{message && <p className="success-message">{message}</p>}{error && <p className="form-error">{error}</p>}<button className="primary-button">Save changes</button></form></section>
}
