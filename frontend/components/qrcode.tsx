import QRCode from "react-qr-code";
import type { ComponentType } from "react";

interface QrcodeProps {
    value: string;
}

export default function Qrcode( { value }: QrcodeProps ) {
    const QRCodeComponent = QRCode as unknown as ComponentType<QrcodeProps>;

    return (
        <div>
            <QRCodeComponent value={value} />
        </div>
    );
}