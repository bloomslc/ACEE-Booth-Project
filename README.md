ACEE Booth Project
Copyright (C) 2026 Bloom Communication

License: GNU General Public License, version 3 or (at your option) any later version
(SPDX-License-Identifier: GPL-3.0-or-later)

## ACEE Portrait Booth

An operator-controlled portrait booth for a Raspberry Pi and Sony camera. The
operator uses the Next.js web interface on an iPad or computer to preview the
camera, capture and review a photo, collect guest details, and send the approved
image by email through Resend.

The backend keeps Resend, S3, and database credentials and camera access off
the browser. Captures are watermarked, saved locally, and optionally uploaded to
an S3-compatible bucket. Neon PostgreSQL is optional and records capture
sessions, photos, and delivery results when it is enabled.

## Booth workflow

1. **Home** – the guest or operator starts a session.
2. **Camera** – live preview from the camera; tap the shutter to capture.
3. **Review** – accept the photo or retake it.
4. **Guest details** – enter a name and email address and send the photo.
5. **Thank you** – confirmation with Bloom social links and QR codes, then back
   to home for the next guest.

## Project structure

```text
backend/
	app/main.py       FastAPI routes and application startup
	app/camera.py     gphoto2 capture, shared preview stream, and watermarking
	app/auth.py       Booth token check for protected routes
	app/config.py     Shared environment and path helpers
	app/storage.py    S3-compatible image upload
	app/database.py   Optional Neon PostgreSQL persistence
	app/email.py      Resend email delivery
	watermark.png     Default watermark applied to captures
	tests/            pytest suite (see Testing)
deploy/systemd/     systemd units for the API and frontend
data/images/        Local capture storage (default PHOTO_STORAGE_DIR)
frontend/
	app/              Next.js application shell
	components/booth/ Booth workflow screens (step/ holds each stage)
	components/       Shared UI (button, social links, QR code)
	libs/api.ts       Browser-to-backend API client
	libs/booth-config.ts  Event name, countdown, and social links
	public/           Logos, social icons, and the bypass image
run.sh              Start the API for LAN access during development
setup-pi.sh         Interactive Raspberry Pi setup and run helper
```

## Requirements

For development:

- Python 3 with virtual-environment support
- [Bun](https://bun.sh) (the frontend uses `bun.lock`)
- A Neon PostgreSQL project, if persistence is enabled
- An S3-compatible bucket, if remote image URLs are enabled

For physical booth operation:

- Raspberry Pi OS 64-bit
- Sony camera configured for USB PC Remote mode
- `gphoto2` and libgphoto2 installed on the Pi
- A verified Resend sender domain

## Development setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Set the Resend values in `backend/.env` for real delivery. For development
without a camera, use the bypass configuration described below.

### Environment variables (`backend/.env`)

| Variable | Purpose |
| --- | --- |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Resend credentials and verified sender (required for delivery) |
| `RESEND_TEMPLATE_ID` | Optional Resend template; empty uses the built-in HTML email |
| `RESEND_TEMPLATE_IMAGE_VARIABLE` | Template variable that receives the image URL (default `PHOTO_IMAGE`) |
| `BOOTH_API_TOKEN` | Shared token required on capture, preview, and email requests (empty disables auth) |
| `FRONTEND_ORIGIN` | Optional comma-separated CORS origins (empty allows any origin) |
| `PHOTO_STORAGE_DIR` | Capture directory (default `data/images`) |
| `WATERMARK_IMAGE_PATH` | Watermark PNG (default `backend/watermark.png`) |
| `DEV_BYPASS`, `DEV_BYPASS_IMAGE` | Camera-free development mode and its image |
| `NEON_DATABASE_URL` | Optional PostgreSQL connection string |
| `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, `S3_PUBLIC_BASE_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Optional image bucket |

Relative paths are resolved from the repository root.

### Booth token

CORS allows any origin by default, so access control is the `BOOTH_API_TOKEN`
shared secret. When it is set, `POST /capture`, `GET /camera/preview`, and
`POST /deliveries/email` require it as an `X-Booth-Token` header (or a `token`
query parameter, which the preview `<img>` uses). Set the same value as
`NEXT_PUBLIC_API_TOKEN` in the frontend environment and rebuild. Because
`NEXT_PUBLIC_*` values ship in the browser bundle, this keeps stray devices and
other websites off the API but is not a per-user login. `/health` and the
public `/images/` files stay open.

The email endpoint also accepts only `image_url` values that point at this
API's `/images/` or `S3_PUBLIC_BASE_URL`.

### Email template

To use a Resend template, create one in Resend and set `RESEND_TEMPLATE_ID`. The
template receives the guest name as `{{GUEST_NAME}}`, the image URL through
`{{PHOTO_IMAGE}}`, and the capture ID through `{{SESSION_ID}}`. Use the image
variable as an image source, for example `<img src="{{PHOTO_IMAGE}}">`. Template
mode requires a `session_id` and an `image_url` that the recipient's mail client
can reach, so use a public bucket URL. Set `RESEND_TEMPLATE_IMAGE_VARIABLE` if
the template uses a different variable name.

Without a template, the built-in email is a short greeting and does not include
the photo. Use a template for real events.

Start the API in one terminal:

```bash
uvicorn app.main:app --reload --port 8080 --app-dir backend
```

Install and start the frontend in a second terminal:

```bash
cd frontend
bun install
NEXT_PUBLIC_API_URL=http://localhost:8080 bun run dev
```

Open <http://localhost:3000>. The frontend defaults to
`http://localhost:8080` when `NEXT_PUBLIC_API_URL` is not set. To point a
browser or iPad at a different server without rebuilding, tap the gear icon on
the home screen and enter the server's IP address (port 8080 is assumed unless
you add one). The setting is saved in that browser, **Save and test** checks
`/api/v1/health`, and **Reset** returns to `NEXT_PUBLIC_API_URL`. `run.sh` starts
the API with `--host 0.0.0.0` so other devices on the LAN can reach it.

