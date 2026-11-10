import type { GuestInfo } from './booth-config'

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8080'
const frontendDevBypass = process.env.NEXT_PUBLIC_DEV_BYPASS === 'true'

type CapturedPhoto = {
  imageUrl: string
  sessionId: string
  remoteUrl: string | null
}

export function previewStreamUrl(): string {
  return frontendDevBypass ? '/image.jpg' : `${apiUrl}/api/v1/camera/preview`
}

export async function capturePhoto(): Promise<CapturedPhoto> {
  if (frontendDevBypass) {
      return {
  		imageUrl: '/image.jpg',
      sessionId: crypto.randomUUID(),
      remoteUrl: null,
    }
  }

  const response = await fetch(`${apiUrl}/api/v1/capture`, { method: 'POST' })
  const body = await response.json().catch(() => null)

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
    console.warn('[email] skipped because NEXT_PUBLIC_DEV_BYPASS is enabled in the frontend build')
    return
  }

  console.info('[email] sending delivery request', { apiUrl, sessionId, hasImageUrl: Boolean(imageUrl) })
  const response = await fetch(`${apiUrl}/api/v1/deliveries/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: guest.name,
      email: guest.email,
      image_url: imageUrl,
      session_id: sessionId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    console.error('[email] delivery request failed', response.status, error)
    throw new Error(error?.detail ?? 'The photo could not be sent')
  }

  console.info('[email] delivery request accepted')
}