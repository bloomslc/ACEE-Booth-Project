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
        <section className="grid grid-rows-[1fr_7fr_1fr] gap-4 lg:border aspect-1488/2266 h-screen w-auto overflow-hidden px-19 py-10">
            <BoothHeader />
            {children}
        </section>
    );
}

export function BoothStructureContent({ children }: BoothStructureContentProps) {
    return (
        <div className={`flex flex-col h-full min-h-0 flex-1`}>
            {children}
        </div>
    );
}

export function BoothStructureAction({ children, action }: BoothStructureActionProps) {
    const columns =
        action === 1
            ? "grid-cols-[1fr]"
            : action === 2
              ? "grid-cols-[1fr_4fr]"
              : "grid-cols-[1fr_3fr_1fr]";

    return (
        <div className={`grid min-h-0 min-w-0 w-full items-center gap-4 ${columns}`}>
            {children}
        </div>
    );
}