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
                    <div className="aspect-2/3 bg-white rounded-3xl relative max-h-full max-w-full overflow-hidden">
                        <Image src={photo} width={100} height={100} alt="Captured" className="w-full h-full object-contain rounded-3xl" />
                        <Image src="bloom.svg" width={40} height={40} alt="" className="absolute left-2 bottom-2" />
                        <p className="absolute right-3 bottom-2 text-center text-white">Oct 16, 2026</p>
                    </div>
                    <div className="flex flex-col justify-center text-text gap-2 h-full">
                        <h1 className="text-4xl font-bold">Looking Good!</h1>
                        <p className="text-xl">Happy with it? Add your details next and we&apos;ll send the photo to you.</p>
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