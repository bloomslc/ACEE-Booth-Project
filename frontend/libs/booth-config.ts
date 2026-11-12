export type SocialType = 'bloom' | 'linkedin' | 'instagram' | 'facebook'

export const boothConfig = {
  eventName: 'ACEE Photo Booth',
  links: [
    { title: 'Bloom', type: 'bloom', href: 'https://slc.qc.ca/bloom' },
    { title: 'LinkedIn', type: 'linkedin', href: 'https://www.linkedin.com/company/slcbloom/' },
    { title: 'Instagram', type: 'instagram', href: 'https://www.instagram.com/slcbloom/' },
    { title: 'Facebook', type: 'facebook', href: 'https://www.facebook.com/slcbloom/' },
  ] satisfies ReadonlyArray<{ title: string; type: SocialType; href: string }>,
} as const

export type GuestInfo = {
  name: string
  email: string
}
