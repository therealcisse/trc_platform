Title: Generate self-contained HTML pages for numeric-named images in `simulations/` and an index

Goal:
Create one standalone HTML file per image in the `simulations/` folder, plus an `index.html` that links to all generated pages. Each page shows its corresponding image and a validation UI. All HTML files must be self contained with inline CSS and JavaScript, no external dependencies.

Input:
A folder `simulations/` that contains multiple image files. Each image filename consists only of digits and an extension, for example `1.png`, `11.png`, `007.jpg`. Supported extensions: `.png`, `.jpg`, `.jpeg`.

Output:

1. For every image file in `simulations/`, generate an HTML file in the same `simulations/` folder. The HTML filename equals the image filename with the extension replaced by `.html`. Examples:

   * `1.png` to `1.html`
   * `11.png` to `11.html`
   * `007.jpg` to `007.html`

2. Generate `simulations/index.html` that lists links to all generated HTML pages.

Per page requirements:

* Layout: Center content vertically and horizontally in a responsive single column, with a visually balanced card. Good symmetry and spacing on mobile and desktop.
* Image: Display at the top, responsive with preserved aspect ratio, capped by a max width. Use `alt` text equal to the base filename without extension.
* Validation UI below the image:

  * A labeled text input and a button labeled “Validate”. Pressing Enter triggers validation.
  * Validation rule: The expected value is the base filename string without the extension, exactly as is. The input, after trimming, must match this string exactly. Examples:

    * For `11.png` only `11` is valid. `011` is invalid.
    * For `007.jpg` only `007` is valid.
    * For `1.jpeg` only `1` is valid.
  * Input must contain only digits. If it contains any non digit characters, treat as invalid.
  * On success, display “OK”. On failure, display “KO”. Show the message inline under the button with clear success or error styling.
* Accessibility:

  * Associate label and input with `for` and `id`.
  * Provide `aria-live="polite"` for the validation result.
  * Ensure visible focus states for interactive elements.
* Visual design:

  * Inline `<style>` only. Clean, modern look, readable system font stack, generous spacing, and a subtle card. Elegant styling for input and button with hover and focus states. No external assets.

Index page requirements (`simulations/index.html`):

* Title: “Simulations Index”.
* List links to all generated HTML pages. The visible link text is the base filename without extension.
* Use protocol relative links so the folder can be served at any host and port without hard coding. Build `href` as:

  * `//` + `location.host` + `/simulations/` + `<page>.html`
  * Implement this with JavaScript at render time so it works regardless of host or port. For users browsing the index as a local file, also provide a fallback to `./<page>.html`.
* The index file must be self contained with inline CSS and JavaScript, no external assets.

Technical constraints:

* No external CSS frameworks, libraries, or fonts. No CDN links.
* Each generated page must load without console errors.
* Use semantic HTML, for example `<main>`, headings, labels.
* Preserve filenames exactly, including any leading zeros. Match must be string exact after trimming.

Edge cases and examples:

* `11.png` expects input `11` exactly.
* `007.jpg` expects input `007` exactly. `7` is invalid.
* `1.jpeg` expects input `1` exactly.
* Input with spaces is trimmed before comparison. Non digit characters cause KO.

Delivery:

* Write all generated files into `simulations/`.
* Ensure the index links resolve correctly using protocol relative links built from `location.host`, with a `./` fallback for local file browsing.

Acceptance criteria:

* Exactly one HTML page per image plus `index.html`.
* Pages are self contained, responsive, accessible, and visually balanced.
* Validation performs an exact string match against the numeric filename without the extension.
* Index opens each page correctly using protocol relative links at runtime, with a local fallback.
