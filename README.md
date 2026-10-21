ACEE Booth Project
Copyright (C) 2026 Bloom Communication

License: GNU General Public License, version 3 or (at your option) any later version
(SPDX-License-Identifier: GPL-3.0-or-later)

The ACEE Booth Project is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

The project is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

A copy of the GNU General Public License is included in the file named LICENSE.
You can also read it at:
https://www.gnu.org/licenses/gpl-3.0.html

This project-specific notice identifies the copyright holder and license for
ACEE Booth Project.

## Email delivery

The booth sends approved photos through the FastAPI backend and Resend. The
Resend API key stays on the backend and is never exposed to the browser.

1. Copy `backend/.env.example` to `backend/.env` and set `RESEND_API_KEY` and
	`RESEND_FROM_EMAIL` using a verified Resend domain.
2. Install dependencies with `python -m pip install -r backend/requirements.txt`.
3. Start the API from the repository root with
	`uvicorn app.main:app --reload --port 8080 --app-dir backend`.
4. Set `NEXT_PUBLIC_API_URL=http://localhost:8080` for the frontend when the
	API is not served from the same origin.

The email endpoint is `POST /api/v1/deliveries/email`. It accepts `name`,
`email`, and an optional base64 image data URL as `image_data_url`.

## Camera capture

The capture screen calls `POST /api/v1/capture`. On the Raspberry Pi, install
`gphoto2`, connect the Sony camera in PC Remote mode, and set `PHOTO_STORAGE_DIR`
to the local directory where captured JPEGs should be retained. The endpoint
returns the locally saved photo to the browser for review; approved photos are
then sent through Resend.

## MySQL persistence

For the easiest desktop setup, install Docker Desktop, copy the MySQL values
from `backend/.env.example`, and start the database from the repository root:

```bash
docker compose up -d mysql
```

The database is available at `127.0.0.1:3306` and persists in the
`mysql_data` Docker volume. The API creates its tables automatically on startup.

### Raspberry Pi

Use Raspberry Pi OS 64-bit and install Docker Engine and the Compose plugin.
From the project directory on the Pi, start the database with:

```bash
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d mysql
```

This stores MySQL files in `data/mysql`, so they remain on the Pi even if the
container is recreated. Keep `MYSQL_HOST=127.0.0.1` in the Pi's
`backend/.env` because the FastAPI process connects through the published local
port. Back up `data/mysql` or use `mysqldump` before changing storage devices.

For a manually installed MySQL server, create the database and user instead:

```sql
CREATE DATABASE portrait_booth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'portrait_booth'@'localhost' IDENTIFIED BY 'change-this-password';
GRANT ALL PRIVILEGES ON portrait_booth.* TO 'portrait_booth'@'localhost';
FLUSH PRIVILEGES;
```

When `MYSQL_HOST` is set, the API creates the `sessions`, `photos`, and
`deliveries` tables on startup. Captures and successful Resend deliveries are
then linked by `session_id`. Leave `MYSQL_HOST` empty to run without MySQL.

For local development without a connected camera or Resend credentials, set
`DEV_BYPASS=true` and optionally point `CAMERA_BYPASS_IMAGE` at a JPEG. This
uses the image for preview/capture and skips the Resend request while returning
a successful development response. Leave it set to `false` for the event.
