import type { GuestInfo } from './booth-config'
import { getApiUrl } from './server-settings'

const apiToken = process.env.NEXT_PUBLIC_API_TOKEN ?? ''
const frontendDevBypass = process.env.NEXT_PUBLIC_DEV_BYPASS === 'true'

type CapturedPhoto = {
  imageUrl: string
  sessionId: string
  remoteUrl: string | null
}

export type CameraMode = 'live' | 'ftp'

export class CaptureTimeoutError extends Error {
  constructor() {
    super('No photo arrived from the camera yet')
  }
}

export async function getCameraMode(): Promise<CameraMode> {
  if (frontendDevBypass) {
    return 'live'
  }

  try {
    const response = await fetch(`${getApiUrl()}/api/v1/health`)
    const body = await response.json()
    return body?.camera_mode === 'ftp' ? 'ftp' : 'live'
  } catch {
    return 'live'
  }
}

export type CameraStatus = {
  waiting: boolean
  ftp: {
    running: boolean
    port: number | null
    clients: number
    last_login_seconds_ago: number | null
    last_login_failed_seconds_ago: number | null
    last_upload: { name: string; seconds_ago: number; used: boolean } | null
  } | null
}

export async function getCameraStatus(): Promise<CameraStatus | null> {
  try {
    const response = await fetch(`${getApiUrl()}/api/v1/camera/status`, {
      headers: authHeaders(),
      signal: AbortSignal.timeout(4000),
    })
    return response.ok ? ((await response.json()) as CameraStatus) : null
  } catch {
    return null
  }
}

function authHeaders(): Record<string, string> {
  return apiToken ? { 'X-Booth-Token': apiToken } : {}
}

export function previewStreamUrl(): string {
  if (frontendDevBypass) {
    return '/image.jpg'
  }

  // Images cannot send headers, so the preview stream takes the token as a query parameter.
  const query = apiToken ? `?token=${encodeURIComponent(apiToken)}` : ''
  return `${getApiUrl()}/api/v1/camera/preview${query}`
}

export async function capturePhoto(signal?: AbortSignal): Promise<CapturedPhoto> {
  if (frontendDevBypass) {
    return {
      imageUrl: '/image.jpg',
      sessionId: crypto.randomUUID(),
      remoteUrl: null,
    }
  }

  const response = await fetch(`${getApiUrl()}/api/v1/capture`, {
    method: 'POST',
    headers: authHeaders(),
    signal,
  })
  const body = await response.json().catch(() => null)

  if (response.status === 408) {
    throw new CaptureTimeoutError()
  }

  if (!response.ok) {
    throw new Error(body?.detail ?? 'The photo could not be captured')
  }

  if (typeof body?.image_url !== 'string' || typeof body?.session_id !== 'string') {
    throw new Error('The camera returned an invalid capture response')
  }

  return {
    imageUrl: body.image_url,
    sessionId: body.session_id,
    remoteUrl: body.remote_url,
  }
}

export async function sendPhotoByEmail(
  guest: GuestInfo,
  imageUrl: string | null,
  sessionId: string | null,
): Promise<void> {
  if (frontendDevBypass) {
    return
  }

  const response = await fetch(`${getApiUrl()}/api/v1/deliveries/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({
      name: guest.name,
      email: guest.email,
      image_url: imageUrl,
      session_id: sessionId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'The photo could not be sent')
  }
}
