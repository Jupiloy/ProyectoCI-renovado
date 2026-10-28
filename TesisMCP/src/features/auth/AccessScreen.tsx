import { useState, type FormEvent } from "react"
import { ApiError } from "../../api/client"
import type { SessionResponse } from "../../api/types"

interface AccessScreenProps {
  csrfToken: string | null
  connectionError: string | null
  onRetryConnection: () => void
  onRefreshCsrf: () => Promise<void>
  onLogin: (email: string, password: string, csrfToken: string) => Promise<SessionResponse>
  onAuthenticated: (session: SessionResponse) => void
  onDemo: () => void
}

export default function AccessScreen({
  csrfToken,
  connectionError,
  onRetryConnection,
  onRefreshCsrf,
  onLogin,
  onAuthenticated,
  onDemo,
}: AccessScreenProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!csrfToken || submitting) return
    setError(null)
    setSubmitting(true)
    try {
      const response = await onLogin(email.trim(), password, csrfToken)
      if (!response.authenticated || !response.user) {
        throw new Error("El servidor no devolvió una sesión autenticada.")
      }
      setPassword("")
      onAuthenticated(response)
    } catch (cause) {
      if (cause instanceof ApiError && cause.kind === "csrf") {
        try {
          await onRefreshCsrf()
          setError("Actualizamos la protección de la sesión. Pulsa «Iniciar sesión» para volver a intentarlo.")
        } catch {
          setError("No se pudo actualizar la protección CSRF. Recarga la página e inténtalo de nuevo.")
        }
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo iniciar sesión.")
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-screen">
      <section className="login-brand-panel">
        <div className="login-brand">
          <div className="brand-mark" aria-hidden="true">T</div>
          <div>
            <b>TesisMCP</b>
            <span>Escritura e investigación académica</span>
          </div>
        </div>
        <div className="login-promise">
          <span className="eyebrow">TU TESIS, EN UN SOLO ESPACIO</span>
          <h1>Investiga, escribe y revisa con trazabilidad.</h1>
          <p>Un espacio de trabajo documental para tesistas y asesores, con fuentes, versiones y observaciones vinculadas.</p>
        </div>
        <div className="login-feature-list">
          <span>Editor académico con versiones</span>
          <span>Evidencia y referencias revisables</span>
          <span>Observaciones vinculadas al documento</span>
        </div>
      </section>
      <section className="login-form-panel">
        {connectionError && (
          <div className="auth-alert" role="alert">
            <span>{connectionError}</span>
            <button type="button" className="text-link" onClick={onRetryConnection}>Reintentar conexión</button>
          </div>
        )}
        <div className="login-card">
          <span className="eyebrow blue">ACCESO AL ESPACIO ACADÉMICO</span>
          <h2>Iniciar sesión</h2>
          <p>Ingresa con la cuenta que te asignó la institución.</p>
          <form onSubmit={handleSubmit}>
            <label className="login-field">
              Correo electrónico
              <input
                type="email"
                name="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                disabled={!csrfToken || submitting}
              />
            </label>
            <label className="login-field">
              Contraseña
              <input
                type="password"
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                disabled={!csrfToken || submitting}
              />
            </label>
            {error && <div className="auth-alert" role="alert">{error}</div>}
            <button className="button button-primary access-submit" type="submit" disabled={!csrfToken || submitting}>
              {submitting ? "Validando…" : "Iniciar sesión"}
            </button>
          </form>
          <button type="button" className="button button-secondary access-demo" onClick={onDemo}>
            Entrar en modo demostración
          </button>
          <small className="auth-scope">El registro público y la recuperación de contraseña no están disponibles.</small>
        </div>
      </section>
    </main>
  )
}
