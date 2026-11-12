const storageKey = 'booth.apiUrl'
const defaultPort = 8080

export const defaultApiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8080'

/**
 * Turn operator input such as "10.1.87.237" or "raspberrypi.local:9000" into an
 * origin like "http://10.1.87.237:8080". Returns null when the input is not a valid address.
 */
export function normalizeServerAddress(input: string): string | null {
  const trimmed = input.trim()
  if (!trimmed) {
    return null
  }

  const hasScheme = /^https?:\/\//i.test(trimmed)
  try {
    const url = new URL(hasScheme ? trimmed : `http://${trimmed}`)
    if (!url.hostname) {
      return null
    }
    if (!hasScheme && !url.port) {
      url.port = String(defaultPort)
    }
    return url.origin
  } catch {
    return null
  }
}

export function getApiUrl(): string {
  if (typeof window === 'undefined') {
    return defaultApiUrl
  }

  try {
    return window.localStorage.getItem(storageKey) ?? defaultApiUrl
  } catch {
    return defaultApiUrl
  }
}

export function saveApiUrl(url: string): void {
  window.localStorage.setItem(storageKey, url)
}

export function resetApiUrl(): void {
  window.localStorage.removeItem(storageKey)
}

export async function checkServer(url: string): Promise<boolean> {
  try {
    const response = await fetch(`${url}/api/v1/health`, { signal: AbortSignal.timeout(5000) })
    return response.ok
  } catch {
    return false
  }
}
