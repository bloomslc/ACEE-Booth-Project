import Image from 'next/image'
import { useState } from 'react'
import { boothConfig } from '@/libs/booth-config'
import Qrcode from './qrcode'

type SocialLink = (typeof boothConfig.links)[number]

export default function Social() {
    const [selectedSocial, setSelectedSocial] = useState<SocialLink>()
    return (
        <>
            <div>
                <h2>Follow our social media</h2>
                <div className="grid grid-cols-4 gap-3">
                    {boothConfig.links.map((social) => (
                        <button
                            key={social.type}
                            type="button"
                            aria-label={social.title}
                            onClick={() => setSelectedSocial(social)}
                            className="flex flex-col items-center gap-2 rounded-4xl bg-secondary p-5 text-text shadow-sm"
                        >
                            <Image src={`/${social.type}.svg`} width={48} height={48} alt="" aria-hidden="true" />
                        </button>
                    ))}
                </div>
            </div>
            {selectedSocial && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
                    role="dialog"
                    aria-modal="true"
                    aria-label={`${selectedSocial.title} QR code`}
                    onClick={() => setSelectedSocial(undefined)}
                >
                    <div className="relative rounded-4xl bg-white p-6" onClick={(event) => event.stopPropagation()}>
                        <Qrcode value={selectedSocial.href} type={selectedSocial.type} />
                    </div>
                </div>
            )}
        </>
    )
}
