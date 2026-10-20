import { GuestInfo } from "@/libs/booth-config"
import { useState, type FormEvent } from 'react'
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "../booth-structure"
import Button from "@/components/button"
import { X } from "lucide-react"

type GuestFormProps = {
  onSubmit: (info: GuestInfo) => void
  onCancel?: () => void
  afterPhoto?: boolean
    isSending?: boolean
    error?: string | null
}



export default function GuestForm({ onSubmit, onCancel, isSending = false, error }: GuestFormProps) {
    const [name, setName] = useState('')
    const [email, setEmail] = useState('')

    function handleSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault()
        onSubmit({ name: name.trim(), email: email.trim().toLowerCase()})
    }

    return (
        <BoothStructure>
            <BoothStructureContent>
                <div className="flex flex-col justify-end gap-4 w-full h-full">
                    <div>
                        <h1 className="text-4xl font-bold">Who are we sending this to?</h1>
                        <p>Please fill out the form below to proceed.</p>
                    </div>
                    <form
                        id="guest-form"
                        onSubmit={handleSubmit}
                        className="flex flex-col justify-center gap-4 w-full h-auto bg-gray-300 rounded-4xl p-4"
                    >
                        <label htmlFor="name">Name<span className="text-red-500">*</span></label>
                        <input
                            onChange={(e) => setName(e.target.value)}
                            value={name}
                            id="name"
                            required
                            type="text"
                            placeholder="Name"
                            className="rounded-md border px-4 py-2 w-full"
                        />
                        <label htmlFor="email">Email</label>
                        <input
                            onChange={(e) => setEmail(e.target.value)}
                            value={email}
                            id="email"
                            required
                            type="email"
                            placeholder="Email"
                            className="rounded-md border px-4 py-2 w-full"
                        />
                        <span className="text-sm text-gray-500">By submitting this form, you agree to our Terms and Conditions.</span>
                        {error && <span className="text-sm text-red-600">{error}</span>}
                    </form>
                </div>
            </BoothStructureContent>
            <BoothStructureAction action={2}>
                <Button onClick={onCancel} secondary square>
                    <X size={30} color="black"/>
                </Button>
                <Button type="submit" form="guest-form" disabled={isSending}>
                    {isSending ? 'Sending...' : 'Send Photo'}
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    );
}