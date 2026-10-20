import { ReactQRCode } from "@lglab/react-qr-code";

interface QrcodeProps {
    value: string;
}

export default function Qrcode( { value }: QrcodeProps ) {

    return (
        <div>
            <ReactQRCode
                finderPatternInnerSettings={{
                    style: 'rounded-lg',
                    color: '#1A3666',
                }}
                finderPatternOuterSettings={{
                    style: 'leaf',
                    color: '#1A3666',
                }}
                imageSettings={{
                    src: '/bloom.svg',
                    width: 35,
                    height: 35,
                    excavate: true,
                    opacity: 1,
                }}
                dataModulesSettings={{
                    style: 'square-sm',
                    color: '#1A3666',
                }}
                size={256}
                value={value}
            />
        </div>
    );
}