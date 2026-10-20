import { ArrowLeft } from "lucide-react";
import Image from "next/image";
import BoothStructure, { BoothStructureContent, BoothStructureAction } from "../booth-structure";
import { capturePhoto, previewPhoto } from "@/libs/api";
import { useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
    onCapture: (dataUrl: string, sessionId: string) => void;
    onCancel: () => void;
}

export default function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
    const [isCapturing, setIsCapturing] = useState(false)
    const [preview, setPreview] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const hasPreview = useRef(false)

    useEffect(() => {
        let isActive = true

        async function refreshPreview() {
            try {
                const imageDataUrl = await previewPhoto()
                if (isActive) {
                    setPreview(imageDataUrl)
                    hasPreview.current = true
                    setError(null)
                }
            } catch (previewError) {
                if (isActive && !hasPreview.current) {
                    setError(previewError instanceof Error ? previewError.message : 'The camera preview is unavailable')
                }
            }
        }

        void refreshPreview()
        const interval = window.setInterval(() => void refreshPreview(), 1500)

        return () => {
            isActive = false
            window.clearInterval(interval)
        }
    }, [])

    async function handleCapture() {
        setIsCapturing(true)
        setError(null)
        try {
            const capturedPhoto = await capturePhoto()
            onCapture(capturedPhoto.imageDataUrl, capturedPhoto.sessionId)
        } catch (captureError) {
            setError(captureError instanceof Error ? captureError.message : 'The photo could not be captured')
        } finally {
            setIsCapturing(false)
        }
    }

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="grid min-h-0 w-full flex-1 place-items-center overflow-hidden">
                    <div className="aspect-2/3 h-full min-h-0 min-w-0 max-h-full w-auto max-w-full rounded-4xl bg-black">
                        <Image src={preview ?? "/image.jpg"} width={500} height={750} alt="Camera preview" className="w-full h-full object-contain rounded-4xl" />
                    </div>
                    {error && <p className="absolute bottom-4 max-w-sm text-center text-red-600">{error}</p>}
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={3}>
                <button
                    onClick={onCancel}
                    className="min-w-0 cursor-pointer flex items-center justify-center gap-2"
                >
                    <ArrowLeft size={20} />
                    <span>Back</span>
                </button>
                <div className="flex min-w-0 h-full items-center justify-center">
                    <button
                        onClick={() => void handleCapture()}
                            type="button"
                            aria-label="Take photo"
                            disabled={isCapturing}
                            className="group flex size-17 items-center justify-center rounded-full border-4 border-red-500 transition-transform active:scale-95 disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
                        >
                        <span className="size-12 rounded-full bg-red-500 transition-transform group-active:scale-90" />
                    </button>
                </div>
                <span className="min-w-0 text-center">
                    Tap to shoot
                </span>
            </BoothStructureAction>
        </BoothStructure>
    )
}