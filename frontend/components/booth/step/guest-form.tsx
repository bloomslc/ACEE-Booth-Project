import type { GuestInfo } from "@/libs/booth-config"
import { useState, type FormEvent } from 'react'
import BoothStructure, { BoothStructureAction, BoothStructureContent } from "../booth-structure"
import Button from "@/components/button"
import { Mail, UserRound, X } from "lucide-react"

type GuestFormProps = {
  onSubmit: (info: GuestInfo) => void
  onCancel?: () => void
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
                <form
                    id="guest-form"
                    onSubmit={handleSubmit}
                    className="flex min-h-0 w-full flex-1 flex-col justify-between gap-5 overflow-y-auto rounded-3xl border border-[#dbe7f2] bg-white p-6 text-text shadow-[0_18px_50px_rgba(26,54,102,0.10)]"
                >
                    <div className="flex flex-col gap-2">
                        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Where should we send it?</h1>
                        <p className="max-w-lg text-sm leading-6 text-[#607797] sm:text-base">Add your details and we&apos;ll send your portrait straight to your inbox.</p>
                    </div>

                    <div className="flex flex-col gap-4">
                        <div className="flex flex-col gap-2">
                            <label htmlFor="name" className="text-sm font-semibold">Name <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <UserRound aria-hidden="true" size={19} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#7892b2]" />
                                <input
                                    onChange={(e) => setName(e.target.value)}
                                    value={name}
                                    id="name"
                                    required
                                    type="text"
                                    autoComplete="name"
                                    placeholder="Your name"
                                    className="w-full rounded-2xl border border-[#cbdbea] bg-[#f7faff] px-4 py-3 pl-12 text-base outline-none transition-colors placeholder:text-[#91a4bc] focus:border-[#5d9bd1] focus:ring-4 focus:ring-[#90c3f1]/30"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label htmlFor="email" className="text-sm font-semibold">Email <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <Mail aria-hidden="true" size={19} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#7892b2]" />
                                <input
                                    onChange={(e) => setEmail(e.target.value)}
                                    value={email}
                                    id="email"
                                    required
                                    type="email"
                                    autoComplete="email"
                                    placeholder="you@example.com"
                                    className="w-full rounded-2xl border border-[#cbdbea] bg-[#f7faff] px-4 py-3 pl-12 text-base outline-none transition-colors placeholder:text-[#91a4bc] focus:border-[#5d9bd1] focus:ring-4 focus:ring-[#90c3f1]/30"
                                />
                            </div>
                        </div>
                    </div>

                    <p className="rounded-2xl bg-[#f2f7fc] px-4 py-3 text-xs leading-5 text-[#6a7f9b]">By submitting this form, you agree to allow Bloom to keep your name and email for the duration of the event or 48 hours, which is the time frame in which your photo will be available for download. This data will be used to send you your photo.</p>
                    {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
                </form>
            </BoothStructureContent>
            <BoothStructureAction action={2}>
                <Button onClick={onCancel} style="secondary">
                    <X size={25} color="#1A3666" aria-hidden="true"/>
                </Button>
                <Button type="submit" form="guest-form" disabled={isSending}>
                    {isSending ? 'Sending...' : 'Send photo'}
                </Button>
            </BoothStructureAction>
        </BoothStructure>
    );
}