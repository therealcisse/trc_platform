import { openAllSimulationLinks } from '@src/lib';

console.log('[CEB] Simulations content script loaded');

// Automatically execute when the script loads
openAllSimulationLinks();

// Also allow manual triggering via console for debugging
(window as any).openSimulationLinks = openAllSimulationLinks;
