"use client";

import { Settings } from "lucide-react";
import { useState, type FormEvent } from "react";
import {
    checkServer,
    defaultApiUrl,
    getApiUrl,
    normalizeServerAddress,
    resetApiUrl,
    saveApiUrl,
} from "@/libs/server-settings";

type Status = { kind: 'ok' | 'error'; message: string } | null

export default function ServerSettings() {
    const [isOpen, setIsOpen] = useState(false)
    const [address, setAddress] = useState('')
    const [isTesting, setIsTesting] = useState(false)
    const [status, setStatus] = useState<Status>(null)

    function open() {
        setAddress(getApiUrl())
        setStatus(null)
        setIsOpen(true)
    }

    async function handleSave(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        const url = normalizeServerAddress(address)
        if (!url) {
            setStatus({ kind: 'error', message: 'Enter a valid IP address or host name.' })
            return
        }

        setIsTesting(true)
        setStatus(null)
        const isReachable = await checkServer(url)
        setIsTesting(false)

        saveApiUrl(url)
        setAddress(url)
        setStatus(
            isReachable
                ? { kind: 'ok', message: `Connected. Saved ${url}.` }
                : {
                      kind: 'error',
                      message: `Saved ${url}, but the browser could not read a response. Check the address and that FRONTEND_ORIGIN on the server is empty or includes this page's address.`,
                  },
        )
    }

    function handleReset() {
        resetApiUrl()
        setAddress(defaultApiUrl)
        setStatus({ kind: 'ok', message: `Reset to ${defaultApiUrl}.` })
    }

    return (
        <>
            <button
                type="button"
                aria-label="Server settings"
                onClick={open}
                className="absolute right-4 top-4 cursor-pointer rounded-full p-2 text-[#7892b2] transition-colors hover:bg-[#f2f7fc] hover:text-text"
            >
                <Settings size={24} aria-hidden="true" />
            </button>
            {isOpen && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
                    role="dialog"
                    aria-modal="true"
                    aria-label="Server settings"
                    onClick={() => setIsOpen(false)}
                >
                    <form
                        onSubmit={(event) => void handleSave(event)}
                        onClick={(event) => event.stopPropagation()}
                        className="flex w-full max-w-md flex-col gap-4 rounded-4xl bg-white p-6 text-left text-text"
                    >
                        <h2 className="text-2xl font-bold">Server settings</h2>
                        <div className="flex flex-col gap-2">
                            <label htmlFor="server-address" className="text-sm font-semibold">Server IP address</label>
                            <input
                                id="server-address"
                                value={address}
                                onChange={(event) => setAddress(event.target.value)}
                                type="text"
                                inputMode="url"
                                autoCapitalize="none"
                                autoCorrect="off"
                                spellCheck={false}
                                placeholder="10.1.87.237"
                                className="w-full rounded-2xl border border-[#cbdbea] bg-[#f7faff] px-4 py-3 text-base outline-none focus:border-[#5d9bd1] focus:ring-4 focus:ring-[#90c3f1]/30"
                            />
                            <p className="text-xs text-[#607797]">Port 8080 is used unless you add one, for example 10.1.87.237:9000.</p>
                        </div>
                        {status && (
                            <p
                                role="status"
                                className={`rounded-2xl px-4 py-3 text-sm ${status.kind === 'ok' ? 'bg-[#f2f7fc] text-text' : 'border border-red-200 bg-red-50 text-red-700'}`}
                            >
                                {status.message}
                            </p>
                        )}
                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={handleReset}
                                className="cursor-pointer rounded-4xl bg-button-background px-5 py-3 text-white"
                            >
                                Reset
                            </button>
                            <button
                                type="submit"
                                disabled={isTesting}
                                className="flex-1 cursor-pointer rounded-4xl bg-red-500 px-5 py-3 text-white disabled:opacity-40"
                            >
                                {isTesting ? 'Testing...' : 'Save and test'}
                            </button>
                            <button
                                type="button"
                                onClick={() => setIsOpen(false)}
                                className="cursor-pointer rounded-4xl px-3 py-3 text-text"
                            >
                                Close
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </>
    )
}
