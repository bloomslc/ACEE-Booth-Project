import type { GuestInfo } from './booth-config'

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8080'

export async function sendPhotoByEmail(
  guest: GuestInfo,
  imageDataUrl: string | null,
): Promise<void> {
  const response = await fetch(`${apiUrl}/api/v1/deliveries/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: guest.name,
      email: guest.email,
      image_data_url: imageDataUrl,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'The photo could not be sent')
  }
}