#!/usr/bin/env bash
set -euo pipefail

# =========================
# Config
# =========================
: "${PROJECT_NAME:=Flow}"        # Used in email subject
: "${PRODUCT_NAME:=Flow}"        # Used in email body
: "${RECIPIENT_NAME:=Patrycjusz}"          # Used in email greeting
: "${DIST_DIR:=dist}"                    # Folder to package
: "${OUTPUT_EMAIL:=delivery_email.txt}"  # Email output file
: "${OUTPUT_SUM:=checksum.txt}"          # Checksum output file

# =========================
# Helpers
# =========================
die() { echo "Error: $*" >&2; exit 1; }

sha256_file() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    die "Neither sha256sum nor shasum found"
  fi
}

# =========================
# Arguments
# =========================
VERSION="${1:-}"

# =========================
# Preflight checks
# =========================
command -v pnpm >/dev/null 2>&1 || die "pnpm not found"
command -v git >/dev/null 2>&1 || die "git not found"
command -v zip >/dev/null 2>&1 || die "zip not found"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not a git repository."

echo "Running build"
pnpm build

[[ -d "$DIST_DIR" ]] || die "Dist folder '$DIST_DIR' does not exist."

# =========================
# Version bump, build, commit
# =========================
if [[ -n "$VERSION" ]]; then
  echo "Setting version: $VERSION"
  pnpm update-version "$VERSION"
else
  echo "No version argument provided, skipping version bump."
  VERSION="$(node -p "require('./package.json').version")"
  echo "Using existing version: $VERSION"
fi

echo "Staging and committing build changes"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "chore(release): v$VERSION"
else
  echo "No changes to commit."
fi

# =========================
# Package dist and checksum
# =========================
DATE_STR="$(date +%F)"
ZIP_NAME="${PRODUCT_NAME// /_}_v${VERSION}_${DATE_STR}.zip"

echo "Creating archive: $ZIP_NAME"
(
  cd "$DIST_DIR"
  zip -r -q -X "../$ZIP_NAME" .
)

echo "Computing SHA-256 checksum"
CHECKSUM="$(sha256_file "$ZIP_NAME")"
echo "$CHECKSUM  $ZIP_NAME" | tee "$OUTPUT_SUM" >/dev/null

# =========================
# Generate email
# =========================
EMAIL_SUBJECT="Software Delivery — ${PROJECT_NAME}, Version ${VERSION}"
EMAIL_BODY=$(cat <<EOF
Subject: ${EMAIL_SUBJECT}

Dear ${RECIPIENT_NAME},

Please find below the delivery of the software as agreed in our contract.

Project: ${PROJECT_NAME}
Product: ${PRODUCT_NAME}
Version: ${VERSION}

File: ${ZIP_NAME}
Checksum (SHA-256): ${CHECKSUM}

Please verify the checksum after download. Kindly confirm receipt and integrity by replying to this email.

Best regards,
Amadou Cisse
EOF
)

echo "$EMAIL_BODY" | tee "$OUTPUT_EMAIL" >/dev/null

# =========================
# Done
# =========================
echo
echo "Delivery artifacts created:"
echo "  Archive:        $ZIP_NAME"
echo "  Checksum file:  $OUTPUT_SUM"
echo "  Email template: $OUTPUT_EMAIL"

