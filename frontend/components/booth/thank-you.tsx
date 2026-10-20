import Button from "../button";
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "./booth-structure";

interface ThankYouProps {
    onBackHome: () => void;
    guest?: {
        name: string;
        email: string;
    };
}

export default function ThankYou({ onBackHome, guest }: ThankYouProps) {
    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex flex-col items-center justify-center w-full h-full bg-gray-300 rounded-4xl">
                    <h1 className="text-3xl font-bold mb-4">Thank You {guest?.name || 'Guest'}!</h1>
                    <p className="mb-4">Your photo has been sent to {guest?.email}.</p>
                    <p className="mb-4">We appreciate your participation in the event.</p>
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