const toggleBtn = document.querySelector("#on-off");
const animalInput = document.querySelector("#animals");
const peopleInput = document.querySelector("#people");
const emailModeInput = document.querySelector("#email-mode");
const emailRefreshMinInput = document.querySelector("#email-refresh-min");
const emailRefreshMaxInput = document.querySelector("#email-refresh-max");
const cancerInput = document.querySelector("#cancer");
const animalTimerMinInput = document.querySelector("#animals-timer-min");
const peopleTimerMinInput = document.querySelector("#people-timer-min");
const cancerTimerMinInput = document.querySelector("#cancer-timer-min");
const animalTimerMaxInput = document.querySelector("#animals-timer-max");
const peopleTimerMaxInput = document.querySelector("#people-timer-max");
const cancerTimerMaxInput = document.querySelector("#cancer-timer-max");
const logsBtn = document.querySelector("#logs");
const removeLogsBtn = document.querySelector("#remove-logs");
const watchTimer = document.querySelector("#watch");

function renderWatchButton(isManaged) {
  if (isManaged) {
    watchTimer.textContent = "Stop";
    watchTimer.style = "background-color: lightsalmon;";
  } else {
    watchTimer.textContent = "Start";
    watchTimer.style = "background-color: lightgreen;";
  }
}

function getOperationalHours() {
  const operationalHours = {};
  for (let i = 0; i < 7; i++) {
    operationalHours[i] = {
      enabled: document.querySelector(`#operation-hours-${i}-enabled`).checked,
      min: parseInt(document.querySelector(`#operation-hours-${i}-min`).value),
      max: parseInt(document.querySelector(`#operation-hours-${i}-max`).value),
    };
  }
}

async function renderButton() {
  const enabled = (await chrome.storage.sync.get(["enabled"])).enabled;
  if (enabled) {
    toggleBtn.textContent = "Disable";
    toggleBtn.style = "background-color: lightsalmon;";
    animalInput.disabled = true;
    peopleInput.disabled = true;
    cancerInput.disabled = true;
    emailModeInput.disabled = false;
    emailRefreshMinInput.disabled = true;
    emailRefreshMaxInput.disabled = true;

    const operationalHours = {};
    for (let i = 0; i < 7; i++) {
      const inputEnabled = document.querySelector(
        `#operation-hours-${i}-enabled`
      );
      const inputMin = document.querySelector(`#operation-hours-${i}-min`);
      const inputMax = document.querySelector(`#operation-hours-${i}-max`);

      operationalHours[i] = {
        enabled: inputEnabled.checked,
        min: parseInt(inputMin.value),
        max: parseInt(inputMax.value),
      };

      inputEnabled.disabled = true;
      inputMin.disabled = true;
      inputMax.disabled = true;
    }

    // record settings
    const config = {
      people: peopleInput.checked,
      animals: animalInput.checked,
      cancer: cancerInput.checked,
      emailMode: emailModeInput.checked,
      emailRefreshMin: parseInt(emailRefreshMinInput.value),
      emailRefreshMax: parseInt(emailRefreshMaxInput.value),
      peopleTimerMin: parseInt(peopleTimerMinInput.value),
      peopleTimerMax: parseInt(peopleTimerMaxInput.value),
      animalTimerMin: parseInt(animalTimerMinInput.value),
      animalTimerMax: parseInt(animalTimerMaxInput.value),
      cancerTimerMin: parseInt(cancerTimerMinInput.value),
      cancerTimerMax: parseInt(cancerTimerMaxInput.value),
      operationalHours,
    };
    await chrome.storage.sync.set({ config });
  } else {
    toggleBtn.textContent = "Enable";
    toggleBtn.style = "background-color: lightgreen;";
    animalInput.disabled = false;
    peopleInput.disabled = false;
    cancerInput.disabled = false;
    emailModeInput.disabled = false;
    emailRefreshMinInput.disabled = false;
    emailRefreshMaxInput.disabled = false;

    for (let i = 0; i < 7; i++) {
      document.querySelector(`#operation-hours-${i}-enabled`).disabled = false;
      document.querySelector(`#operation-hours-${i}-min`).disabled = false;
      document.querySelector(`#operation-hours-${i}-max`).disabled = false;
    }
  }

  renderWatchButton(
    await chrome.runtime.sendMessage({
      action: "isManagedTab",
      tabId: currentTab.id,
    })
  );
}

