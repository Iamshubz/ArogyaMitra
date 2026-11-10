import { FormEvent, useEffect, useState } from 'react'
import {
  AuthUser,
  getHealthStatus,
  getProfile,
  loginAccount,
  registerAccount,
  updateProfile,
  createReminder,
  listEmergencyContacts,
  listHealthContent,
  listReminders,
  updateReminderStatus,
  getSystemMonitoring,
  listAdminContent,
  listAdminAnalytics,
  listAssignedPatients,
  listTranslationHistory,
  listWorkerFollowUps,
  simplifyMedicalText,
  translateMedicalText,
  type FollowUp,
  type PatientSummary,
  type HealthContent,
  type Reminder,
} from './services/api'

type Connection = 'checking' | 'connected' | 'offline'

type View = 'dashboard' | 'login' | 'register' | 'profile' | 'workspace'

const roleNavigation: Record<AuthUser['role'], string[]> = {
  patient: ['Dashboard', 'AI assistant', 'Medical records', 'Reminders', 'Health education'],
  healthcare_worker: ['Dashboard', 'Patients', 'Consultations', 'Health education', 'Notifications'],
  admin: ['Dashboard', 'Users', 'Content management', 'System monitoring', 'Analytics'],
}

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

      {view === 'profile'
        ? <ProfilePage user={user} onUpdated={setUser} onBack={() => setView('dashboard')} />
        : view === 'workspace'
          ? <WorkspaceNotice user={user} onBack={() => setView('dashboard')} />
          : <Dashboard user={user} onProfile={() => setView('profile')} onWorkspace={() => setView('workspace')} />}
      <footer><span>ArogyaMitra · Healthcare in Your Language, Care for Everyone.</span><span>Information support only. Healthcare professionals remain responsible for clinical decisions.</span></footer>
    </main>
  )
}

