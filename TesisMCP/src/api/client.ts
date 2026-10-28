export type ApiRequestOptions = RequestInit & {
  csrfToken?: string
  idempotencyKey?: string
  expectedVersion?: string
}

const API_PREFIX = "/api/v1"

export type ApiErrorKind = "csrf" | "permission" | "unknown"

export class ApiError extends Error {
  readonly status: number
  readonly detail: string
  readonly kind: ApiErrorKind

  constructor(status: number, detail: string, kind: ApiErrorKind = "unknown") {
    super(detail)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
    this.kind = kind
  }
}

function defaultMessage(status: number): string {
  if (status === 400) return "La solicitud contiene datos no válidos."
  if (status === 401) return "La sesión terminó o las credenciales no son válidas."
  if (status === 403) return "El servidor rechazó la solicitud (HTTP 403)."
  if (status === 404) return "El recurso ya no está disponible."
  if (status === 409) return "El recurso cambió. Recarga los datos antes de continuar."
  if (status >= 500) return "El servidor no pudo completar la solicitud. Inténtalo más tarde."
  return `La solicitud no se completó (HTTP ${status}).`
}

async function readError(response: Response): Promise<ApiError> {
  const contentType = response.headers.get("content-type") ?? ""
  if (contentType.includes("application/json")) {
    try {
      const body: unknown = await response.json()
      if (body && typeof body === "object" && "detail" in body) {
        const detail = (body as { detail?: unknown }).detail
        if (typeof detail === "string" && detail.trim()) {
          const kind: ApiErrorKind = response.status === 403 && detail.startsWith("PERMISSION_DENIED:")
            ? "permission"
            : response.status === 403 && detail.startsWith("CSRF_") ? "csrf" : "unknown"
          return new ApiError(response.status, detail, kind)
        }
      }
    } catch {
      // A malformed JSON response falls back to a status-specific message.
    }
  }
  if (response.status === 403 && contentType.includes("text/html")) {
    const html = await response.text()
    if (/\bcsrf\b/i.test(html)) {
      return new ApiError(403, "La protección CSRF rechazó la solicitud. Actualiza la sesión y vuelve a intentarlo.", "csrf")
    }
  }
  // Do not surface Django's HTML CSRF error page or a proxy error page to the user.
  return new ApiError(response.status, defaultMessage(response.status))
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { csrfToken, idempotencyKey, expectedVersion, headers, ...request } = options
  const requestHeaders = new Headers(headers)
  requestHeaders.set("Accept", "application/json")

  const isFormData = typeof FormData !== "undefined" && request.body instanceof FormData
  if (request.body && !isFormData && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json")
  }
  if (csrfToken) requestHeaders.set("X-CSRFToken", csrfToken)
  if (idempotencyKey) requestHeaders.set("Idempotency-Key", idempotencyKey)
  if (expectedVersion) requestHeaders.set("If-Match", expectedVersion)

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...request,
    credentials: "include",
    headers: requestHeaders,
  })

  if (!response.ok) throw await readError(response)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function apiDownload(
  path: string,
  options: ApiRequestOptions = {},
): Promise<{ blob: Blob; filename?: string }> {
  const { csrfToken, idempotencyKey, expectedVersion, headers, ...request } = options
  const requestHeaders = new Headers(headers)
  if (csrfToken) requestHeaders.set("X-CSRFToken", csrfToken)
  if (idempotencyKey) requestHeaders.set("Idempotency-Key", idempotencyKey)
  if (expectedVersion) requestHeaders.set("If-Match", expectedVersion)

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...request,
    credentials: "include",
    headers: requestHeaders,
  })

  if (!response.ok) throw await readError(response)

  const disposition = response.headers.get("content-disposition")
  let filename: string | undefined
  if (disposition && disposition.includes("filename=")) {
    const match = disposition.match(/filename=["']?([^"';]+)["']?/)
    if (match) filename = match[1]
  }
  const blob = await response.blob()
  return { blob, filename }
}
