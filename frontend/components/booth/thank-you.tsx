"use client";

import Button from "../button";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "./booth-structure";
import Social from "../social";

interface ThankYouProps {
    onBackHome: () => void;
    guest?: {
        name: string;
        email: string;
    };
    sessionId?: string;
}

export default function ThankYou({ onBackHome, guest }: ThankYouProps) {

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex h-full w-full items-center justify-center rounded-3xl border border-[#dbe7f2] bg-white p-8 text-center text-text shadow-[0_18px_50px_rgba(26,54,102,0.10)]">
                    <div className="flex max-w-2xl flex-col items-center gap-5">
                        <div className="flex flex-col gap-2">
                            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[#6b86a8]">All set</span>
                            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Thank you, {guest?.name || 'Guest'}!</h1>
                            <p className="text-sm leading-6 text-[#607797] sm:text-base">Your photo has been sent to {guest?.email}.</p>
                            <p className="text-sm leading-6 text-[#607797] sm:text-base">We appreciate your visit to our booth!</p>
                        </div>
                        <Social />
                    </div>
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={1}>
                <Button onClick={onBackHome}>
                    Back Home
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    );
}