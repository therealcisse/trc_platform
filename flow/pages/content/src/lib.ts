
/**
 * Opens all simulation links found on the page in new tabs
 */
export function openAllSimulationLinks(): void {
  console.log('[CEB] Looking for simulation links to open...');

  // Function to extract and open links
  const processLinks = () => {
    // Find all links in the list items
    const links = document.querySelectorAll('ul li a');

    if (links.length === 0) {
      console.log('[CEB] No simulation links found');
      return;
    }

    console.log(`[CEB] Found ${links.length} simulation links`);

    // Collect all valid hrefs
    const hrefs: string[] = [];

    links.forEach((link) => {
      if (link instanceof HTMLAnchorElement) {
        const href = link.href;

        // Skip invalid links
        if (!href || href === '#' || href === 'javascript:void(0)') {
          return;
        }

        // Resolve relative URLs to absolute
        let absoluteUrl = href;
        if (href.startsWith('./')) {
          // Handle relative paths
          const baseUrl = window.location.origin + window.location.pathname.replace(/\/[^\/]*$/, '/');
          absoluteUrl = baseUrl + href.substring(2);
        } else if (!href.startsWith('http')) {
          // Handle other relative paths
          absoluteUrl = new URL(href, window.location.href).href;
        }

        hrefs.push(absoluteUrl);
      }
    });

    if (hrefs.length === 0) {
      console.log('[CEB] No valid links to open');
      return;
    }

    // Open all links with a delay to prevent browser blocking
    console.log(`[CEB] Opening ${hrefs.length} links...`);

    hrefs.forEach((href, index) => {
      setTimeout(() => {
        console.log(`[CEB] Opening link ${index + 1}/${hrefs.length}: ${href}`);

        // Use window.open with specific features to ensure new tab
        const newWindow = window.open(href, '_blank', 'noopener,noreferrer');

        if (!newWindow) {
          console.warn(`[CEB] Failed to open: ${href} (popup may be blocked)`);
        }
      }, index * 150); // 150ms delay between each tab to avoid blocking
    });

    // Log completion after all tabs should be opened
    setTimeout(() => {
      console.log('[CEB] Finished opening all simulation links');
    }, hrefs.length * 150 + 500);
  };

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processLinks);
  } else {
    // DOM is already ready, but let's give it a moment for any dynamic content
    setTimeout(processLinks, 100);
  }
}

/**
 * Processes an image from a simulation page by:
 * 1. Extracting the image from the DOM
 * 2. Sending it to the background script for API processing (bypasses CORS)
 * 3. Filling in the result and submitting the form
 */
export async function processImage(): Promise<void> {
  console.log('[CEB] Processing simulation image...');

  try {
    // Find the image element
    const imageElement = document.querySelector('.image-container img') as HTMLImageElement;
    if (!imageElement) {
      throw new Error('Image not found on page');
    }

    // Find the form elements
    const inputElement = document.getElementById('numberInput') as HTMLInputElement;
    const formElement = document.getElementById('validationForm') as HTMLFormElement;

    if (!inputElement || !formElement) {
      throw new Error('Form elements not found on page');
    }

    console.log('[CEB] Extracting image from:', imageElement.src);

    // Convert image to base64 data URL for message passing
    const imageDataUrl = await fetchImageAsDataUrl(imageElement.src);

    console.log('[CEB] Sending image to background script for processing...');

    // Send message to background script to process the image
    // This bypasses CORS completely as the background script makes the API call
    const response = await chrome.runtime.sendMessage({
      type: 'PROCESS_IMAGE',
      imageData: imageDataUrl
    });

    if (!response.success) {
      throw new Error(response.error || 'Failed to process image');
    }

    console.log('[CEB] Received result from background:', response.result);

    // Extract the numeric answer from the result
    // The API might return something like "The answer is 10" or just "10"
    const result = extractNumericAnswer(response.result);

    console.log('[CEB] Extracted answer:', result);

    // Fill in the input
    inputElement.value = result;

    // Trigger input event to ensure any validation listeners are fired
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));

    // Submit the form
    console.log('[CEB] Submitting form with answer:', result);

    // Find and click the submit button or submit the form directly
    const submitButton = formElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    if (submitButton) {
      submitButton.click();
    } else {
      formElement.submit();
    }

    console.log('[CEB] Image processing completed successfully');

  } catch (error) {
    console.error('[CEB] Error processing image:', error);

    // Show error in result div if it exists
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
      resultDiv.className = 'result error show';
      resultDiv.textContent = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
    }
  }
}

/**
 * Fetches an image URL and returns it as a data URL for message passing
 */
async function fetchImageAsDataUrl(imageUrl: string): Promise<string> {
  try {
    // If it's a relative URL, convert to absolute
    const absoluteUrl = new URL(imageUrl, window.location.href).href;

    const response = await fetch(absoluteUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status}`);
    }

    const blob = await response.blob();

    // Ensure it's an image
    if (!blob.type.startsWith('image/')) {
      throw new Error(`Fetched content is not an image: ${blob.type}`);
    }

    // Convert blob to data URL for message passing
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert image to data URL'));
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('[CEB] Error fetching image:', error);
    throw error;
  }
}

/**
 * Fetches an image URL and returns it as a Blob
 */
async function fetchImageAsBlob(imageUrl: string): Promise<Blob> {
  try {
    // If it's a relative URL, convert to absolute
    const absoluteUrl = new URL(imageUrl, window.location.href).href;

    const response = await fetch(absoluteUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status}`);
    }

    const blob = await response.blob();

    // Ensure it's an image
    if (!blob.type.startsWith('image/')) {
      throw new Error(`Fetched content is not an image: ${blob.type}`);
    }

    return blob;
  } catch (error) {
    console.error('[CEB] Error fetching image:', error);
    throw error;
  }
}

/**
 * Extracts a numeric answer from the API result text
 * The API might return various formats like:
 * - "10"
 * - "The answer is 10"
 * - "x = 10"
 * - "Result: 10"
 */
function extractNumericAnswer(result: string): string {
  // First, try to find the answer pattern from the simulation page
  // The correct answer format follows the pattern in the HTML files

  // Remove any markdown or formatting
  let cleanResult = result.replace(/```[\s\S]*?```/g, '')  // Remove code blocks
                          .replace(/[*_~`]/g, '')          // Remove markdown formatting
                          .trim();

  // Try to extract numbers that match the expected format
  // Look for patterns like "answer is X", "= X", "result: X", etc.
  const patterns = [
    /answer[\s:]*is[\s:]*(\d+)/i,
    /result[\s:]*is[\s:]*(\d+)/i,
    /=[\s]*(\d+)/,
    /:[\s]*(\d+)$/,
    /^(\d+)$/,
  ];

  for (const pattern of patterns) {
    const match = cleanResult.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }

  // If no pattern matches, try to find any number in the result
  const numbers = cleanResult.match(/\d+/g);
  if (numbers && numbers.length === 1) {
    return numbers[0];
  }

  // If multiple numbers or no numbers found, return the cleaned result
  // and let the validation handle it
  console.warn('[CEB] Could not extract clear numeric answer from:', result);
  return cleanResult;
}
