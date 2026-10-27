ACEE Booth Project
Copyright (C) 2026 Bloom Communication

License: GNU General Public License, version 3 or (at your option) any later version
(SPDX-License-Identifier: GPL-3.0-or-later)

## ACEE Portrait Booth

An operator-controlled portrait booth for a Raspberry Pi and Sony camera. The
operator uses the Next.js web interface on an iPad or computer to preview the
camera, capture and review a photo, collect guest details, and send the approved
image by email through Resend.

The backend keeps Resend credentials and camera access off the browser. Neon
PostgreSQL is optional and records capture sessions, photos, and delivery
results when it is enabled.

## Project structure

```text
backend/
	app/main.py       FastAPI routes and application startup
	app/camera.py     gphoto2 capture and preview adapter
	app/database.py   Optional Neon PostgreSQL persistence
	app/email.py      Resend email delivery
frontend/
	app/              Next.js application shell
	components/booth/ Booth workflow screens
	libs/api.ts       Browser-to-backend API client
```

## Requirements

For development:

- Python 3 with virtual-environment support
- Node.js and npm, or Bun
- A Neon PostgreSQL project, if persistence is enabled

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

For a Resend template, copy [backend/email-template.html](backend/email-template.html)
into a Resend template and set `RESEND_TEMPLATE_ID`. The template receives the
guest name as `{{GUEST_NAME}}`, the public bucket image URL through
`{{PHOTO_IMAGE}}`, and the capture ID through `{{SESSION_ID}}`. Use the image
variable in the template as an image source, for example
`<img src="{{PHOTO_IMAGE}}">`. In template mode the image is referenced from
the bucket URL instead of being attached to the email.
Set `RESEND_TEMPLATE_IMAGE_VARIABLE` if the template uses a different image
variable name. Leave `RESEND_TEMPLATE_ID` empty to use the built-in HTML email.

Start the API in one terminal:

```bash
uvicorn app.main:app --reload --port 8080 --app-dir backend
```

Install and start the frontend in a second terminal:

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_URL=http://localhost:8080 npm run dev
```

Open <http://localhost:3000>. The frontend defaults to
`http://localhost:8080` when `NEXT_PUBLIC_API_URL` is not set.

The frontend scripts are:

```bash
npm run dev
npm run lint
npm run build
npm run start
```

## Development bypass

Set this in `backend/.env`:

```env
DEV_BYPASS=true
DEV_BYPASS_IMAGE=frontend/public/image.jpg
```

With `DEV_BYPASS=true`:

- Preview and capture use the configured local JPEG instead of `gphoto2`.
- Bypass captures are not written to `data/images`; their `local_path` is null.
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

The preview screen requests a fresh frame every 1.5 seconds through the API.
Physical preview uses `gphoto2 --capture-preview`. Capture uses
`gphoto2 --capture-image-and-download`, saves a UUID-named JPEG under
`PHOTO_STORAGE_DIR` (default: `data/images`), and returns the image to the
browser for review. The saved local path is returned as `local_path` and is
stored in Neon with the capture session.

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

The capture response includes `remote_url`, and Neon stores that URL with the
local path. The bucket must allow public reads because this configuration is
intended to provide a public image URL. Keep the access keys only in the
backend environment; never add them to `NEXT_PUBLIC_*` variables.

## Neon persistence

Create a Neon PostgreSQL project and put its pooled or direct connection string
in `backend/.env`:

```env
NEON_DATABASE_URL=postgresql://user:password@ep-example.us-east-2.aws.neon.tech/booth?sslmode=require
```

The API creates these tables on startup:

- `sessions`
- `photos`
- `deliveries`

Leave `NEON_DATABASE_URL` empty to disable Neon, or enable `DEV_BYPASS` to
disable database access automatically during development. The connection must
use SSL, as shown by `sslmode=require`.

## Raspberry Pi deployment

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

The frontend can be served with `npm run build && npm run start`, or hosted
behind the local network's preferred web server. Do not expose the Pi API to
the public internet or forward its port publicly.

## API

All routes use the `/api/v1` prefix.

### `GET /health`

Returns application, email provider, and database status.

### `POST /camera/preview`

Returns a temporary preview as a base64 image data URL. It does not save a
photo. Camera errors return `503`.

### `POST /capture`

Captures and locally saves a photo, then returns:

```json
{
	"status": "captured",
	"image_data_url": "data:image/jpeg;base64,...",
	"session_id": "uuid",
	"local_path": "/path/to/project/data/images/uuid.jpg",
	"remote_url": "https://images.example.com/sessions/uuid/uuid.jpg"
}
```

### `POST /deliveries/email`

Accepts `name`, `email`, `image_data_url`, and an optional `session_id`.
Normal mode sends the image through Resend and returns the provider message ID.
Development bypass mode returns `provider_id: "dev-bypass"` without sending.

## Current limitations

This is an end-to-end booth prototype, not yet a production queueing system.

- Capture creates a session per capture; a separate multi-capture session API is
	not implemented.
- Upload retry workers and offline delivery queues are not implemented.
- Template email delivery depends on a publicly readable bucket URL; the
	attachment-based fallback is used only when no Resend template is configured.
- Neon connectivity is checked at API startup, so an unavailable Neon project
	will prevent the API from starting when `NEON_DATABASE_URL` is configured.
- Captured files remain on local disk indefinitely; there is no retention or
	cleanup job yet.
- Preview polling serializes camera commands through separate `gphoto2` calls;
	benchmark this on the exact Pi and camera hardware.
- Operator authentication, upload retry handling, and systemd service files
	still need to be added before a public event.

## License

Copyright (C) 2026 Bloom Communication.

This project is licensed under the GNU General Public License, version 3 or any
later version. See [LICENSE](LICENSE) for the full license text.
