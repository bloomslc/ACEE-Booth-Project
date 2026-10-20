import Image from "next/image";

export default function BoothHeader() {
    return (
        <header className="flex justify-center items-center">
            <Image src="/BloomLetterNo.svg" alt="Logo" width={150} height={100} />
        </header>
    );
}