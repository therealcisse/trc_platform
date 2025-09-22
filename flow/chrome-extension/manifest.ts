import { readFileSync } from 'node:fs';
import type { ManifestType } from '@extension/shared';

const packageJson = JSON.parse(readFileSync('./package.json', 'utf8'));

/**
 * @prop default_locale
 * if you want to support multiple languages, you can use the following reference
 * https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Internationalization
 *
 * @prop browser_specific_settings
 * Must be unique to your extension to upload to addons.mozilla.org
 * (you can delete if you only want a chrome extension)
 *
 * @prop permissions
 * Firefox doesn't support sidePanel (It will be deleted in manifest parser)
 *
 * @prop content_scripts
 * css: ['content.css'], // public folder
 */
const manifest = {
  manifest_version: 3,
  default_locale: 'en',
  name: 'trc_platform_extension',
  browser_specific_settings: {
    gecko: {
      id: 'example@example.com',
      strict_min_version: '109.0',
    },
  },
  version: packageJson.version,
  description: 'TRC Platform Extension',
  host_permissions: ['<all_urls>'],
  permissions: ['storage', 'scripting', 'tabs', 'notifications'],
  options_page: 'options/index.html',
  background: {
    service_worker: 'background.js',
    type: 'module',
  },
  action: {
    default_popup: 'popup/index.html',
    default_icon: 'icon-34.png',
  },
  icons: {
    '128': 'icon-128.png',
  },
  content_scripts: [
    {
      matches: ['https://outlook.office.com/mail/*', 'https://outlook.office.com.mcas.ms/mail/*'],
      js: ['content/email.iife.js'],
      run_at: 'document_end',
    },
    {
      matches: [
        'http://localhost:8082/item/*',
        'https://auktion.hansemerkur.de/item.php',
      ],
      js: ['content/item.iife.js'],
      run_at: 'document_end',
    },
    {
      matches: [
        'http://localhost:8082/buy_now/id/*',
        'https://auktion.hansemerkur.de/buy_now/id/*',
      ],
      js: ['content/buyOffer.iife.js'],
      run_at: 'document_end',
    },
    {
      matches: [
        'http://localhost:8082/myOffer/*',
        'https://auktion.hansemerkur.de/my_message_center_show_message.php',
      ],
      js: ['content/myOffer.iife.js'],
      run_at: 'document_end',
    },
    {
      matches: [
        'http://localhost:8082/inbox.html',
        'https://auktion.hansemerkur.de/my_message_center_inbox.html',
      ],
      js: ['content/inbox.iife.js'],
      run_at: 'document_end',
    },
  ],
  web_accessible_resources: [
    {
      resources: ['*.js', '*.css', '*.svg', 'icon-128.png', 'icon-34.png'],
      matches: ['*://*/*'],
    },
  ],
} satisfies ManifestType;

export default manifest;
