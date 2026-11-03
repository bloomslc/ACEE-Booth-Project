"use client";

import { useState } from "react";
import Button from "../button";
import Qrcode from "../qrcode";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "./booth-structure";

interface ThankYouProps {
    onBackHome: () => void;
    guest?: {
        name: string;
        email: string;
    };
    sessionId?: string;
}

const socialLinks = [
    { name: "LinkedIn", type: "linkedin" as const, value: "https://www.linkedin.com/company/slcbloom/" },
    { name: "Instagram", type: "instagram" as const, value: "https://www.instagram.com/slcbloom/" },
    { name: "Facebook", type: "facebook" as const, value: "https://www.facebook.com/slcbloom/" },
];

export default function ThankYou({ onBackHome, guest, sessionId }: ThankYouProps) {
    const [selectedSocial, setSelectedSocial] = useState<typeof socialLinks[number]>();

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex flex-col items-center justify-center text-center w-full h-full text-text">
                    <h1 className="text-3xl font-bold mb-4">Thank You {guest?.name || 'Guest'}!</h1>
                    <p className="mb-4">Your photo has been sent to {guest?.email}.</p>
                    <p className="mb-4">We appreciate your participation in the event.</p>
                    {sessionId && <p className="mb-4">Session ID: {sessionId}</p>}
                    <div>
                        <h2>Follow our social media</h2>
                        <div className="grid grid-cols-3 gap-3">
                            {socialLinks.map((social) => (
                                <button
                                    key={social.type}
                                    type="button"
                                    onClick={() => setSelectedSocial(social)}
                                    className="flex flex-col items-center gap-2 rounded-4xl bg-secondary p-5 text-text shadow-sm"
                                >
                                    <img src={`/${social.type}.svg`} width={48} height={48} alt="" aria-hidden="true" />
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={1}>
                <Button onClick={onBackHome}>
                    Back Home
                </Button>
            </BoothStructureAction>
            {selectedSocial && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
                    role="dialog"
                    aria-modal="true"
                    aria-label={`${selectedSocial.name} QR code`}
                    onClick={() => setSelectedSocial(undefined)}
                >
                    <div className="relative rounded-4xl bg-white p-6" onClick={(event) => event.stopPropagation()}>
                        <Qrcode value={selectedSocial.value} type={selectedSocial.type} />
                    </div>
                </div>
            )}
        </BoothStructure>
    );
}