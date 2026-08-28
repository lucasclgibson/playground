// Side panel wiring. Chrome only lets an extension open its side panel in
// response to a user gesture, so the panel is enabled automatically on DVSA
// pages and opened by the toolbar icon, the keyboard shortcut, or the button
// the content script puts on the page.

const DVSA_HOST = 'dvsa.gov.uk';

function isDvsa(url) {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' && (parsed.hostname === DVSA_HOST || parsed.hostname.endsWith('.' + DVSA_HOST));
  } catch (err) {
    return false;
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {
    /* older Chrome without the behaviour toggle still opens via the action */
  });
});

// Offer the panel on DVSA tabs and nowhere else, so the toolbar icon does
// nothing surprising on unrelated sites.
async function syncPanel(tabId, url) {
  try {
    await chrome.sidePanel.setOptions({
      tabId,
      path: 'sidepanel.html',
      enabled: isDvsa(url),
    });
  } catch (err) {
    /* tab closed mid-update */
  }
}

chrome.tabs.onUpdated.addListener((tabId, info, tab) => {
  if (!info.status && !info.url) return;
  syncPanel(tabId, tab.url);
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === 'open-side-panel' && sender.tab) {
    // The click happened in the page, so the gesture may or may not carry
    // through to us depending on the Chrome version. If it doesn't, the user
    // still has the toolbar icon and the keyboard shortcut.
    chrome.sidePanel
      .open({ tabId: sender.tab.id })
      .then(() => sendResponse({ opened: true }))
      .catch(() => sendResponse({ opened: false }));
    return true;
  }
  return false;
});