async function getCurrentTab() {
  return new Promise((resolve, _) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      resolve(tabs[0]);
    });
  });
}
// async function renderCheckbox() {
//   const animals = (await chrome.storage.sync.get(["animals"]))?.animals;
//   animalInput.checked = !!animals;
//   const people = (await chrome.storage.sync.get(["people"]))?.people;
//   peopleInput.checked = !!people;
// }

async function renderConfig() {
  const config = Object.assign(
    {
      people: true,
      animals: true,
      cancer: true,
      peopleTimerMin: 1,
      peopleTimerMax: 2,
      animalTimerMin: 1,
      animalTimerMax: 2,
      cancerTimerMin: 4,
      cancerTimerMax: 7,
      emailMode: true,
      emailRefreshMin: 2 * 60,
      emailRefreshMax: 5 * 60,
      operationalHours: {
        0: {
          enabled: true,
          min: 8,
          max: 20,
        },
        1: {
          enabled: true,
          min: 8,
          max: 20,
        },
        2: {
          enabled: true,
          min: 8,
          max: 20,
        },
        3: {
          enabled: true,
          min: 8,
          max: 20,
        },
        4: {
          enabled: true,
          min: 8,
          max: 20,
        },
        5: {
          enabled: true,
          min: 8,
          max: 20,
        },
        6: {
          enabled: true,
          min: 8,
          max: 20,
        },
      },
    },
    (await chrome.storage.sync.get(["config"]))?.config
  );

  console.log(config);

  animalInput.checked = config.animals;
  peopleInput.checked = config.people;
  cancerInput.checked = config.cancer;
  emailModeInput.checked = config.emailMode;
  emailRefreshMinInput.value = config.emailRefreshMin;
  emailRefreshMaxInput.value = config.emailRefreshMax;
  peopleTimerMinInput.value = config.peopleTimerMin;
  peopleTimerMaxInput.value = config.peopleTimerMax;
  animalTimerMinInput.value = config.animalTimerMin;
  animalTimerMaxInput.value = config.animalTimerMax;
  cancerTimerMinInput.value = config.cancerTimerMin;
  cancerTimerMaxInput.value = config.cancerTimerMax;
  for (let i = 0; i < 7; i++) {
    document.querySelector(`#operation-hours-${i}-enabled`).checked =
      config.operationalHours[i].enabled;
    document.querySelector(`#operation-hours-${i}-min`).value =
      config.operationalHours[i].min;
    document.querySelector(`#operation-hours-${i}-max`).value =
      config.operationalHours[i].max;
  }
}

const currentTab = await getCurrentTab();
await renderConfig();
await renderButton();
toggleBtn.addEventListener("click", () => {
  chrome.storage.sync.get(["enabled"]).then((result) => {
    const newValue = !result.enabled;
    chrome.storage.sync.set({ enabled: newValue }).then(() => renderButton());
  });
});
// animalInput.addEventListener("change", (e) => {
//   chrome.storage.sync
//     .set({ animals: e.target.checked })
//     .then(() => renderCheckbox());
// });
// peopleInput.addEventListener("change", (e) => {
//   chrome.storage.sync
//     .set({ people: e.target.checked })
//     .then(() => renderCheckbox());
// });
logsBtn.addEventListener("click", () => {
  chrome.storage.local.get(["logs"]).then((result) => {
    console.log(result.logs);
    if (result.logs) {
      const win = window.open(
        "",
        "logs",
        "toolbar=no,location=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=780,height=200,top=" +
          (screen.height - 400) +
          ",left=" +
          (screen.width - 840)
      );
      win.document.body.innerHTML = `<pre>${result.logs.join("\n")}</pre>`;
      console.log(logs);
    }
  });
});
removeLogsBtn.addEventListener("click", () => {
  chrome.storage.local.remove(["logs"]);
});

watchTimer.addEventListener("click", () => {
  console.log(currentTab);
  if (
    !currentTab.url.startsWith("https://auktion.hansemerkur.de/item.php?id=")
  ) {
    alert("cannot watch this page");
    return;
  }

  chrome.runtime
    .sendMessage({
      action: "isManagedTab",
      tabId: currentTab.id,
    })
    .then((isManaged) => {
      chrome.runtime.sendMessage({
        action: isManaged ? "unmanageTab" : "manageTab",
        tabId: currentTab.id,
      });
      if (!isManaged) {
        chrome.tabs.reload(currentTab.id);
      }
      return !isManaged;
    })
    .then(renderWatchButton);
});
