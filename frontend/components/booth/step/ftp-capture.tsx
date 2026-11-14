import { ArrowLeft, Camera } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "../booth-structure";
import Button from "@/components/button";
import { CaptureTimeoutError, capturePhoto } from "@/libs/api";

interface FtpCaptureProps {
    onCapture: (imageUrl: string, sessionId: string) => void;
    onCancel: () => void;
}

const retryDelayMs = 3000

export default function FtpCapture({ onCapture, onCancel }: FtpCaptureProps) {
    const [error, setError] = useState<string | null>(null)
    const onCaptureRef = useRef(onCapture)

    useEffect(() => {
        onCaptureRef.current = onCapture
    }, [onCapture])

    useEffect(() => {
        const controller = new AbortController()

        async function waitForPhoto() {
            while (!controller.signal.aborted) {
                try {
                    const photo = await capturePhoto(controller.signal)
                    onCaptureRef.current(photo.imageUrl, photo.sessionId)
                    return
                } catch (captureError) {
                    if (controller.signal.aborted) return
                    // A timeout only means nobody has shot yet, so keep waiting.
                    if (captureError instanceof CaptureTimeoutError) continue
                    setError(captureError instanceof Error ? captureError.message : 'The photo could not be received')
                    await new Promise((resolve) => setTimeout(resolve, retryDelayMs))
                    setError(null)
                }
            }
        }

        void waitForPhoto()
        return () => controller.abort()
    }, [])

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden rounded-3xl border border-[#dbe7f2] bg-[#f7faff] p-8 text-center text-text shadow-[0_18px_50px_rgba(26,54,102,0.10)]">
                    <div className="flex max-w-md flex-col items-center gap-5">
                        <Camera size={72} aria-hidden="true" className="animate-pulse text-[#5d9bd1]" />
                        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Take the photo with the camera</h1>
                        <p className="text-sm leading-6 text-[#607797] sm:text-base">
                            Press the camera&apos;s shutter. Your photo will appear here automatically.
                        </p>
                        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
                    </div>
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={1}>
                <Button
                    onClick={onCancel}
                    style="ghost"
                    className="min-w-0 cursor-pointer flex items-center justify-center gap-2"
                >
                    <ArrowLeft size={20} />
                    <span>Back</span>
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    )
}
