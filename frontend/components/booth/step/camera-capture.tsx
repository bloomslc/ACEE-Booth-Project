import { ArrowLeft } from "lucide-react";
import Image from "next/image";
import BoothStructure, { BoothStructureContent, BoothStructureAction } from "../booth-structure";

interface CameraCaptureProps {
    onCapture: (dataUrl: string) => void;
    onCancel: () => void;
}

export default function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="grid min-h-0 w-full flex-1 place-items-center overflow-hidden">
                    <div className="aspect-2/3 h-full min-h-0 min-w-0 max-h-full w-auto max-w-full rounded-4xl bg-black">
                        <Image src="/image.jpg" width={500} height={750} alt="Camera" className="w-full h-full object-contain rounded-4xl" />
                    </div>
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
                        onClick={() => {
                            // Simulate taking a photo
                            onCapture('');
                        }}
                            type="button"
                            aria-label="Take photo"
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