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
