import { boothConfig } from "@/libs/booth-config";
import { Aperture } from "lucide-react";
import BoothStructure, { BoothStructureContent, BoothStructureAction } from "../booth-structure";
import Button from "@/components/button";
import Social from "@/components/social";

interface BoothHomeProps {
    onBegin: () => void;
}

export default function BoothHome({ onBegin }: BoothHomeProps) {
    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex h-full w-full items-center justify-center rounded-3xl border border-[#dbe7f2] bg-white p-8 text-text shadow-[0_18px_50px_rgba(26,54,102,0.10)]">
                    <div className="flex max-w-2xl flex-col items-center gap-6 text-center">
                        <div className="flex flex-col gap-3">
                            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[#6b86a8]">Welcome to</span>
                            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">{boothConfig.eventName}</h1>
                            <p className="text-sm leading-6 text-[#607797] sm:text-base">Make a portrait, keep the moment, and have it sent straight to you.</p>
                        </div>
                        <Social />
                    </div>
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