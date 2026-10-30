import type { ReactNode } from "react";
import BoothHeader from "./booth-header";

interface BoothStructureProps {
    children: ReactNode;
}

interface BoothStructureContentProps {
    children: ReactNode;
}

interface BoothStructureActionProps {
    action: 1 | 2 | 3;
    children: ReactNode;
}

export default function BoothStructure({ children }: BoothStructureProps) {
    return (
        <section className="grid h-full w-full max-w-full grid-rows-[1fr_7fr] overflow-hidden px-[5%] py-[4%] lg:aspect-1488/2266 lg:w-auto lg:border">
            <BoothHeader />
            <div className="h-full w-full grid grid-rows-[6fr_1fr] bg-foreground gap-4 rounded-4xl overflow-hidden">
                {children}
            </div>
        </section>
    );
}

export function BoothStructureContent({ children }: BoothStructureContentProps) {
    return (
        <div className={`flex flex-col h-full min-h-0 flex-1 p-4`}>
            {children}
        </div>
    );
}

export function BoothStructureAction({ children, action }: BoothStructureActionProps) {
    const columns =
        action === 1
            ? "grid-cols-1"
            : action === 2
              ? "grid-cols-2"
              : "grid-cols-3";

    return (
        <div className={`grid max-h-full w-full items-center p-4 gap-4 overflow-hidden ${columns}`}>
            {children}
        </div>
    );
}