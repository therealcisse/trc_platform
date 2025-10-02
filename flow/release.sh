#!/usr/bin/env bash
set -euo pipefail

# =========================
# Config
# =========================
: "${PROJECT_NAME:=Flow}"                    # Used in email subject
: "${PRODUCT_NAME:=Image Solver Extension}"                    # Used in email body
: "${RECIPIENT_NAME:=Patrycjusz}"            # Used in email greeting
: "${DIST_DIR:=dist}"                        # Folder to package
: "${OUTPUT_EMAIL:=delivery_email.txt}"      # Email output file name
: "${OUTPUT_SUM:=checksum.txt}"              # Checksum output file name

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

validity_date() {
  # Try GNU date first, fallback to BSD date
  if date -d "+7 days" "+%d %B %Y" >/dev/null 2>&1; then
    date -d "+7 days" "+%d %B %Y"
  else
    date -v+7d "+%d %B %Y"
  fi
}

# =========================
# Arguments
# =========================
VERSION=""
KEY_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --key)
      KEY_PATH="$2"
      shift 2
      ;;
    --key=*)
      KEY_PATH="${1#*=}"
      shift
      ;;
    *)
      if [[ -z "$VERSION" ]]; then
        VERSION="$1"
      else
        die "Unknown argument: $1"
      fi
      shift
      ;;
  esac
done

# =========================
# Preflight checks
# =========================
command -v pnpm >/dev/null 2>&1 || die "pnpm not found"
command -v git >/dev/null 2>&1 || die "git not found"
command -v zip >/dev/null 2>&1 || die "zip not found"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not a git repository."

# =========================
# Version bump, commit
# =========================
if [[ -n "$VERSION" ]]; then
  echo "Setting version: $VERSION"
  pnpm update-version "$VERSION"
else
  echo "No version argument provided, skipping version bump."
  VERSION="$(node -p "require('./package.json').version")"
  echo "Using existing version: $VERSION"
fi

echo "Running build"
pnpm build

[[ -d "$DIST_DIR" ]] || die "Dist folder '$DIST_DIR' does not exist."

# =========================
# Package Chrome extension
# =========================
if [[ -n "$KEY_PATH" ]]; then
  echo "Packaging Chrome extension with key: $KEY_PATH"
  [[ -f "$KEY_PATH" ]] || die "Key file not found: $KEY_PATH"

  PACKAGE_NAME="$(node -p "require('./package.json').name")"
  CRX_NAME="${PACKAGE_NAME}_v${VERSION}.crx"

  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --pack-extension="./$DIST_DIR" \
    --pack-extension-key="$KEY_PATH"

  # Chrome creates the .crx in the parent directory of dist
  if [[ -f "${DIST_DIR}.crx" ]]; then
    mv "${DIST_DIR}.crx" "$CRX_NAME"
    echo "Chrome extension packaged: $CRX_NAME"
  else
    echo "Warning: Chrome extension .crx file not found"
    CRX_NAME=""  # Clear the variable if packaging failed
  fi
else
  echo "Skipping Chrome extension packaging (no --key provided)"
  CRX_NAME=""
fi

echo "Staging and committing build changes"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "chore(release): v$VERSION"
else
  echo "No changes to commit."
fi

# =========================
# Prepare release directory
# =========================
RELEASE_DIR="releases/$VERSION"
mkdir -p "$RELEASE_DIR"

# =========================
# Package dist and checksum
# =========================
DATE_STR="$(date +%F)"
ZIP_NAME="${PRODUCT_NAME// /_}_v${VERSION}_${DATE_STR}.zip"
ZIP_PATH="$RELEASE_DIR/$ZIP_NAME"

echo "Creating archive: $ZIP_PATH"
(
  cd "$DIST_DIR"
  zip -r -q -X "../$ZIP_PATH" .
)

echo "Computing SHA-256 checksum"
CHECKSUM="$(sha256_file "$ZIP_PATH")"
echo "$CHECKSUM  $ZIP_NAME" | tee "$RELEASE_DIR/$OUTPUT_SUM" >/dev/null

# Move .crx to release directory if it exists
if [[ -n "$CRX_NAME" && -f "$CRX_NAME" ]]; then
  mv "$CRX_NAME" "$RELEASE_DIR/$CRX_NAME"
  CRX_CHECKSUM="$(sha256_file "$RELEASE_DIR/$CRX_NAME")"
  echo "$CRX_CHECKSUM  $CRX_NAME" | tee -a "$RELEASE_DIR/$OUTPUT_SUM" >/dev/null
  echo "Chrome extension moved to: $RELEASE_DIR/$CRX_NAME"
  
  # Zip the .crx file
  CRX_ZIP_NAME="${CRX_NAME%.crx}.crx.zip"
  echo "Creating crx archive: $RELEASE_DIR/$CRX_ZIP_NAME"
  (
    cd "$RELEASE_DIR"
    zip -q "$CRX_ZIP_NAME" "$CRX_NAME"
  )
  CRX_ZIP_CHECKSUM="$(sha256_file "$RELEASE_DIR/$CRX_ZIP_NAME")"
  echo "$CRX_ZIP_CHECKSUM  $CRX_ZIP_NAME" | tee -a "$RELEASE_DIR/$OUTPUT_SUM" >/dev/null
  echo "Chrome extension zip created: $RELEASE_DIR/$CRX_ZIP_NAME"
fi

# =========================
# Generate email
# =========================
VALIDITY="$(validity_date)"

EMAIL_SUBJECT="Software Delivery — ${PROJECT_NAME}, Version ${VERSION}"
EMAIL_BODY=$(cat <<EOF
Subject: ${EMAIL_SUBJECT}

Dear ${RECIPIENT_NAME},

Please find below the delivery of the software as agreed in our contract.

Project: ${PROJECT_NAME}
Product: ${PRODUCT_NAME}
Version: ${VERSION}

Download link (valid until ${VALIDITY}):
${ZIP_NAME}

Checksum (SHA-256):
${CHECKSUM}

Please verify the checksum after download. Kindly confirm receipt and integrity by replying to this email.

Best regards,
Amadou Cisse
EOF
)

echo "$EMAIL_BODY" | tee "$RELEASE_DIR/$OUTPUT_EMAIL" >/dev/null

# =========================
# Done
# =========================
echo
echo "Delivery artifacts created in $RELEASE_DIR:"
echo "  Archive:        $ZIP_PATH"
if [[ -n "$CRX_NAME" && -f "$RELEASE_DIR/$CRX_NAME" ]]; then
  echo "  Extension:      $RELEASE_DIR/$CRX_NAME"
  if [[ -f "$RELEASE_DIR/$CRX_ZIP_NAME" ]]; then
    echo "  Extension zip:  $RELEASE_DIR/$CRX_ZIP_NAME"
  fi
fi
echo "  Checksum file:  $RELEASE_DIR/$OUTPUT_SUM"
echo "  Email template: $RELEASE_DIR/$OUTPUT_EMAIL"