The frontend scripts are:

```bash
bun run dev
bun run lint
bun run build
bun run start
```

## Testing

```bash
python -m pip install -r backend/requirements-dev.txt
cd backend
python -m pytest
ruff check .
```

The tests cover email payloads, token auth, URL handling, capture cleanup,
watermarking, and the shared preview stream.

## Development bypass

Set this in `backend/.env`:

```env
DEV_BYPASS=true
DEV_BYPASS_IMAGE=frontend/public/image.jpg
```

With `DEV_BYPASS=true`:

- Preview and capture use the configured local JPEG instead of `gphoto2`.
- Bypass captures are not written to `data/images`; their `local_path` is null
	and `image_url` points to `/api/v1/dev-bypass-image`.
- Resend is not called; delivery returns `status: "skipped"`.
- Neon startup, reads, and writes are disabled even if `NEON_DATABASE_URL` is set.

Set `DEV_BYPASS=false` for physical camera and email testing.

To bypass the backend entirely from the browser, create `frontend/.env.local`
with:

```env
NEXT_PUBLIC_DEV_BYPASS=true
```

This uses `frontend/public/image.jpg`, creates a browser-side session UUID, and
skips preview, capture, database, bucket, and email API requests. Restart the
Next.js dev server after changing this value.

## Camera operation

