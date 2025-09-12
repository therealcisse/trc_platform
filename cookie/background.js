class LocalDate {
  constructor() {
    const d = new Date();
    self.localDate = new Date(d.getTime() - d.getTimezoneOffset() * 60 * 1000);
  }

  toString() {
    return self.localDate.toISOString().split("Z")[0];
  }

  getHours() {
    return self.localDate.getHours();
  }

  getMinutes() {
    return self.localDate.getMinutes();
  }

  getDay() {
    return self.localDate.getDay();
  }
}

const openedTabs = {};
const buyingOffers = {};

const watchedTimers = {};

// debugging
const viewedUrls = {};
const viewedOffers = {};

async function reloadTabIfUrl(enabled, url) {
  const tabs = await chrome.tabs.query({
    url,
  });
  if (enabled && tabs.length > 0) {
    const mainTab = tabs.shift();
    await chrome.tabs.reload(mainTab.id);
    for (const tab of tabs) {
      await chrome.tabs.remove(tab.id);
    }
  }
}
chrome.storage.onChanged.addListener(async (changes, area) => {
  // console.log(changes, area);
  if (area === "sync" && changes.enabled?.newValue) {
    const enabled = Boolean(changes.enabled.newValue);

    await reloadTabIfUrl(enabled,  "https://auktion.hansemerkur.de/karte_sofortkauf.html");
    await reloadTabIfUrl(enabled,  "https://outlook.office.com/mail*");
    await reloadTabIfUrl(enabled,  "https://outlook.office.com.mcas.ms/mail*");
    // const tabs = await chrome.tabs.query({
    //   url: "https://auktion.hansemerkur.de/karte_sofortkauf.html",
    // });
    // if (enabled && tabs.length > 0) {
    //   const mainTab = tabs.shift();
    //   await chrome.tabs.reload(mainTab.id);
    //   for (const tab of tabs) {
    //     await chrome.tabs.remove(tab.id);
    //   }
    // }

    // const tabs2 = await chrome.tabs.query({
    //   url: "https://outlook.office.com/mail*",
    // });
    // if (enabled && tabs2.length > 0) {
    //   const mainTab = tabs2.shift();
    //   await chrome.tabs.reload(mainTab.id);
    //   for (const tab of tabs2) {
    //     await chrome.tabs.remove(tab.id);
    //   }
    // }
  }
});

// chrome.storage.setAccessLevel("TRUSTED_AND_UNTRUSTED_CONTEXTS");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // console.log(sender, request);

  // message from popup.js
  if (!sender.tab) {
    switch (request.action) {
      case "isManagedTab":
        sendResponse(request.tabId in openedTabs);
        return;
      case "manageTab":
        openedTabs[request.tabId] = Date.now();
        sendResponse(true);
        return;
      case "unmanageTab":
        delete openedTabs[request.tabId];
        sendResponse(true);
        return;
    }
    return;
  }

  // message from content.js
  switch (request.action) {
    case "log":
      (async () => {
        // await chrome.storage.local.remove(["logs"]);
        let logs = (await chrome.storage.local.get(["logs"]))?.logs;
        if (!logs) {
          logs = [];
        }
        logs.push(`${new LocalDate().toString()} ${request.text}`);
        await chrome.storage.local.set({ logs });
        sendResponse(true);
      })();
      return true;

    case "openTab":
      (async () => {
        const tab = await chrome.windows.create({
          url: request.url,
          //active: false,
          //windowId: sender.tab.windowId,
        });
        openedTabs[tab.id] = Date.now();
        sendResponse(tab);
      })();
      return true;

    case "closeTab":
      (async () => {
        delete openedTabs[tab.id];
        sendResponse(await chrome.tabs.remove(request.id));
      })();
      return true;

    case "closeCurrentTab":
      (async () => {
        delete openedTabs[sender.tab.id];
        console.log("Closing current tab", sender.tab.id);
        const r = await chrome.tabs.remove(sender.tab.id);
        sendResponse(r);
      })();
      return true;
    case "isManagedTab":
      console.log(sender.tab);
      sendResponse(sender.tab.id in openedTabs);
      return;

    case "isEnabled":
      (async () => {
        sendResponse(!!(await chrome.storage.sync.get(["enabled"])).enabled);
      })();
      return true;

    case "config":
      (async () => {
        sendResponse((await chrome.storage.sync.get(["config"])).config);
      })();
      return true;

    case "markBuying":
      buyingOffers[request.key] = {
        id: request.id,
        timeout: request.timeout,
      };
      sendResponse(true);
      return;

    case "isBuying":
      const entry = buyingOffers[request.key];
      if (!entry) {
        sendResponse({ buying: false });
        return;
      }

      // remove from cache if timeout has elapsed
      if (Date.now() > entry.timeout) {
        delete buyingOffers[request.key];
        sendResponse({ buying: false });
        return;
      }

      sendResponse({ buying: true, id: entry.id });
      return;

    case "watchTimer":
      watchedTimers[request.key] = true;
      sendResponse(true);
      return;
    case "unwatchTimer":
      delete watchedTimers[request.key];
      sendResponse(true);
      return;
    case "isWatchedTimer":
      sendResponse(watchedTimers[request.key] === true);
      return;
  }
});
