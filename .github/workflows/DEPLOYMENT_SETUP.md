# Cloudflare Pages Deployment Setup

This guide explains how to configure GitHub Actions for deploying the frontend to Cloudflare Pages.

## Required GitHub Secrets

You need to add the following secrets to your GitHub repository:

### 1. Cloudflare Authentication

#### `CLOUDFLARE_API_TOKEN`
- **Required**: Yes
- **Description**: Cloudflare API token with permissions to deploy to Pages
- **How to get it**:
  1. Go to https://dash.cloudflare.com/profile/api-tokens
  2. Click "Create Token"
  3. Use the "Custom token" template
  4. Set permissions:
     - Account > Cloudflare Pages:Edit
     - Zone > Zone:Read (if using custom domain)
  5. Copy the generated token

#### `CLOUDFLARE_ACCOUNT_ID`
- **Required**: Yes
- **Description**: Your Cloudflare account ID
- **How to get it**:
  1. Go to https://dash.cloudflare.com/
  2. Select your account
  3. Copy the Account ID from the right sidebar

### 2. Application Configuration

#### `VITE_API_URL`
- **Required**: Yes
- **Description**: Production API endpoint URL
- **Example**: `https://api.yourdomain.com/api`
- **Default for development**: `http://localhost:8000/api`

#### `VITE_API_URL_PREVIEW`
- **Required**: No (only for PR previews)
- **Description**: Preview/staging API endpoint URL
- **Example**: `https://staging-api.yourdomain.com/api`
- **Note**: Can be the same as `VITE_API_URL` if you don't have a separate staging environment

#### `VITE_MAX_VERIFICATION_ATTEMPTS`
- **Required**: No
- **Description**: Maximum number of email verification attempts allowed per day
- **Default**: `3`

## How to Add Secrets to GitHub

1. Go to your repository on GitHub: https://github.com/therealcisse/trc_platform
2. Click on "Settings" tab
3. Navigate to "Secrets and variables" > "Actions"
4. Click "New repository secret"
5. Add each secret with its name and value
6. Click "Add secret"

## Cloudflare Pages Project Setup

Before the first deployment, you may need to create the Cloudflare Pages project:

### Option 1: Automatic Creation
The GitHub Action will attempt to create the project automatically on first deployment.

### Option 2: Manual Creation
1. Go to https://dash.cloudflare.com/pages
2. Click "Create a project"
3. Choose "Direct Upload"
4. Name your project: `trc-platform`
5. Upload a dummy file (the GitHub Action will handle actual deployments)
6. Configure custom domain if needed

## Custom Domain Configuration (Optional)

After the first deployment, you can add a custom domain:

1. Go to your Cloudflare Pages project
2. Navigate to "Custom domains" tab
3. Click "Set up a custom domain"
4. Follow the instructions to configure DNS

## Deployment Workflow

### Production Deployment
- Triggers on push to `main` branch
- Only when files in `frontend/` directory change
- Deploys to main Cloudflare Pages URL

### Preview Deployment
- Triggers on pull requests to `main` branch
- Creates a preview URL for testing
- Comments the preview URL on the PR

### Manual Deployment
- Can be triggered manually from GitHub Actions tab
- Useful for redeploying without code changes

## Troubleshooting

### Build Fails
- Check that all npm dependencies are properly installed
- Verify that the build command works locally: `npm run build`
- Check GitHub Actions logs for specific error messages

### Deployment Fails
- Verify Cloudflare API token has correct permissions
- Ensure account ID is correct
- Check that the project name matches in Cloudflare Pages

### Environment Variables Not Working
- Ensure secrets are properly set in GitHub
- Variable names must match exactly (case-sensitive)
- Check that variables are used with `VITE_` prefix in the frontend code

## Local Testing

To test the build locally with production settings:

```bash
cd frontend
npm ci
VITE_API_URL=https://api.yourdomain.com/api npm run build
npm run preview
```

## Support

For issues related to:
- GitHub Actions: Check the Actions tab in your repository
- Cloudflare Pages: Visit https://dash.cloudflare.com/pages
- Wrangler CLI: Run `npx wrangler pages --help`
