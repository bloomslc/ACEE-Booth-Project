# ACEE Portrait Booth frontend

Next.js interface for the portrait booth. It talks to the FastAPI backend in
[`../backend`](../backend); setup, environment variables, and deployment are
documented in the [root README](../README.md).

This project uses Bun.

```bash
bun install
bun run dev      # http://localhost:3000
bun run lint
bun run build
bun run start
```

## Environment

Copy `.env.example` to `.env.local`:

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend URL (default `http://localhost:8080`) |
| `NEXT_PUBLIC_API_TOKEN` | Booth token sent to the backend; must match `BOOTH_API_TOKEN` |
| `NEXT_PUBLIC_IMAGE_URLS` | Optional comma-separated extra image origins, such as the bucket URL |
| `NEXT_PUBLIC_DEV_BYPASS` | `true` skips every backend request and uses `public/image.jpg` |

The gear icon on the home screen sets the server address per browser and
overrides `NEXT_PUBLIC_API_URL` until it is reset.

`NEXT_PUBLIC_*` values are embedded in the browser bundle, so rebuild after
changing them.

## Layout

- `app/` – application shell
- `components/booth/` – workflow container; `step/` holds each screen
- `components/` – shared UI (button, social links, QR code)
- `libs/api.ts` – backend client
- `libs/booth-config.ts` – event name and social links
