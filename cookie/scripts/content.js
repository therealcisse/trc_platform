class LocalDate {
  constructor() {
    const d = new Date();
    this.utcDate = new Date();
    this.localDate = new Date(
      this.utcDate - this.utcDate.getTimezoneOffset() * 60 * 1000
    );
  }

  toString() {
    return this.localDate.toISOString().split("Z")[0];
  }

  getHours() {
    return this.utcDate.getHours();
  }

  getMinutes() {
    return this.utcDate.getMinutes();
  }

  getSeconds() {
    return this.utcDate.getSeconds();
  }

  getMilliseconds() {
    return this.utcDate.getMilliseconds();
  }

  getDay() {
    return this.utcDate.getDay();
  }
}

class Log {
  constructor(title) {
    this.text = title ? [title] : [];
  }

  push(text) {
    this.text.push(text);
    return this;
  }

  async write() {
    if (this.text.length === 0) {
      return;
    }

    await chrome.runtime.sendMessage({
      action: "log",
      text: this.text.join(";"),
    });
    this.text = [];
  }
}

class Product {
  constructor(text) {
    const match = text.match(
      /([^:]+).* (?:(\S+)\s+Alter|Alter\s+(\S+)): (\d+)/
    );
    if (!match) {
      console.log(`failed matching: ${text}`);
      this.valid = false;
      return;
    }

    this.text = text;
    this.name = match[1];
    this.insuredType = match[2] || match[3];
    this.insuredAge = parseInt(match[4]);
    this.meta = {};

    if (isNaN(this.insuredAge)) {
      console.log(`failed parsing age: ${match[4]}`);
      this.valid = false;
      return;
    }

    if (match[1] === "KV-Voll Arbeitnehmer KW") {
      this.meta.aboveIncomeLimit = false;
      // buy
      if (text.match(/Tätigkeit:\sAngestellter/)) {
        this.meta.aboveIncomeLimit = true;
      }

      // check if JAEG is present above income threshold
      const match = text.match(/(\S+) JAEG/);
      if (match) {
        this.meta.aboveIncomeLimit = match[1] === "über";
      }
    }

    this.valid = true;
  }

  isAllowed(config) {
    const result = { allowed: false, delay: 0 };
    if (!this.valid) {
      return result;
    }

    const usePeople = config.people;
    const useAnimals = config.animals;
    const useCancer = config.cancer;

    if (useAnimals && this.name === "Tier KV KW") {
      if (this.insuredType === "Hund" && this.insuredAge <= 3) {
        result.allowed = true;
        result.delay = random(config.animalTimerMin, config.animalTimerMax);
        return result;
      }
    }

    if (useCancer && this.name === "Krebs-Scan KW") {
      result.allowed = true;
      result.delay = random(config.cancerTimerMin, config.cancerTimerMax);
      return result;
    }

    if (usePeople) {
      const delay = random(config.peopleTimerMin, config.peopleTimerMax);
      if (this.insuredAge <= 60) {
        switch (this.name) {
          case "KV-Voll Selbstständige KW":
            result.allowed = true;
            result.delay = delay;
            return result;
          case "KV-Voll Arbeitnehmer KW":
            result.allowed = this.meta.aboveIncomeLimit;
            result.delay = delay;
            return result;
        }
      }
    }

    return result;
  }

  toString() {
    if (!this.valid) {
      return "Invalid Product";
    }

    return JSON.stringify({
      name: this.name,
      insuredType: this.insuredType,
      insuredAge: this.insuredAge,
      meta: this.meta,
    });
  }
}