The preview screen displays a continuous MJPEG stream from
`/api/v1/camera/preview`, built from repeated `gphoto2 --capture-preview
--stdout` calls. One shared loop feeds every connected preview client, runs only
while someone is watching, and stops after three consecutive camera failures.
Starting a capture stops the active preview process. Capture uses
`gphoto2 --capture-image-and-download`, saves a UUID-named JPEG under
`PHOTO_STORAGE_DIR` (default: `data/images`), and returns the image to the
browser as an HTTP URL for review. The API serves local captures at
`/images/<filename>.jpg`, and builds the image URL from the server address the
client connected to (the one set in the client's server settings). The saved
local path is returned as `local_path` and is stored in Neon with the capture
session. Captured JPEGs are corrected for EXIF orientation, rotated to
portrait if landscape, and receive the lower-left `backend/watermark.png`
watermark (about a quarter of the image width) before they are stored or
uploaded. Set `WATERMARK_IMAGE_PATH` to use a different PNG watermark.

The camera adapter times out preview after 15 seconds and capture after 60
seconds. A missing camera, failed command, timeout, or missing output file is
returned as an HTTP `503` error.

Before an event, verify the exact camera and Pi combination:

```bash
gphoto2 --version
gphoto2 --auto-detect
gphoto2 --capture-image-and-download
```

## Image bucket

Set the S3-compatible bucket variables in `backend/.env` to upload each real
capture after it is saved locally:

```env
S3_BUCKET=portrait-booth-images
S3_REGION=us-east-1
S3_ENDPOINT_URL=
S3_PUBLIC_BASE_URL=https://images.example.com
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
```

`S3_ENDPOINT_URL` is optional for AWS S3 and should be set for providers such
as Cloudflare R2. `S3_PUBLIC_BASE_URL` should be the public base URL for the
bucket or its custom domain. The object key is:

```text
sessions/<session-id>/<filename>.jpg
```

The capture response includes `remote_url`, which becomes the `image_url` used
for review and email. Neon stores that URL with the local path. If the upload
fails, capture returns `502`. If the database write fails after an upload, the
uploaded object and local file are deleted and capture returns `503`. The bucket must allow public reads because this configuration is
intended to provide a public image URL. Keep the access keys only in the
backend environment; never add them to `NEXT_PUBLIC_*` variables.

## Neon persistence

Create a Neon PostgreSQL project and put its pooled or direct connection string
in `backend/.env`:

```env
NEON_DATABASE_URL=postgresql://user:password@ep-example.us-east-2.aws.neon.tech/booth?sslmode=require
```

The API creates these tables on startup:

- `sessions` (status moves from `created` to `captured` to `delivered`)
- `photos`
- `deliveries`

Leave `NEON_DATABASE_URL` empty to disable Neon, or enable `DEV_BYPASS` to
disable database access automatically during development. The connection must
use SSL, as shown by `sslmode=require`.

## Raspberry Pi deployment

### Setup script

[setup-pi.sh](setup-pi.sh) is an interactive helper that clones or updates the
repository, creates `.venv`, installs backend and frontend dependencies (it
installs Bun if missing), and builds the frontend. It can also launch the
backend and frontend in separate terminal windows. It copies
`.env.frontend` and `.env.backend` from `ENV_DIR` (default
`/home/bloomslc/env`) into `frontend/.env` and `backend/.env`, so create those
files first.

```bash
bash setup-pi.sh [install-dir]
```

The run option binds the API to `0.0.0.0` on port 8080, so any device on the
Pi's network can reach it. Use the Pi's address in the client's server
settings (gear icon on the home screen).

### Manual setup

Use Raspberry Pi OS 64-bit, install `gphoto2`, and give the Pi outbound HTTPS
access to Neon. Install the backend dependencies in the Pi virtual environment
and start the API from the repository root:

```bash
sudo apt update
sudo apt install -y gphoto2 python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir backend
```

The frontend can be served with `bun run build && bun run start`, or hosted
behind the local network's preferred web server. Do not expose the Pi API to
the public internet or forward its port publicly.

### Start on boot (systemd)

[deploy/systemd/](deploy/systemd) contains `acee-backend.service` and
`acee-frontend.service`. They assume user `bloomslc`, the repository at
`/home/bloomslc/ACEE-Booth-Project`, and Bun at `/home/bloomslc/.bun/bin/bun`
(the layout `setup-pi.sh` creates); edit those paths if yours differ. Run the
setup script first so the virtual environment, environment files, and frontend
build exist, then:

```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now acee-backend acee-frontend
journalctl -u acee-backend -f
```

The service user needs permission to use the camera USB device.

## API

All routes use the `/api/v1` prefix. Routes marked **token** require
`BOOTH_API_TOKEN` when it is configured.

### `GET /health`

Returns application, email provider, database, `dev_bypass`, and
`image_storage` (`s3` or `local`) status.

### `GET /dev-bypass-image`

Serves the configured bypass image. Returns `404` unless `DEV_BYPASS` is on.

### `GET /camera/preview` (token)

Returns a continuous multipart JPEG preview stream using
`gphoto2 --capture-preview --stdout`. It does not save a photo. The browser
closes this request before starting a capture. Camera errors return `503`.

### `POST /capture` (token)

Captures and locally saves a photo, uploads it to the bucket when configured
(`502` on failure), records it in Neon when enabled (`503` on failure), then
returns:

```json
{
	"status": "captured",
	"image_url": "http://raspberrypi.local:8080/images/uuid.jpg",
	"session_id": "uuid",
	"local_path": "/path/to/project/data/images/uuid.jpg",
	"remote_url": "https://images.example.com/sessions/uuid/uuid.jpg"
}
```

### `POST /deliveries/email` (token)

Accepts `name`, `email`, `image_url`, and an optional `session_id`. A foreign
`image_url` returns `400`, and Resend rejections return `502`. Normal mode sends the image through Resend and returns the provider message ID.
Development bypass mode returns `provider_id: "dev-bypass"` without sending.

## Current limitations

This is an end-to-end booth prototype, not yet a production queueing system.

- Capture creates a session per capture; a separate multi-capture session API is
	not implemented.
- Upload retry workers and offline delivery queues are not implemented.
- The built-in (non-template) email does not include the photo; use a Resend
	template with a publicly reachable image URL.
- Neon connectivity is checked at API startup, so an unavailable Neon project
	will prevent the API from starting when `NEON_DATABASE_URL` is configured.
- Captured files remain on local disk and in the bucket indefinitely; there is
	no retention or cleanup job, even though the guest form promises data is kept
	for the event or 48 hours.
- The preview stream runs a separate `gphoto2` call per frame; benchmark this on
	the exact Pi and camera hardware.
- Authentication is a single shared booth token, not per-operator accounts.

## License

Copyright (C) 2026 Bloom Communication.

This project is licensed under the GNU General Public License, version 3 or any
later version. See [LICENSE](LICENSE) for the full license text.
