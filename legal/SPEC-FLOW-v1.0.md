# Flow Deliverable Specification v1.0 (Annex to SALE-v1.0)

1. Overview and purpose
- Deliverable: A Chrome-compatible browser extension (“Flow”) packaged as an obfuscated JavaScript build (no un‑obfuscated source).
- Purpose: Automate user flows across specific web pages, monitor inbox states, open relevant product links, and perform image-based processing via the TRC backend API.
- Primary domains and contexts:
  - Microsoft Outlook Web: https://outlook.office.com/mail/* (and mcas mirror)
  - HanseMerkur auction site pages:
    - Item page: https://auktion.hansemerkur.de/item.php (and localhost dev variant)
    - Buy-now page: https://auktion.hansemerkur.de/buy_now/id/* (and localhost dev variant)
    - My message center (message): https://auktion.hansemerkur.de/my_message_center_show_message.php (and localhost dev variant)
    - My message center (inbox): https://auktion.hansemerkur.de/my_message_center_inbox.html (and localhost dev variant)

2. Architecture and components
- Background service worker: background.js
  - Receives messages from content scripts and orchestrates actions.
  - Manages tab lifecycle (open/close/reload), flow state, and buying-state coordination.
  - Provides an image processing command that calls the TRC backend.
- Content scripts (compiled as IIFE bundles):
  - email.iife.js, inbox.iife.js, item.iife.js, buyOffer.iife.js, myOffer.iife.js
  - Deployed per manifest matches (see section 1).
  - Detect page state, extract IDs/metadata, send commands to background.
- Popup UI: popup/index.html (user view and quick controls).
- Options page: options/index.html (configuration screen, token input, feature toggles).
- Shared packages: configuration, logging, utilities, i18n, storage, and types used across modules.

3. Configuration
- Backend base URL (build-time): set via env var CEB_TRC_BACKEND_URL; required for production builds.
- API token (runtime): stored in extension local storage via the Options page.
- Core toggles and timings (runtime, managed in Options):
  - emailMode (on/off), inboxMode (on/off)
  - inboxReloadSeconds, inboxPostReloadDelayMs, inboxMaxLinksPerScan, inboxInterOpenDelayMs
  - operationalHours per day (enabled/min/max)
  - product strategy flags and timers (animals, cancer, people)
- Storage: Chrome extension local storage (keyed state with live updates). No server-side storage.

4. Backend API integration
- Endpoint: POST {CEB_TRC_BACKEND_URL}/api/core/solve
- Authentication: Authorization: Bearer <token>
  - Tokens are created and managed via /api/customers/tokens (server-side; not part of the extension).
  - User must have accepted terms and verified email for tokens to be valid.
- Request (multipart/form-data):
  - file: image binary (PNG/JPEG) converted from base64 by the extension
  - flow_id: string identifier for the current flow (used for result caching and attribution)
- Successful response (HTTP 200, JSON):
  - {
    "request_id": string,
    "result": string,    // solver output
    "duration_ms": number
  }
- Error responses:
  - 400: missing/invalid input
  - 401: missing/invalid token
  - 500: solver/internal error (body includes { detail, code })
- Notes:
  - The backend may return cached results when flow_id matches a prior solve.
  - The extension must treat non-2xx as errors and surface messages in logs.

5. Functional behavior (high level)
- Email route (Outlook):
  - Scan unread emails as configured, open target links that lead to item or buy-now pages.
- Inbox route (HanseMerkur):
  - Periodically reload and scan the inbox page for relevant messages/links up to configured limits.
- Item route:
  - Extract product information (e.g., insured type/age) and expose to the flow for decision-making.
- Buy-now route:
  - Execute the “buy offer” workflow (injector/executor model) with configured timeout and telemetry.
- My message center (message):
  - Navigate to and open product link(s) as needed.
- Image solving:
  - When content requires image processing (e.g., captcha/visual recognition), sendBase64 image to background;
  - Background converts to Blob, POSTs to /api/core/solve with flow_id; on success returns { result } to content script.

6. Security and privacy
- API tokens are stored locally in the extension using Chrome storage and read by background when sending API requests.
- The extension uses a background script to avoid CORS issues for API calls.
- Host permissions are broad (“<all_urls>”) to ensure operation across required pages; matches are constrained in content scripts.
- No personal data is transmitted to the backend except what is embedded in the images or logs intentionally sent by the user flows.

7. Packaging and delivery
- Build process: pnpm build (requires Node >= 22.x; uses Vite + Turbo repo tooling).
- Required env: CEB_TRC_BACKEND_URL must be defined at build time for production bundles.
- Output: zipped extension bundle via pnpm zip suitable for manual installation or store upload.
- Obfuscation: All shipped JS is minified/obfuscated as part of the production build; no un‑obfuscated source or toolchain is delivered.

8. Acceptance criteria
- Installation: The extension can be loaded in Chrome and displays the Options and Popup pages.
- Configuration: User can set API token in Options; status is persisted.
- Domain matching: Content scripts load only on the specified URLs in section 1.
- Flow start/track: Starting a flow (email or inbox) creates a flow record; flows can be marked done/failed; tab management is consistent (open, close, cleanup).
- API call: For a valid token and backend URL, background POSTs to /api/core/solve with (file, flow_id), receives a JSON response containing result, and returns it to the content originator.
- Error handling: Non-2xx responses or network errors are captured and surfaced in logs without crashing the extension.
- Performance: Default polling/reload intervals and link limits are respected; no excessive tab churn; background logs remain responsive.

9. Non-functional requirements
- Browser: Chrome (MV3 service worker). Firefox build targeted by scripts but out-of-scope unless explicitly requested.
- Resilience: Avoids blocking UI; retries/backoff for transient failures where implemented; respects configured operational hours.
- Observability: Background logger available; telemetry events emitted to console (can be adapted to external sinks in future).

10. Out of scope
- Store submission, signing, or deployment to extension marketplaces.
- Server-side token issuance or web portal workflows.
- Custom captchas or third-party site changes not reflected in manifests/selectors.

11. References
- Flow diagrams: flow/diagrams/*.puml (email_flow, inbox_flow, overview)
- Manifest and content registrations: flow/chrome-extension/manifest.ts
- Background entry: flow/chrome-extension/src/background/index.ts (processImageAPI, tab and flow handlers)
- Configuration storage defaults: flow/packages/storage/lib/impl/extension-config-storage.ts
- Types and commands: flow/packages/types/lib/app/types.ts
- Backend endpoints: backend/core/urls.py (/api/core/solve), backend/customers/urls.py (tokens, usage), backend/README.md (API usage)
