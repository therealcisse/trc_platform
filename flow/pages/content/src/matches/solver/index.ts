import { processImage } from '@src/lib';

console.log('[CEB] Simulations solver content script loaded');

/**
 * Auto-process the simulation page when it loads
 */
function autoProcessSimulation(): void {
  // Check if we're on a simulation page (has the validation form)
  const hasValidationForm = document.getElementById('validationForm');
  const hasImage = document.querySelector('.image-container img');

  if (!hasValidationForm || !hasImage) {
    console.log('[CEB] Not a simulation page, skipping auto-process');
    return;
  }

  console.log('[CEB] Simulation page detected, starting auto-process...');

  // Wait a moment for the page to fully render
  setTimeout(async () => {
    try {
      await processImage();
      console.log('[CEB] Auto-process completed');
    } catch (error) {
      console.error('[CEB] Auto-process failed:', error);
    }
  }, 500);
}

// Run when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', autoProcessSimulation);
} else {
  autoProcessSimulation();
}

// Also expose for manual triggering via console
(window as any).processSimulation = processImage;
