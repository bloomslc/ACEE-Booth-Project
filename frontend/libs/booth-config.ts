export const boothConfig = {
  eventName: 'ACEE Photo Booth',
  countdownSeconds: 3,
  links: [
    { title: 'Bloom', type: 'bloom' as const, href: 'https://slc.qc.ca/bloom' },
    { title: 'LinkedIn', type: 'linkedin' as const, href: 'https://www.linkedin.com/company/slcbloom/' },
    { title: 'Instagram', type: 'instagram' as const, href: 'https://www.instagram.com/slcbloom/' },
    { title: 'Facebook', type: 'facebook' as const, href: 'https://www.facebook.com/slcbloom/' },
  ],
} as const

export type GuestInfo = {
  name: string
  email: string
}
