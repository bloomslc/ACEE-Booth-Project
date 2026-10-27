interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    secondary?: boolean;
    square?: boolean;
    ghost?: boolean;
    classname?: string;
}

export default function Button({ onClick, children, type, secondary, ghost, square, classname, ...props }: ButtonProps) {
    return (
        <button
            {...props}
            onClick={onClick}
            type={type}
            className={`cursor-pointer ${secondary ? 'bg-button-background' : 'bg-red-500'} ${ghost ? 'bg-transparent border border-white' : ''} ${square ? 'aspect-square' : 'aspect-auto'} text-white text-lg rounded-full w-full h-full flex gap-4 justify-center items-center ${classname || ''}`}
        >
            {children}
        </button>
    );
}