function random(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

function isValidTimeOfDay(config) {
  const now = new LocalDate();
  const hh = now.getHours();
  const day = now.getDay();

  // skip on Sunday
  // if (now.getDay() === 0) {
  //   return false;
  // }

  const operationalHours = config.operationalHours[day];
  if (!operationalHours.enabled) {
    return false;
  }

  // skip before 8am and after 8pm
  if (hh < operationalHours.min || hh >= operationalHours.max) {
    return false;
  }

  return true;
}

async function assertValidTimeOfDay(config) {
  if (!isValidTimeOfDay(config)) {
    console.log("invalid time of day, skipping");
    await new Promise((resolve, _reject) => {
      setTimeout(resolve, 500);
    });
    await assertValidTimeOfDay(config);
  }
}

async function checkOffers(config, mutationList, observer) {
  if (
    mutationList.some(
      (m) =>
        m.target.nodeName === "IMG" &&
        m.target.className === "leaflet-tile leaflet-tile-loaded"
    )
  ) {
    observer.disconnect();
    const validOffers = document.querySelectorAll(
      '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]'
    );

    const log = new Log("check");
    log.push(`offers=${validOffers.length}`);

    for (const validOffer of validOffers) {
      const key = JSON.stringify({
        marginLeft: validOffer.style.marginLeft,
        marginRight: validOffer.style.marginRight,
        width: validOffer.style.width,
        height: validOffer.style.height,
        transform: validOffer.style.transform,
      });

      validOffer.click();
      await new Promise(async (resolve, _reject) => {
        setTimeout(async () => {
          const offer = document.querySelector(".leaflet-popup-content a");
          if (offer) {
            log.push(`open=${offer.href}`);
            await chrome.runtime.sendMessage({
              action: "openTab",
              url: offer.href,
            });
          }
          resolve(null);
        }, 200);
      });
    }

    await log.write();
    return true;
  }

  return false;
}

async function browseOffers(config) {
  const log = new Log("browse");

  console.log("logging...");
  const isManaged = await chrome.runtime.sendMessage({
    action: "isManagedTab",
  });
  console.log("is managed", isManaged);
  if (!isManaged) {
    await log.push("unmanaged").write();
    return;
  }

  console.log("check tab");

  for (const offer of document.querySelectorAll("div.browse_list .row")) {
    const link = offer.querySelector(".buy_now a.btn");
    const title = offer.querySelector(".title a");

    if (!link) {
      log.push(`no link`);
      console.log("no link detected, skipping");
      continue;
    }
    if (!title) {
      log.push(`no title`);
      console.log("no title detected, skipping");
      continue;
    }

    log.push(`title=${title.textContent}`);
    const product = new Product(title.textContent);
    if (!product.valid) {
      log.push(`no product`);
      console.log("no product detected, skipping");
      continue;
    }

    log.push(`product=${product.toString()}`);
    console.log(product);
    const { allowed } = product.isAllowed(config);
    if (!allowed) {
      log.push(`not valid`);
      console.log(`not following link: ${title.textContent}`);
      continue;
    }

    log.push(`opened ${link.href}`);
    await chrome.runtime.sendMessage({
      action: "openTab",
      url: link.href,
    });
  }

  await log.write();

  console.log("closing tab");
  await chrome.runtime.sendMessage({ action: "closeCurrentTab" });
}

async function buyOffer(config) {
  const log = new Log("buy");

  const isManaged = await chrome.runtime.sendMessage({
    action: "isManagedTab",
  });
  console.log(isManaged);
  if (!isManaged) {
    await log.push("unmanaged").write();
    return;
  }

  const title = document.querySelector("#page_buy_now h2");
  if (!title) {
    await log.push(`no title`).write();
    console.log("no title detected, skipping");
    return;
  }

  log.push(`title=${title.textContent}`);
  const product = new Product(title.textContent);
  if (!product.valid) {
    await log.push(`no product`).write();
    console.log("no product detected, skipping");
    return;
  }

  log.push(`product=${product.toString()}`);
  console.log(product);
  const { allowed, delay } = product.isAllowed(config);
  if (!allowed) {
    await log.push(`invalid product`).write();
    console.log(`not following link: ${title.textContent}`);
    return;
  }

  // wait before buying
  const delaySeconds = delay * 1000;
  const extraHeadroomSeconds = 2 * 1000; // give extra timeout headroom of 2s for network issues.
  const randomId = (Math.random() + 1).toString(36).substring(7);
  const buyFormBtn = document.querySelector('button[name="action"]')
  if (buyFormBtn) {
    const maybeBuying = await chrome.runtime.sendMessage({
      action: "isBuying",
      key: product.text,
    });
    if (maybeBuying.buying) {
      console.log("already buying insurance");
      await log.push(`already buying ${maybeBuying.id}`).write();
      await chrome.runtime.sendMessage({ action: "closeCurrentTab" });
    } else {
      console.log("buying insurance");
      await log.push(`wait ${delay}s`).push(`id=${randomId}`).write();
      await chrome.runtime.sendMessage({
        action: "markBuying",
        key: product.text,
        id: randomId,
        timeout: Date.now() + delaySeconds + extraHeadroomSeconds,
      });
      setTimeout(() => {
        log
          .push(`bought id=${randomId}`)
          .push(`waited ${delay}s`)
          .push(`title=${title.textContent}`)
          .write()
          .then(() => {
            buyFormBtn.click();
          });
      }, delaySeconds);
    }
  } else {
    await log.push(`no button`).write();
    await chrome.runtime.sendMessage({ action: "closeCurrentTab" });
  }
}

async function waitTill8AM() {
  let log500MsWait = true;
  return new Promise((resolve, _) => {
    function checkAndSet() {
      const date = new LocalDate();
      const hh = date.getHours();
      const mm = date.getMinutes();
      const targetHH = 8; // shorter wait if 7:XX
      const targetMMBefore = 50; // shorter wait if 7:50+

      console.log(`checked ${hh}:${mm}`);
      if (hh === targetHH) {
        console.log(`done`);
        resolve();
      } else if (hh == targetHH - 1) {
        if (mm < targetMMBefore) {
          console.log(`wait 5 minutes`);
          setTimeout(checkAndSet, 5 * 60 * 1000); // sleep for 5 minutes if not 07:50
        } else {
          if (log500MsWait) {
            console.log(`check every 500ms`);
            log500MsWait = false;
          }
          setTimeout(checkAndSet, 500); // sleep for 500 millisecond else
        }
      } else {
        console.log(`wait 30 minutes`);
        setTimeout(checkAndSet, 30 * 60 * 1000); // sleep for 30 minutes if not 1 hr before
      }
    }

    checkAndSet();
  });
}

async function checkTimerOffer() {
  const log = new Log("timer");

  const randomId = (Math.random() + 1).toString(36).substring(7);
  log.push(`id=${randomId}`).push(window.location.href);

  const isManaged = await chrome.runtime.sendMessage({
    action: "isManagedTab",
  });
  if (!isManaged) {
    await log.push("unmanaged").write();
    return;
  }

  const titleElem = document.querySelector(".item_title");
  const title = titleElem ? titleElem.textContent : "<none>";
  const offer = document.querySelector(".buy_now a");
  if (!offer) {
    await log
      .push(`id=${randomId}`)
      .push("wait start")
      .push(`title=${title}`)
      .write();
    await waitTill8AM();
    await log.push(`id=${randomId}`).push("wait done").write();
    setTimeout(() => window.location.reload(), 200);
  } else {
    log
      .push(`id=${randomId}`)
      .push(`timer-open=${offer.href}`)
      .push(`title=${title}`);
    await chrome.runtime.sendMessage({
      action: "openTab",
      url: offer.href,
    });
    await log.write();

    console.log("closing tab");
    await chrome.runtime.sendMessage({ action: "closeCurrentTab" });
  }
}

chrome.runtime.sendMessage({ action: "isEnabled" }).then(async (enabled) => {
  if (!enabled) {
    return;
  }
  const config = await chrome.runtime.sendMessage({ action: "config" });

  if (
    window.location.href ===
    "https://auktion.hansemerkur.de/karte_sofortkauf.html"
  ) {
    if (config.emailMode) {
      // reload every minute
      const randomMinutes = random(20, 50);
      setTimeout(() => window.location.reload(), randomMinutes * 60 * 1000);
    } else {
      await assertValidTimeOfDay(config);

      // Create an observer instance linked to the callback function
      let isChecking = true;
      let checkCount = 0;
      const observer = new MutationObserver(async (mutationList, observer) => {
        if (await checkOffers(config, mutationList, observer)) {
          isChecking = false;
        }
      });

      setInterval(() => {
        if (config.emailMode) {
          return;
        }

        checkCount++;
        if (!isChecking || checkCount > 4) {
          window.location.reload();
        }
      }, 1000);

      // Start observing the target node for configured mutations
      const targetNode = document.querySelector("body");
      observer.observe(targetNode, {
        attributes: true,
        childList: true,
        subtree: true,
      });
    }
  } else if (
    window.location.href.startsWith(
      "https://auktion.hansemerkur.de/item.php?id="
    )
  ) {
    console.log("checking...");
    checkTimerOffer(config);
  } else if (
    window.location.href.startsWith(
      "https://auktion.hansemerkur.de/browse/search/"
    )
  ) {
    browseOffers(config);
  } else if (
    window.location.href.startsWith(
      "https://auktion.hansemerkur.de/buy_now/id/"
    )
  ) {
    buyOffer(config);
  } else if (
    window.location.href.startsWith("https://outlook.office.com/mail") ||
    window.location.href.startsWith("https://outlook.office.com.mcas.ms/mail")
  ) {
    console.log("checking...");
    checkAuctionEmail(config, {});
  }
});

async function checkAuctionEmail(config, visitedUrls) {
  // retry
  const enabled = await chrome.runtime.sendMessage({ action: "isEnabled" });
  const randomRefreshSeconds = random(config.emailRefreshMin, config.emailRefreshMax);
  if (enabled) {
    setTimeout(async () => {
      // const otherEmail = document.querySelector(
      //   '[aria-label^="HanseMerkur AuktionsPlattform"]'
      // );
      // if (otherEmail) {
      //   otherEmail.click()
      // }

      // checkAuctionEmail(config, visitedUrls);
      setTimeout(() => window.location.reload(), 200);
    }, randomRefreshSeconds * 1000);
  }

  async function checkMails(config, visitedUrls) {
    const emails = document.querySelectorAll(
      '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]'
    );

    const log = new Log("email");
    log.push(`emails=${emails.length}`);

    for (const email of emails) {
      email.click();

      await new Promise(async (resolve, _reject) => {
        setTimeout(async () => {
          const auction = document.querySelector("#x_body a");
          if (auction && !visitedUrls[auction.href]) {
            visitedUrls[auction.href] = true;
            // mark as read
            let unreadReadBtn = [...document.querySelectorAll("span")].find((a) =>
              a.textContent.includes("Gelesen/Ungelesen")
            );
            if (unreadReadBtn) {
              unreadReadBtn.click();
            }

            log.push(`open=${auction.href}`);
            await chrome.runtime.sendMessage({
              action: "openTab",
              url: auction.href,
            });
          }
          resolve(null);
        }, 1000);
      });
    }

    await log.write();

    if (!emails.length) {
      setTimeout(async () => {
        await checkMails(config, visitedUrls);
      }, 500);
    }
  }

  await checkMails(config, visitedUrls);
}
