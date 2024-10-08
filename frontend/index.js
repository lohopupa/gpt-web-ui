"use strict";
var __awaiter =
  (this && this.__awaiter) ||
  function (thisArg, _arguments, P, generator) {
    function adopt(value) {
      return value instanceof P
        ? value
        : new P(function (resolve) {
            resolve(value);
          });
    }
    return new (P || (P = Promise))(function (resolve, reject) {
      function fulfilled(value) {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      }
      function rejected(value) {
        try {
          step(generator["throw"](value));
        } catch (e) {
          reject(e);
        }
      }
      function step(result) {
        result.done
          ? resolve(result.value)
          : adopt(result.value).then(fulfilled, rejected);
      }
      step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
  };
var _a;
const sendButton = document.getElementById("sendButton");
const addCategotyButton = document.getElementById("loadButton");
const themeButton = document.getElementById("theme-button");
const messageInput = document.getElementById("messageInput");
const chatBox = document.getElementById("chatBox");
const modelsSelector = document.getElementById("model-select");
const categorySelector = document.getElementById("category-select");
const preloader = document.getElementById("preloader");
const loadFilesElement = document.getElementById("load-files");
const selectedCategories = [];
const getNextTheme = () => {
  var _a;
  const theme =
    (_a = localStorage.getItem("theme")) !== null && _a !== void 0
      ? _a
      : "light";
  return theme == "dark" ? "light" : "dark";
};
const applyTheme = (theme) => {
  document.body.classList.toggle("dark-theme", theme == "dark");
  localStorage.setItem("theme", theme);
  themeButton.innerHTML = getNextTheme() + " theme";
};
const theme =
  (_a = localStorage.getItem("theme")) !== null && _a !== void 0 ? _a : "dark";
applyTheme(theme);
themeButton.addEventListener("click", () => applyTheme(getNextTheme()));
const chatHistory = [];
const cleanChatHistory = () => {
  chatHistory.length = 0;
  chatHistory.push({
    role: "system",
    content:
      "Ты - ChatGPT, большая языковая модель. Пиши ответы только на русском языке",
  });
};
let selectedModel = undefined;
const renderChat = () => {
  chatBox.innerHTML = "";
  chatHistory.filter((c) => c.role != "system").forEach(renderMessage);
};
const renderMessage = (msg) => {
  const messageElement = document.createElement("div");
  messageElement.className = "message " + msg.role;
  messageElement.textContent = msg.content;
  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight;
};
const addMessage = (msg) => {
  chatHistory.push(msg);
};
const renderNewBotMessage = () => {
  const messageElement = document.createElement("div");
  messageElement.className = "message assistant";
  messageElement.textContent = "";
  messageElement.id = "active_message_box";
  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight;
  return messageElement;
};
const appendBotMessage = (text, done) => {
  let messageBox = document.getElementById("active_message_box");
  if (!messageBox) {
    messageBox = renderNewBotMessage();
  }
  messageBox.innerHTML += text;
  if (done) {
    addMessage({ content: messageBox.innerHTML, role: "assistant" });
    messageBox.id = "";
  }
};
const queryGenerate = () =>
  __awaiter(void 0, void 0, void 0, function* () {
    const resp = yield queryApi("POST", "generate", undefined, {
      model: selectedModel,
      query: chatHistory[chatHistory.length - 1].content,
      categories: selectedCategories,
    });
    renderNewBotMessage();
    appendBotMessage(resp["response"], resp["done"]);
  });
const addModelName = (model) => {
  const newOption = document.createElement("option");
  newOption.value = model;
  newOption.text = `Model ${model}`;
  modelsSelector.appendChild(newOption);
};
const loadModels = () =>
  __awaiter(void 0, void 0, void 0, function* () {
    const models = yield queryApi("GET", "models").catch(console.error);
    models.forEach(addModelName);
  });
const addCategoryLable = (category) => {
  const catLabel = document.createElement("label");
  catLabel.className = "toggle-container";
  const chekBox = document.createElement("input");
  chekBox.type = "checkbox";
  chekBox.addEventListener("change", (event) => {
    const target = event.target;
    if (target.checked) {
      if (!selectedCategories.includes(category)) {
        selectedCategories.push(category);
      }
    } else {
      const index = selectedCategories.indexOf(category);
      if (index !== -1) {
        selectedCategories.splice(index, 1);
      }
    }
  });
  // TODO: Add id
  const span = document.createElement("span");
  span.className = "toggle-label";
  span.innerHTML = category;
  catLabel.appendChild(chekBox);
  catLabel.appendChild(span);
  categorySelector.appendChild(catLabel);
};
const loadCategories = () =>
  __awaiter(void 0, void 0, void 0, function* () {
    const cats = yield queryApi("GET", "categories");
    categorySelector.innerHTML = "";
    cats.forEach(addCategoryLable);
  });
const loadModel = () => {
  preloader.style.display = "inline-block";
  messageInput.disabled = true;
  sendButton.disabled = true;
  // queryChat(false).then(() => {
  preloader.style.display = "none";
  messageInput.disabled = false;
  sendButton.disabled = false;
  // });
};
const constructPath = (endpoint, args) => {
  if (Array.isArray(endpoint)) {
    endpoint = endpoint.join("/");
  }
  let path = `${window.location.protocol}//${window.location.host}/api/${endpoint}`;
  // let path = `http://speccy49home.ddns.net:5000/api/${endpoint}`;
  // let path = `http://5.164.181.30:5000/api/${endpoint}`;
  if (args)
    path +=
      "?" +
      Object.entries(args)
        .filter(([k, v]) => v != undefined)
        .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
        .join("&");
  return path;
};
const alertError = (message) => {
  return (e) => {
    e = e;
    const cause = e.cause ? e.cause["detail"] : null;
    alert(message + " " + cause);
  };
};
const queryApi = (method, endpoint, parameters, body, headers) =>
  __awaiter(void 0, void 0, void 0, function* () {
    const path = constructPath(endpoint, parameters);
    const init = {
      method: method,
      headers:
        headers !== null && headers !== void 0
          ? headers
          : {
              accept: "application/json",
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "true",
            },
    };
    if (["POST", "PUT", "PATCH"].includes(method) && body) {
      if (body instanceof File) {
        const formData = new FormData();
        formData.append("file", body);
        init.body = formData;
      } else if (
        Array.isArray(body) &&
        body.every((item) => item instanceof File)
      ) {
        const formData = new FormData();
        body.forEach((file) => {
          console.log(file);
          formData.append("files", file);
        });
        init.body = formData;
        console.log(init);
      } else {
        init.body = JSON.stringify(body);
      }
    }
    const response = yield fetch(path, init);
    if (!response.ok) {
      throw new Error(response.statusText, { cause: yield response.json() });
    }
    return yield response.json();
  });
const addCategory = () => {
  loadFilesElement.click();
};
(() => {
  sendButton.addEventListener("click", () => {
    console.log("CLICK");
    const message = messageInput.value.trim();
    if (!selectedModel) {
      alert("Model was not selected");
      return;
    }
    if (message) {
      const msg = { role: "user", content: message };
      renderMessage(msg);
      addMessage(msg);
      queryGenerate();
    }
    messageInput.value = "";
  });
  addCategotyButton.addEventListener("click", () => {
    addCategory();
  });
  messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendButton.click();
    }
  });
  modelsSelector.addEventListener("change", (e) => {
    const target = e.target;
    selectedModel = target.value;
    loadModel();
    cleanChatHistory();
    chatBox.innerHTML = "";
  });
  loadFilesElement.addEventListener("change", (e) => {
    const target = e.target;
    const files = target.files;
    if (!files) {
      console.log("No files selected.");
      return;
    }
    if (files.length === 0) {
      console.log("No files selected.");
      return;
    }
    const category = prompt("New category name");
    if (!category) return;
    queryApi(
      "POST",
      "upload_files",
      { category: category },
      Array.from(files),
      {}
    )
      .then(() => {
        alert("DONE!");
        loadCategories();
        loadFilesElement.innerHTML = "";
      })
      .catch(console.error);
  });
  loadCategories();
  loadModels();
  cleanChatHistory();
})();
//# sourceMappingURL=index.js.map
