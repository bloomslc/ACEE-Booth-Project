import Image from "next/image";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "../booth-structure";
import Button from "@/components/button";
import { X, RotateCcw, Check } from "lucide-react";

interface PhotoReviewProps {
    onAccept: () => void;
    onCancel: () => void;
    onRetake: () => void;
    photo: string;
}

export default function PhotoReview({ onAccept, onCancel, onRetake, photo }: PhotoReviewProps) {
    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="grid grid-rows-[4fr_1fr] gap-4 w-full max-h-full max-w-full overflow-hidden">
                    <div className="aspect-2/3 bg-white rounded-3xl relative h-full w-auto overflow-hidden">
                        <Image src={photo} width={100} height={100} alt="Captured" unoptimized className="w-full h-full object-contain rounded-3xl" />
                        <Image src="bloom.svg" width={40} height={40} alt="" className="absolute left-2 bottom-2" />
                        <p className="absolute right-3 bottom-2 text-center text-white">Oct 16, 2026</p>
                    </div>
                    <div className="flex h-full flex-col justify-center gap-2 rounded-3xl border border-[#dbe7f2] bg-white px-6 text-text shadow-[0_18px_50px_rgba(26,54,102,0.10)]">
                        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Looking good!</h1>
                        <p className="text-sm leading-6 text-[#607797] sm:text-base">Happy with it? Add your details next and we&apos;ll send the photo to you.</p>
                    </div>
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={3}>
                <Button onClick={onCancel} style="secondary">
                    <X size={30} color="#1A3666"/>
                </Button>
                <Button onClick={onAccept}>
                    <Check size={30} color="#ffffff" />
                </Button>
                <Button onClick={onRetake} style="secondary">
                    <RotateCcw size={30} color="#1A3666"/>
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    );
}