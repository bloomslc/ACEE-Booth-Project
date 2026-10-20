import Image from "next/image";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "../booth-structure";
import Button from "@/components/button";
import { X, RotateCcw } from "lucide-react";

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
                <div className="aspect-1034/1142 p-3 w-full bg-[#1A3666] rounded-4xl grid grid-cols-[1fr_auto]">
                    <div className="aspect-2/3 bg-white rounded-3xl">
                        <Image src="/image.jpg" width={100} height={100} alt="Captured" className="w-full h-full object-contain rounded-3xl" />
                    </div>
                    <div className="flex flex-col justify-between items-end">
                        <p className="text-center text-white -rotate-90 whitespace-nowrap">Oct 16, 2026</p>
                        <Image src="bloom.svg" width={50} height={50} alt="" />
                    </div>
                </div>
                <div className="flex flex-col justify-center gap-2 h-full">
                    <h1 className="text-4xl font-bold">Looking Good!</h1>
                    <p className="text-xl">Happy with it? Add your details next and we'll send the photo to you.</p>
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={3}>
                <Button onClick={onCancel} secondary square>
                    <X size={30} color="black"/>
                </Button>
                <Button onClick={onAccept}>
                    Use This Photo
                </Button>
                <Button onClick={onRetake} secondary square>
                    <RotateCcw size={30} color="black"/>
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    );
}