function AuthPage({ mode, onSwitch, onSuccess }: { mode: 'login' | 'register'; onSwitch: () => void; onSuccess: (user: AuthUser, token: string) => void }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', phone_number: '', age: '', date_of_birth: '', gender: '', address: '', designation: '', facility_name: '', preferred_language: 'en', role: 'patient' as 'patient' | 'healthcare_worker' })
  const [error, setError] = useState('')
  const [history, setHistory] = useState<Array<{ id: number; document_id: number; original_text: string; translated_text: string; review_required: boolean }>>([])
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

function Dashboard({ user, onProfile, onWorkspace }: { user: AuthUser; onProfile: () => void; onWorkspace: () => void }) {
  const roleTitle = user.role === 'patient' ? 'Patient dashboard' : user.role === 'healthcare_worker' ? 'Healthcare worker dashboard' : 'Administrator dashboard'
  return <section className="dashboard"><div className="workspace-nav" aria-label={`${roleTitle} navigation`}>{roleNavigation[user.role].map((item) => <button key={item} className={item === 'Dashboard' ? 'workspace-nav-active' : ''} onClick={item === 'Dashboard' ? undefined : onWorkspace}>{item}</button>)}</div><div className="welcome-panel"><div><p className="eyebrow">YOUR AROGYAMITRA WORKSPACE</p><h1>Welcome, {user.full_name.split(' ')[0]}.</h1><p>Healthcare in Your Language, Care for Everyone.</p></div><button className="primary-button" onClick={onProfile}>Manage profile <span>→</span></button></div><div className="dashboard-grid"><article className="info-card"><span className="card-icon">◉</span><h3>{roleTitle}</h3><p>Your secure workspace is ready. Use the navigation above to access role-specific tools.</p><span className="status-label">Foundation complete</span></article><article className="info-card"><span className="card-icon blue">文</span><h3>Language preference</h3><p>You are viewing ArogyaMitra in <strong>{user.preferred_language.name}</strong>.</p><span className="status-label blue-label">Personalized access</span></article><article className="info-card"><span className="card-icon orange">✓</span><h3>Care and privacy</h3><p>Your account data is protected. Do not upload or share information that is not yours.</p><span className="status-label orange-label">Safety first</span></article></div><div className="coming-section"><p className="eyebrow">NEXT MILESTONES</p><h2>More support, step by step</h2><div className="coming-grid"><span>Medical document understanding</span><span>Simple explanations and translation</span><span>Voice-enabled assistance</span></div></div></section>
}

function WorkspaceNotice({ user, onBack }: { user: AuthUser; onBack: () => void }) {
  if (user.role === 'patient') return <PatientServices user={user} onBack={onBack} />
  return user.role === 'healthcare_worker' ? <WorkerWorkspace onBack={onBack} /> : <AdminWorkspace onBack={onBack} />
}

function WorkerWorkspace({ onBack }: { onBack: () => void }) {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [followUps, setFollowUps] = useState<FollowUp[]>([])
  const [history, setHistory] = useState<Array<{ id: number; document_id: number; original_text: string; translated_text: string; review_required: boolean }>>([])
  const [error, setError] = useState('')
  useEffect(() => { Promise.all([listAssignedPatients(), listWorkerFollowUps()]).then(([nextPatients, nextFollowUps]) => { setPatients(nextPatients); setFollowUps(nextFollowUps) }).catch(() => setError('Worker services require an approved account and assigned patients.')) }, [])
  const loadHistory = async (patientId: number) => { try { setHistory(await listTranslationHistory(patientId)); setError('') } catch { setError('Unable to load authorized translation history.') } }
  return <section className="services-page"><button className="link-button back-link" onClick={onBack}>← Back to dashboard</button><div className="page-heading"><p className="eyebrow">HEALTHCARE WORKER</p><h1>Patient management and follow-ups</h1><p>Only patients assigned by an administrator are shown.</p></div><div className="services-grid"><article className="profile-card"><h3>Assigned patients</h3>{patients.map((patient) => <div className="service-row" key={patient.id}><span><strong>{patient.full_name}</strong><small>{patient.email} · {patient.preferred_language}</small></span><button className="link-button" onClick={() => loadHistory(patient.id)}>Translations</button></div>)}{patients.length === 0 && <p className="muted-text">No assigned patients.</p>}</article><article className="profile-card"><h3>Follow-up monitoring</h3>{followUps.map((followUp) => <div className="service-row" key={followUp.id}><span><strong>Patient {followUp.patient_id}</strong><small>{new Date(followUp.due_at).toLocaleString()} · {followUp.status}</small></span></div>)}{followUps.length === 0 && <p className="muted-text">No follow-ups scheduled.</p>}</article><article className="profile-card"><h3>Translation support</h3>{history.map((item) => <div className="article-row" key={item.id}><strong>{item.translated_text}</strong><small>{item.original_text} · {item.review_required ? 'Review required' : 'Reviewed'}</small></div>)}{history.length === 0 && <p className="muted-text">Select an assigned patient to view translations.</p>}</article></div>{error && <p className="form-error" role="alert">{error}</p>}</section>
}

function AdminWorkspace({ onBack }: { onBack: () => void }) {
  const [analytics, setAnalytics] = useState<Record<string, number> | null>(null)
  const [system, setSystem] = useState<{ api_status: string; database_status: string; ai_provider: string; storage_provider: string } | null>(null)
  const [content, setContent] = useState<HealthContent[]>([])
  const [error, setError] = useState('')
  useEffect(() => { Promise.all([listAdminAnalytics(), getSystemMonitoring(), listAdminContent()]).then(([nextAnalytics, nextSystem, nextContent]) => { setAnalytics(nextAnalytics); setSystem(nextSystem); setContent(nextContent) }).catch(() => setError('Administrator access is required to view analytics and system monitoring.')) }, [])
  return <section className="services-page"><button className="link-button back-link" onClick={onBack}>← Back to dashboard</button><div className="page-heading"><p className="eyebrow">ADMINISTRATION</p><h1>Analytics and system monitoring</h1><p>Operational metrics are aggregated and do not expose patient medical text.</p></div><div className="services-grid"><article className="profile-card"><h3>Analytics</h3>{analytics ? Object.entries(analytics).map(([key, value]) => <div className="service-row" key={key}><strong>{key.split('_').join(' ')}</strong><span>{value}</span></div>) : <p className="muted-text">Loading metrics...</p>}</article><article className="profile-card"><h3>System status</h3>{system ? Object.entries(system).map(([key, value]) => <div className="service-row" key={key}><strong>{key.split('_').join(' ')}</strong><span>{value}</span></div>) : <p className="muted-text">Loading status...</p>}</article><article className="profile-card"><h3>Published health content</h3>{content.map((item) => <div className="article-row" key={item.id}><strong>{item.title}</strong><small>{item.category} · {item.language_code}</small></div>)}{content.length === 0 && <p className="muted-text">No content has been published.</p>}</article></div>{error && <p className="form-error" role="alert">{error}</p>}</section>
}

function PatientServices({ user, onBack }: { user: AuthUser; onBack: () => void }) {
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [articles, setArticles] = useState<HealthContent[]>([])
  const [contacts, setContacts] = useState<Array<{ id: number; name: string; phone_number: string; is_verified: boolean }>>([])
  const [voiceText, setVoiceText] = useState('')
  const [voiceError, setVoiceError] = useState('')
  const [reminderForm, setReminderForm] = useState({ medication_name: '', dosage: '', instructions: '', scheduled_at: '' })
  const [message, setMessage] = useState('')
  const [aiText, setAiText] = useState('')
  const [aiResult, setAiResult] = useState('')

  useEffect(() => {
    Promise.all([listReminders(), listHealthContent(user.preferred_language.code), listEmergencyContacts()])
      .then(([nextReminders, nextArticles, nextContacts]) => {
        setReminders(nextReminders)
        setArticles(nextArticles)
        setContacts(nextContacts)
      })
      .catch(() => setVoiceError('Patient services are temporarily unavailable. Please try again.'))
  }, [user.preferred_language.code])

  const startListening = () => {
    setVoiceError('')
    const speechWindow = window as Window & { webkitSpeechRecognition?: new () => {
      lang: string
      onresult: (event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void
      onerror: () => void
      start: () => void
    } }
    if (!speechWindow.webkitSpeechRecognition) {
      setVoiceError('Speech recognition is not supported in this browser. You can type your question instead.')
      return
    }
    const recognition = new speechWindow.webkitSpeechRecognition()
    recognition.lang = user.preferred_language.code === 'hi' ? 'hi-IN' : user.preferred_language.code === 'mr' ? 'mr-IN' : 'en-IN'
    recognition.onresult = (event) => setVoiceText(event.results[0][0].transcript)
    recognition.onerror = () => setVoiceError('Microphone access or speech recognition failed. Please use text input.')
    recognition.start()
  }

  const speak = () => {
    if (!voiceText.trim() || !window.speechSynthesis) {
      setVoiceError('Text-to-speech is not supported or there is no text to read.')
      return
    }
    const utterance = new SpeechSynthesisUtterance(voiceText)
    utterance.lang = user.preferred_language.code === 'hi' ? 'hi-IN' : user.preferred_language.code === 'mr' ? 'mr-IN' : 'en-IN'
    window.speechSynthesis.speak(utterance)
  }

  const addReminder = async (event: FormEvent) => {
    event.preventDefault()
    try {
      const reminder = await createReminder(reminderForm)
      setReminders([...reminders, reminder])
      setReminderForm({ medication_name: '', dosage: '', instructions: '', scheduled_at: '' })
      setMessage('Reminder saved. Delivery is not claimed until a provider confirms it.')
    } catch {
      setVoiceError('Unable to save the reminder.')
    }
  }

  const markTaken = async (id: number) => {
    const updated = await updateReminderStatus(id, 'taken')
    setReminders(reminders.map((item) => item.id === id ? updated : item))
  }

  const runAi = async (operation: 'simplify' | 'translate') => {
    try {
      const result = operation === 'simplify'
        ? await simplifyMedicalText(aiText, user.preferred_language.code)
        : await translateMedicalText(aiText, user.preferred_language.code)
      setAiResult(result.simplified_text || result.translated_text || '')
      setVoiceError('')
    } catch {
      setVoiceError('The medical text service is unavailable. Please try again later.')
    }
  }

  return <section className="services-page"><button className="link-button back-link" onClick={onBack}>← Back to dashboard</button><div className="page-heading"><p className="eyebrow">PATIENT SERVICES</p><h1>Voice, reminders and health education</h1><p>These tools support communication and organization. They do not diagnose or replace emergency care.</p></div>
    <div className="services-grid">
      <article className="profile-card"><h3>Medical language support</h3><textarea value={aiText} onChange={(event) => setAiText(event.target.value)} placeholder="Paste a medical term or instruction" /><div className="service-actions"><button className="primary-button" disabled={!aiText.trim()} onClick={() => runAi('simplify')}>Explain simply</button><button className="outline-button" disabled={!aiText.trim()} onClick={() => runAi('translate')}>Translate</button></div>{aiResult && <p className="success-message">{aiResult}</p>}</article>
      <article className="profile-card"><h3>Voice assistance</h3><p className="muted-text">Use your browser microphone and speech engine. Recognized text stays editable.</p><textarea value={voiceText} onChange={(event) => setVoiceText(event.target.value)} placeholder="Speak or type a question" /><div className="service-actions"><button className="primary-button" onClick={startListening}>Start listening</button><button className="outline-button" onClick={speak}>Read aloud</button></div></article>
      <article className="profile-card"><h3>Medication reminders</h3><form className="service-form" onSubmit={addReminder}><input required placeholder="Medicine name" value={reminderForm.medication_name} onChange={(event) => setReminderForm({ ...reminderForm, medication_name: event.target.value })} /><input required placeholder="Dosage" value={reminderForm.dosage} onChange={(event) => setReminderForm({ ...reminderForm, dosage: event.target.value })} /><input required placeholder="Instructions" value={reminderForm.instructions} onChange={(event) => setReminderForm({ ...reminderForm, instructions: event.target.value })} /><input required type="datetime-local" value={reminderForm.scheduled_at} onChange={(event) => setReminderForm({ ...reminderForm, scheduled_at: event.target.value })} /><button className="primary-button">Save reminder</button></form>{reminders.map((reminder) => <div className="service-row" key={reminder.id}><span><strong>{reminder.medication_name}</strong><small>{reminder.dosage} · {new Date(reminder.scheduled_at).toLocaleString()}</small></span>{reminder.status === 'scheduled' && <button className="link-button" onClick={() => markTaken(reminder.id)}>Mark taken</button>}</div>)}</article>
      <article className="profile-card"><h3>Emergency assistance</h3><p className="muted-text">For life-threatening situations, call emergency services immediately.</p>{contacts.map((contact) => <div className="service-row" key={contact.id}><span><strong>{contact.name}</strong><small>Verified contact</small></span><a className="primary-button" href={`tel:${contact.phone_number}`}>Call {contact.phone_number}</a></div>)}</article>
      <article className="profile-card"><h3>Health education</h3>{articles.map((article) => <div className="article-row" key={article.id}><strong>{article.title}</strong><small>{article.category} · {article.description}</small></div>)}{articles.length === 0 && <p className="muted-text">No published articles are available in your language yet.</p>}</article>
    </div>{message && <p className="success-message">{message}</p>}{voiceError && <p className="form-error" role="alert">{voiceError}</p>}
  </section>
}

function ProfilePage({ user, onUpdated, onBack }: { user: AuthUser; onUpdated: (user: AuthUser) => void; onBack: () => void }) {
  const [form, setForm] = useState({ full_name: user.full_name, phone_number: user.phone_number || '', preferred_language: user.preferred_language.code, age: user.age?.toString() || '', date_of_birth: user.date_of_birth || '', gender: user.gender || '', address: user.address || '', facility_name: user.facility_name || '', specialization: user.specialization || '', designation: user.designation || '' })
  const [message, setMessage] = useState(''); const [error, setError] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); setMessage(''); setError(''); try { const updated = await updateProfile({ ...form, age: form.age ? Number(form.age) : undefined, date_of_birth: form.date_of_birth || undefined }); onUpdated(updated); setMessage('Profile updated successfully.') } catch (requestError: any) { setError(requestError.response?.data?.detail || 'Unable to update your profile.') } }
  return <section className="profile-page"><button className="link-button back-link" onClick={onBack}>← Back to dashboard</button><div className="page-heading"><p className="eyebrow">ACCOUNT SETTINGS</p><h1>Manage your profile</h1><p>Keep your contact details and language preference current.</p></div><form className="profile-card" onSubmit={submit}><div className="form-grid"><label>Full name<input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label><label>Email address<input disabled value={user.email} /></label></div><div className="form-grid"><label>Phone number<input type="tel" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} /></label><label>Preferred language<select value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}><option value="en">English</option><option value="hi">Hindi</option><option value="mr">Marathi</option><option value="bn">Bengali</option><option value="ta">Tamil</option><option value="te">Telugu</option></select></label></div><label>Address<input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label>{user.role === 'patient' && <div className="form-grid"><label>Age<input type="number" min="0" max="130" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} /></label><label>Date of birth<input type="date" value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} /></label></div>}{user.role === 'healthcare_worker' && <><div className="form-grid"><label>Designation<input value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} /></label><label>Facility name<input value={form.facility_name} onChange={(e) => setForm({ ...form, facility_name: e.target.value })} /></label></div><label>Specialization<input value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} /></label></>}{message && <p className="success-message">{message}</p>}{error && <p className="form-error">{error}</p>}<button className="primary-button">Save changes</button></form></section>
}
