import Qrcode from "@/components/qrcode";

export default function Home() {
  return (
    <main>
      <div className="flex flex-col items-center justify-center min-h-screen py-2">
        <h1 className="text-4xl font-bold mb-4">ACEE Booth Project</h1>
        <p className="text-lg mb-8">Scan the QR code below to access the project</p>
        <Qrcode value="https://slc.qc.ca/bloom"></Qrcode>
      </div>
    </main>
  );
}
