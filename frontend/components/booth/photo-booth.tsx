"use client";

import { boothConfig, type GuestInfo } from '@/libs/booth-config';
import { useCallback, useState } from "react";
import BoothHome from "./step/booth-home";
import CameraCapture from "./step/camera-capture";
import PhotoReview from './step/photo-review';
import GuestForm from './step/guest-form';
import ThankYou from './thank-you';

type Step = 'home' | 'camera' | 'review' | 'guest' | 'done'

const emptyGuest: GuestInfo = { name: '', email: '' }

export default function PhotoBooth() {
    const [step, setStep] = useState<Step>('home')
    const [guest, setGuest] = useState<GuestInfo>(emptyGuest)
    const [photo, setPhoto] = useState<string | null>(null)
    const [sessionKey, setSessionKey] = useState<string | null>(null)

    const startNewSession = useCallback(() => {
        setGuest(emptyGuest)
        setPhoto(null)
        setStep('home')
        setSessionKey(crypto.randomUUID())
    }, [])

    return (
        <main>
            {step === 'home' && (
                <BoothHome 
                    onBegin={() => {
                        startNewSession()
                        setStep('camera')
                    }}
                />
            )}

            {step === 'camera' && (
                <CameraCapture
                    onCancel={startNewSession}
                    onCapture={(dataUrl) => {
                        setPhoto(dataUrl)
                        setStep('review')
                    }}
                />
            )}

            {step === 'review' && (
                <PhotoReview
                    photo={photo!}
                    onAccept={() => setStep('guest')}
                    onCancel={startNewSession}
                    onRetake={() => {
                        setPhoto(null)
                        setStep('camera')
                    }}
                />
            )}

            {step === 'guest' && (
                <GuestForm 
                    onSubmit={(guestInfo) => {
                        setGuest(guestInfo)
                        setStep('done')
                    }}
                    onCancel={startNewSession}
                />
            )}

            {step === 'done' && (
                <ThankYou
                    onBackHome={startNewSession}
                    guest={guest}
                    sessionKey={sessionKey}
                />
            )}
        </main>
    )
}