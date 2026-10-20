interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    secondary?: boolean;
    square?: boolean;
}

export default function Button({ onClick, children, type, secondary, square, ...props }: ButtonProps) {
    return (
        <button
            {...props}
            onClick={onClick}
            type={type}
            className={`cursor-pointer ${secondary ? 'bg-gray-300' : 'bg-red-500'} ${square ? 'aspect-square' : 'aspect-auto'} text-white text-lg rounded-full w-full h-full flex gap-4 justify-center items-center`}
        >
            {children}
        </button>
    );
}