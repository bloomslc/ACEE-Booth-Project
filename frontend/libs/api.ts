import type { GuestInfo } from './booth-config'

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8080'

type CapturedPhoto = {
  imageDataUrl: string
  sessionId: string
  remoteUrl: string | null
}

export async function previewPhoto(): Promise<string> {
  const response = await fetch(`${apiUrl}/api/v1/camera/preview`, { method: 'POST' })
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(body?.detail ?? 'The camera preview is unavailable')
  }

  return body.image_data_url
}

export async function capturePhoto(): Promise<CapturedPhoto> {
  const response = await fetch(`${apiUrl}/api/v1/capture`, { method: 'POST' })
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(body?.detail ?? 'The photo could not be captured')
  }

  return {
    imageDataUrl: body.image_data_url,
    sessionId: body.session_id,
    remoteUrl: body.remote_url,
  }
}

export async function sendPhotoByEmail(
  guest: GuestInfo,
  imageDataUrl: string | null,
  sessionId: string | null,
  imageUrl: string | null,
): Promise<void> {
  const response = await fetch(`${apiUrl}/api/v1/deliveries/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: guest.name,
      email: guest.email,
      image_data_url: imageDataUrl,
      image_url: imageUrl,
      session_id: sessionId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'The photo could not be sent')
  }
}