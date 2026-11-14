import { ArrowLeft, Camera } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "../booth-structure";
import Button from "@/components/button";
import { CaptureTimeoutError, capturePhoto, getCameraStatus, type CameraStatus } from "@/libs/api";

interface FtpCaptureProps {
    onCapture: (imageUrl: string, sessionId: string) => void;
    onCancel: () => void;
}

const retryDelayMs = 3000
const statusIntervalMs = 2000

function ago(seconds: number): string {
    if (seconds < 5) return 'just now'
    if (seconds < 90) return `${seconds}s ago`
    return `${Math.round(seconds / 60)} min ago`
}

function describeCamera(status: CameraStatus): string {
    const ftp = status.ftp
    if (!ftp) return 'Camera status unavailable'
    if (ftp.clients > 0) return 'Camera connected'
    if (ftp.last_login_seconds_ago !== null) return `Camera last connected ${ago(ftp.last_login_seconds_ago)}`
    if (ftp.last_login_failed_seconds_ago !== null) return 'Camera tried to connect but the login was rejected'
    return 'No camera connection yet. Check the camera FTP settings.'
}

function describeUpload(status: CameraStatus): string | null {
    const upload = status.ftp?.last_upload
    if (!upload) return null
    const suffix = upload.used ? '' : ' (ignored: not a JPEG)'
    return `Last file received: ${upload.name}, ${ago(upload.seconds_ago)}${suffix}`
}

export default function FtpCapture({ onCapture, onCancel }: FtpCaptureProps) {
    const [error, setError] = useState<string | null>(null)
    const [status, setStatus] = useState<CameraStatus | null>(null)
    const [hasStatus, setHasStatus] = useState(false)
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

    useEffect(() => {
        let isActive = true

        async function refresh() {
            const next = await getCameraStatus()
            if (!isActive) return
            setStatus(next)
            setHasStatus(true)
        }

        void refresh()
        const timer = setInterval(() => void refresh(), statusIntervalMs)
        return () => {
            isActive = false
            clearInterval(timer)
        }
    }, [])

    const isUnreachable = hasStatus && status === null
    const isWaiting = status?.waiting === true
    const headline = isUnreachable
        ? 'Cannot reach the booth server'
        : isWaiting
          ? 'Booth is waiting for a photo'
          : 'Connecting to the booth...'
    const dotColor = isUnreachable ? 'bg-red-500' : isWaiting ? 'bg-green-500' : 'bg-amber-400'
    const uploadLine = status ? describeUpload(status) : null

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden rounded-3xl border border-[#dbe7f2] bg-[#f7faff] p-8 text-center text-text shadow-[0_18px_50px_rgba(26,54,102,0.10)]">
                    <div className="flex max-w-md flex-col items-center gap-5">
                        <Camera size={72} aria-hidden="true" className={isWaiting ? 'animate-pulse text-[#5d9bd1]' : 'text-[#91a4bc]'} />
                        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Take the photo with the camera</h1>
                        <p className="text-sm leading-6 text-[#607797] sm:text-base">
                            Press the camera&apos;s shutter. Your photo will appear here automatically.
                        </p>
                        <div role="status" className="flex w-full flex-col gap-1 rounded-2xl bg-white px-4 py-3 text-sm">
                            <p className="flex items-center justify-center gap-2 font-semibold">
                                <span aria-hidden="true" className={`h-3 w-3 rounded-full ${dotColor} ${isWaiting ? 'animate-pulse' : ''}`} />
                                {headline}
                            </p>
                            {status && <p className="text-[#607797]">{describeCamera(status)}</p>}
                            {uploadLine && <p className="text-[#607797]">{uploadLine}</p>}
                        </div>
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
