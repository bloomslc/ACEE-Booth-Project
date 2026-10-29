interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "style"> {
    children: React.ReactNode;
    style?: "secondary" | "ghost" | "default";
    classname?: string;
    type?: "button" | "submit" | "reset";
    onClick?: () => void;
}

export default function Button({ onClick, children, type, style, classname, ...props }: ButtonProps) {
    const Style =
        style === "secondary"
            ? "bg-button-background text-white"
            : style === "ghost"
              ? "bg-transparent text-text"
              : "bg-red-500 text-white";

    return (
        <button
            {...props}
            onClick={onClick}
            type={type}
            className={`cursor-pointer ${Style} text-lg rounded-4xl w-auto h-full flex gap-4 justify-center items-center ${classname || ''}`}
        >
            {children}
        </button>
    );
}