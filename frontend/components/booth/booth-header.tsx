import Image from "next/image";

export default function BoothHeader() {
    return (
        <header className="flex justify-center items-center">
            <Image src="/BloomLetterNo.svg" alt="Logo" width={200} height={150} />
        </header>
    );
}