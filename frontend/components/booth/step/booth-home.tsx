import Qrcode from "@/components/qrcode";
import { Aperture } from "lucide-react";
import BoothStructure, { BoothStructureContent, BoothStructureAction } from "../booth-structure";
import Button from "@/components/button";

interface BoothHomeProps {
    onBegin: () => void;
}

export default function BoothHome({ onBegin }: BoothHomeProps) {
    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex flex-col items-center justify-center w-full h-full text-text">
                    <h1 className="text-4xl font-bold mb-4">Photo Booth</h1>
                    <p className="text-lg mb-8">Scan the QR code below to access our website</p>
                    <Qrcode value="https://slc.qc.ca/bloom" type="bloom" />
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={1}>
                <Button onClick={onBegin}>
                    <Aperture size={30} />
                    <span>Start Shooting</span>
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    )
}