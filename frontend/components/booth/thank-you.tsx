import Button from "../button";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "./booth-structure";

interface ThankYouProps {
    onBackHome: () => void;
    guest?: {
        name: string;
        email: string;
    };
    sessionId?: string;
}

export default function ThankYou({ onBackHome, guest, sessionId }: ThankYouProps) {
    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex flex-col items-center justify-center text-center w-full h-full bg-foreground text-text rounded-4xl">
                    <h1 className="text-3xl font-bold mb-4">Thank You {guest?.name || 'Guest'}!</h1>
                    <p className="mb-4">Your photo has been sent to {guest?.email}.</p>
                    <p className="mb-4">We appreciate your participation in the event.</p>
                    {sessionId && <p className="mb-4">Session ID: {sessionId}</p>}
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