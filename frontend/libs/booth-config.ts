export const boothConfig = {
  eventName: 'ACEE Booth Project',
  countdownSeconds: 3,
  autoResetSeconds: 8,
  links: [
    { label: 'Visit our website', href: 'https://slc.qc.ca/bloom' },
    { label: 'See the gallery', href: 'https://slc.qc.ca/bloom/gallery' },
  ],
} as const

export type GuestInfo = {
  name: string
  email: string
}
