import { ArrowLeft } from "lucide-react";
import Image from "next/image";
import BoothStructure, { BoothStructureContent, BoothStructureAction } from "../booth-structure";
import { capturePhoto, previewPhoto } from "@/libs/api";
import { useEffect, useRef, useState } from "react";
import Button from "@/components/button";

interface CameraCaptureProps {
    onCapture: (imageUrl: string, sessionId: string) => void;
    onCancel: () => void;
}

export default function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
    const [isCapturing, setIsCapturing] = useState(false)
    const [preview, setPreview] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const hasPreview = useRef(false)
    const isPreviewing = useRef(false)
    const isCapturingRef = useRef(false)
    const previewController = useRef<AbortController | null>(null)

    useEffect(() => {
        let isActive = true

        async function refreshPreview() {
            if (isCapturingRef.current || isPreviewing.current) {
                return
            }

            isPreviewing.current = true
            const controller = new AbortController()
            previewController.current = controller
            try {
                const imageDataUrl = await previewPhoto(controller.signal)
                if (isActive) {
                    setPreview(imageDataUrl)
                    hasPreview.current = true
                    setError(null)
                }
            } catch (previewError) {
                if (isActive && !hasPreview.current && controller.signal.reason === undefined) {
                    setError(previewError instanceof Error ? previewError.message : 'The camera preview is unavailable')
                }
            } finally {
                isPreviewing.current = false
                if (previewController.current === controller) {
                    previewController.current = null
                }
            }
        }

        void refreshPreview()
        const interval = window.setInterval(() => void refreshPreview(), 1500)

        return () => {
            isActive = false
            previewController.current?.abort()
            window.clearInterval(interval)
        }
    }, [])

    async function handleCapture() {
        isCapturingRef.current = true
        previewController.current?.abort()
        setIsCapturing(true)
        setError(null)
        try {
            const capturedPhoto = await capturePhoto()
            onCapture(capturedPhoto.imageUrl, capturedPhoto.sessionId)
        } catch (captureError) {
            setError(captureError instanceof Error ? captureError.message : 'The photo could not be captured')
        } finally {
            isCapturingRef.current = false
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
                <Button
                    onClick={onCancel}
                    style="ghost"
                    className="min-w-0 cursor-pointer flex items-center justify-center gap-2"
                >
                    <ArrowLeft size={20} />
                    <span>Back</span>
                </Button>
                <div className="flex min-w-0 h-full items-center justify-center">
                    <button
                        onClick={() => void handleCapture()}
                        type="button"
                        aria-label="Take photo"
                        disabled={isCapturing}
                        className="group flex h-full w-auto aspect-square items-center justify-center rounded-full p-2 border-4 border-red-500 transition-transform active:scale-95 disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
                    >
                        <span className="h-full w-auto aspect-square rounded-full bg-red-500 transition-transform group-active:scale-90" />
                    </button>
                </div>
                <span className="min-w-0 text-center text-text">
                    Tap to shoot
                </span>
            </BoothStructureAction>
        </BoothStructure>
    )
}