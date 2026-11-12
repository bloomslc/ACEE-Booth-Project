import { ArrowLeft } from "lucide-react";
import Image from "next/image";
import BoothStructure, { BoothStructureContent, BoothStructureAction } from "../booth-structure";
import { capturePhoto, previewStreamUrl } from "@/libs/api";
import { useState } from "react";
import Button from "@/components/button";

interface CameraCaptureProps {
    onCapture: (imageUrl: string, sessionId: string) => void;
    onCancel: () => void;
}

export default function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
    const [isCapturing, setIsCapturing] = useState(false)
    const [isPreviewEnabled, setIsPreviewEnabled] = useState(true)
    const [error, setError] = useState<string | null>(null)

    async function handleCapture() {
        setIsPreviewEnabled(false)
        setIsCapturing(true)
        setError(null)
        try {
            await new Promise<void>((resolve) => window.requestAnimationFrame(() => resolve()))
            const capturedPhoto = await capturePhoto()
            onCapture(capturedPhoto.imageUrl, capturedPhoto.sessionId)
        } catch (captureError) {
            setIsPreviewEnabled(true)
            setError(captureError instanceof Error ? captureError.message : 'The photo could not be captured')
        } finally {
            setIsCapturing(false)
        }
    }

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden rounded-3xl border border-[#dbe7f2] bg-[#f7faff] p-4 shadow-[0_18px_50px_rgba(26,54,102,0.10)]">
                    <div className="aspect-2/3 h-full min-h-0 min-w-0 max-h-full w-auto max-w-full overflow-hidden rounded-2xl bg-black shadow-inner">
                        {isPreviewEnabled ? (
                            <Image
                                src={previewStreamUrl()}
                                width={500}
                                height={750}
                                alt="Camera preview"
                                unoptimized
                                onError={() => setError('The camera preview is unavailable')}
                                className="w-full h-full object-cover rounded-4xl"
                            />
                        ) : (
                            <div className="h-full w-full" aria-hidden="true" />
                        )}
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