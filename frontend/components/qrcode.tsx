import { ReactQRCode } from "@lglab/react-qr-code";

interface QrcodeProps {
    value: string;
}

export default function Qrcode( { value }: QrcodeProps ) {

    return (
        <div>
            <ReactQRCode
                finderPatternInnerSettings={{
                    color: '#1A3666',
                }}
                finderPatternOuterSettings={{
                    color: '#1A3666',
                }}
                imageSettings={{
                    src: '/bloom.svg',
                    width: 30,
                    height: 30,
                    excavate: true,
                    opacity: 1,
                }}
                dataModulesSettings={{
                    color: '#1A3666',
                }}
                size={250}
                value={value}
            />
        </div>
    );
}