"use client";

import type { GuestInfo } from '@/libs/booth-config';
import { useCallback, useState } from "react";
import BoothHome from "./step/booth-home";
import CameraCapture from "./step/camera-capture";
import PhotoReview from './step/photo-review';
import GuestForm from './step/guest-form';
import ThankYou from './thank-you';
import { sendPhotoByEmail } from '@/libs/api';

type Step = 'home' | 'camera' | 'review' | 'guest' | 'done'

const emptyGuest: GuestInfo = { name: '', email: '' }

export default function PhotoBooth() {
    const [step, setStep] = useState<Step>('home')
    const [guest, setGuest] = useState<GuestInfo>(emptyGuest)
    const [photo, setPhoto] = useState<string | null>(null)
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [deliveryError, setDeliveryError] = useState<string | null>(null)
    const [isSending, setIsSending] = useState(false)

    const startNewSession = useCallback(() => {
        setGuest(emptyGuest)
        setPhoto(null)
        setSessionId(null)
        setDeliveryError(null)
        setIsSending(false)
        setStep('home')
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
                    onCapture={(dataUrl, capturedSessionId) => {
                        setPhoto(dataUrl)
                        setSessionId(capturedSessionId)
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
                        setDeliveryError(null)
                        setIsSending(true)
                        void sendPhotoByEmail(guestInfo, photo, sessionId)
                            .then(() => setStep('done'))
                            .catch((error: unknown) => {
                                setDeliveryError(
                                    error instanceof Error ? error.message : 'The photo could not be sent',
                                )
                            })
                            .finally(() => setIsSending(false))
                    }}
                    onCancel={startNewSession}
                    isSending={isSending}
                    error={deliveryError}
                />
            )}

            {step === 'done' && (
                <ThankYou
                    onBackHome={startNewSession}
                    guest={guest}
                />
            )}
        </main>
    )
}