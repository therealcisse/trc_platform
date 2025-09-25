# Flow Deliverable Functional Specification (Non‑Technical) v1.0

Purpose of this document
- This specification explains, in plain language, what the delivered browser extension (“Flow”) does and does not do. It is intended for acceptance and warranty reference. Anything not described here is out of scope and may require a new agreement.

1) What the extension does (high level)
- Automates simple, repeatable actions on a small set of web pages related to messages and product offers.
- Monitors for new messages and opens relevant links within defined limits and time windows.
- On product pages, it follows links and runs a pre-defined “buy offer” sequence when conditions match.
- If an image-based check is needed (e.g., visual recognition), it sends that image to the TRC backend API and uses the returned text/result.
- Provides a Popup to show active tasks (“flows”) and a switch to enable/disable the extension.
- Provides an Options page to set the API token and adjust behavior such as refresh timing, daily time windows, and which monitors are active.

2) Where it works (supported pages)
- Outlook Web (Inbox): outlook.office.com (and Microsoft’s security-mirrored domain) — “Email mode”.
- HanseMerkur pages (and their localhost equivalents for testing):
  - Inbox: my_message_center_inbox.html — “Inbox mode”
  - Message details: my_message_center_show_message.php
  - Item page: item.php
  - Buy-now page: buy_now/id/*

3) How it behaves on each page
A. Outlook Web: Email mode
- When Email mode is ON, the extension periodically checks for new messages according to the configured refresh timing (see Options below) and looks for messages that contain relevant links.
- If a relevant link is found, it opens that link in a new tab for further processing on the target site.
- It does not send emails, delete emails, mark emails as read/unread, or change mailbox settings.
- If Email mode is OFF, the extension does not scan or open email links.

B. HanseMerkur Inbox: my_message_center_inbox.html
- When Inbox mode is ON, the extension reloads this page at the configured frequency and scans for message links that match the criteria.
- It opens up to a configured maximum number of links per scan (limit is adjustable in Options).
- It waits a short pause between opening links to avoid stressing the browser/site (adjustable in Options).
- If Inbox mode is OFF, the extension does not reload this page or open inbox links.

C. HanseMerkur Message details: my_message_center_show_message.php
- When opened from Email mode or Inbox mode, the extension looks for the primary product link in the message and opens it.
- If no link is present or the page format has changed, it does nothing.

D. HanseMerkur Item page: item.php
- The extension reads the visible information needed to decide which action to take (for example, a product type or age shown on the page).
- If the page provides a “buy now” link, the extension will follow that link to the buy-now page.
- The extension does not edit page content or submit forms on this page.

E. HanseMerkur Buy-now page: buy_now/id/*
- The extension runs a predefined “buy offer” sequence designed for this page.
- If the page is missing expected elements or has changed significantly, the extension logs the issue and stops (it does not attempt unsafe actions).
- The extension does not attempt to bypass security checks. If an image prompt (e.g., a captcha) is shown, the extension may capture the image and send it to the TRC backend to interpret. If the backend returns a result, the extension uses it to proceed; otherwise it stops gracefully.

Important: The extension only acts on the specific pages above. If those pages change layout, names, or behavior, or if new pages are introduced, additional paid work may be required.

4) Popup page (what the user sees)
- Enable/Disable switch: A single toggle that turns the extension’s automation ON or OFF globally.
- Active flows: A simple list of recent/active tasks with their status (running, done, failed), start time, and duration. This list is for visibility only and does not provide manual control over steps.

5) Options page (configuration)
A. Authentication
- API token: A field to paste the API token obtained from the TRC web portal. Without a valid token, image solving will not work and related tasks will fail gracefully.

B. Message monitoring — Email mode
- Email mode (ON/OFF): When ON, Outlook Web inbox is checked for new relevant messages.
- Email refresh timing: Two numbers (minimum and maximum, in minutes) define how frequently the extension re-checks the inbox. The extension uses these settings to space out checks and avoid constant polling.

C. Message monitoring — Inbox mode
- Inbox mode (ON/OFF): When ON, the HanseMerkur inbox page is periodically refreshed.
- Inbox refresh frequency: A simple schedule defining how often the page is refreshed (defaults provide frequent but brief checks). In practice, this means “refresh the inbox every few seconds” while the page is open.
- Max links per scan: Limits how many message links are opened each time the inbox is scanned (default 10). This avoids opening too many tabs at once.
- Delay between opening links: A short pause between opening each link (default ~0.4 seconds) for stability.

D. Valid time of day (per day of week)
- For each day (Sunday–Saturday), you can enable/disable automation and define a start time and end time. Outside those hours, no automated actions run even if modes are ON.

E. Product filters (if present)
- Category toggles (for example, Animals, Cancer, People) enable/disable processing for those product categories across the flows. When a category is OFF, the extension skips those items.
- Additional timing values for categories indicate approximate pacing of related actions.

6) What the extension does NOT do
- It does not send or delete emails.
- It does not change mailbox settings or manage folders.
- It does not act on websites other than the specific pages listed.
- It does not guarantee a purchase or outcome on third-party websites (availability, UI changes, network issues, or security features can prevent actions).
- It does not store personal data on external services other than the images/results sent to and received from the TRC backend strictly for image interpretation when needed.

7) Safeguards and limits
- Global ON/OFF switch in the Popup.
- Daily time windows (valid time of day) to prevent actions outside business hours.
- Rate limits: maximum links opened per scan; short pauses between openings.
- If the API token is missing or invalid, related actions stop and an error is shown in logs.
- If a page changes or a required element is missing, the extension stops the action and logs the issue.

8) Assumptions and dependencies
- The supported websites remain materially similar to those used during development (same page names and essential elements).
- The user supplies and maintains a valid API token and has accepted the TRC terms.
- The TRC backend is reachable and returns results for image-based checks.
- The extension is enabled, the relevant modes are turned ON, and the browser remains open on the relevant pages.

9) Acceptance criteria (user-visible)
- Installation: The extension loads in Chrome and shows the Popup and Options pages.
- Configuration: User can paste an API token; settings are saved.
- Email mode: When ON and within valid time windows, the extension periodically checks Outlook Web inbox and opens relevant links. When OFF, it does nothing on Outlook.
- Inbox mode: When ON and within valid time windows, the extension refreshes the HanseMerkur inbox page, opens up to the configured number of links per scan, and pauses briefly between openings. When OFF, it does nothing on that page.
- Product flow: On item and buy-now pages, the extension follows the predefined sequence; if something is missing or changed, it stops safely and logs the issue.
- Image solving: When prompted by the page, the extension sends the image to the TRC backend and uses the returned text if successful; otherwise it logs and stops.

10) Warranty scope reference
- The 90‑day warranty covers reproducible defects where the extension fails to perform the behaviors described here within the configured options and valid time windows, on the supported pages, under the agreed operating environment.
- Changes to third‑party sites, additional pages, new flows, or behaviors not described in this document are out of scope and may require a separate paid engagement.

11) Image Solver – Warranty and Use Notice
- The Image Solver is an optional convenience feature that tries to read a math question from a picture and returns only the final numeric answer.
- It relies on a third-party AI service. Accuracy, availability, and response times are not guaranteed and may change without notice.
- Results may be incomplete or incorrect, or no problem may be detected—especially with unclear or low‑quality images. Always verify results independently.
- This feature is not intended for safety‑critical or other high‑risk uses. Use is at your own risk, and we are not liable for losses arising from reliance on its output.
- Images you submit are sent to an external provider only to process your request; we do not retain them longer than necessary to provide the service. Using this feature means you consent to this transfer.
- We may limit, suspend, or discontinue this feature at any time (for example, due to provider limits, costs, policy, or abuse prevention).
- If no valid math problem is detected, the service may return a message indicating that no problem was found.
- This feature does not automatically modify your data or documents; it only returns a suggested answer for you to review.
- This feature is provided “as is,” without warranties of any kind (including accuracy or fitness for a particular purpose).
- Math problem recognition and output rules:
  - If the image contains a math problem, return only the numerical answer.
  - For expressions like "2+2", return "4".
  - For equations like "x=5+3", return "8".
  - If there are multiple problems, solve all and return answers separated by commas.
  - If you cannot identify a math problem, return "ERROR: No math problem found".
  - Do not include units, explanations, or any other text — just the number(s).
- Examples (non-exhaustive):
  - Image shows "3 + 5" → Return: "8"
  - Image shows "12 × 4" → Return: "48"
  - Image shows "100 ÷ 5" → Return: "20"
  - Image shows "7 - 3" → Return: "4"
  - Image shows "2³" → Return: "8"
  - Image shows "√16" → Return: "4"
  - Image shows "What is 15% of 200?" → Return: "30"
  - Image shows multiple: "2+2" and "3×3" → Return: "4, 9"
