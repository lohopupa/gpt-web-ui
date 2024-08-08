"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var _a;
const sendButton = document.getElementById("sendButton");
const addCategotyButton = document.getElementById("loadButton");
const themeButton = document.getElementById("theme-button");
const messageInput = document.getElementById("messageInput");
const chatBox = document.getElementById("chatBox");
const selector = document.getElementById("model-select");
const preloader = document.getElementById("preloader");
const getNextTheme = () => {
    var _a;
    const theme = (_a = localStorage.getItem("theme")) !== null && _a !== void 0 ? _a : "light";
    return theme == "dark" ? "light" : "dark";
};
const applyTheme = (theme) => {
    document.body.classList.toggle("dark-theme", theme == "dark");
    localStorage.setItem("theme", theme);
    themeButton.innerHTML = getNextTheme() + " theme";
};
const theme = (_a = localStorage.getItem("theme")) !== null && _a !== void 0 ? _a : "dark";
applyTheme(theme);
themeButton.addEventListener("click", () => applyTheme(getNextTheme()));
// const API_PORT = 11433;
// const API_HOST = "5.164.175.65";
// const apiBaseUrl = `http://${API_HOST}:${API_PORT}/api`;
// // const apiBaseUrl = `${window.location.protocol}//${window.location.host.split(":")[0]}:${API_PORT}/api`;
const chatHistory = [];
const cleanChatHistory = () => {
    chatHistory.length = 0;
    chatHistory.push({
        role: "system",
        content: "Ты - ChatGPT, большая языковая модель. Пиши ответы только на русском языке",
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
const queryChat = (useOutput) => __awaiter(void 0, void 0, void 0, function* () {
    var _a, _b, _c;
    const apiUrl = `/chat`;
    const headers = { "Content-Type": "application/json" };
    try {
        const response = yield fetch(apiUrl, {
            method: "POST",
            body: JSON.stringify({
                model: selectedModel,
                messages: chatHistory,
                stream: true,
            }),
            headers: headers,
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        if (!useOutput)
            return;
        renderNewBotMessage();
        const reader = (_a = response.body) === null || _a === void 0 ? void 0 : _a.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        if (reader) {
            while (true) {
                const { done, value } = yield reader.read();
                if (done) {
                    break;
                }
                buffer += decoder.decode(value, { stream: true });
                let lineEnd;
                while ((lineEnd = buffer.indexOf("\n")) >= 0) {
                    const line = buffer.substring(0, lineEnd).trim();
                    buffer = buffer.substring(lineEnd + 1);
                    try {
                        const data = JSON.parse(line);
                        if (data.message != undefined) {
                            appendBotMessage(data.message.content, (_b = data.done) !== null && _b !== void 0 ? _b : false);
                        }
                        if (data.done) {
                            console.log("Complete response received.");
                            return;
                        }
                    }
                    catch (error) {
                        console.error("Error decoding JSON:", error);
                    }
                }
            }
        }
        if (buffer.length > 0) {
            try {
                const data = JSON.parse(buffer);
                if (data.response) {
                    appendBotMessage(data.message.content, (_c = data.done) !== null && _c !== void 0 ? _c : false);
                }
            }
            catch (error) {
                console.error("Error decoding JSON:", buffer, error);
            }
        }
    }
    catch (error) {
        console.error("Request failed:", error);
    }
});
const queryChatGenerate = () => __awaiter(void 0, void 0, void 0, function* () {
    const apiUrl = `/generate`;
    const headers = { "Content-Type": "application/json" };
    try {
        const response = yield fetch(apiUrl, {
            method: "POST",
            body: JSON.stringify({
                model: "llama3.1:8b",
                prompt: chatHistory[chatHistory.length - 1].content,
                stream: false,
            }),
            headers: headers,
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const resp_json = yield response.json();
        renderNewBotMessage();
        appendBotMessage(resp_json["response"], resp_json["done"]);
    }
    catch (e) {
        console.error(e);
    }
});
const addModelName = (model) => {
    const newOption = document.createElement("option");
    newOption.value = model;
    newOption.text = `Model ${model}`;
    selector.appendChild(newOption);
};
const loadModels = () => __awaiter(void 0, void 0, void 0, function* () {
    try {
        const resp = yield fetch(`/tags`, {
            headers: { "Content-Type": "application/json" },
        });
        const resp_json = yield resp.json();
        resp_json.models.forEach((r) => {
            addModelName(r.model);
        });
    }
    catch (error) {
        console.error("Failed to load models:", error);
    }
});
const loadModel = () => {
    preloader.style.display = "inline-block";
    messageInput.disabled = true;
    sendButton.disabled = true;
    queryChat(false).then(() => {
        preloader.style.display = "none";
        messageInput.disabled = false;
        sendButton.disabled = false;
    });
};
(() => {
    sendButton.addEventListener("click", () => {
        console.log("CLICK");
        const message = messageInput.value.trim();
        // if (!selectedModel) {
        //   alert("Model was not selected");
        //   return;
        // }
        if (message) {
            const msg = { role: "user", content: message };
            renderMessage(msg);
            addMessage(msg);
            queryChatGenerate();
        }
        messageInput.value = "";
    });
    addCategotyButton.addEventListener("click", () => {
        console.log("AAAAA");
        queryApi("GET", "test").then(console.log);
    });
    messageInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendButton.click();
        }
    });
    selector.addEventListener("change", (e) => {
        const target = e.target;
        selectedModel = target.value;
        loadModel();
        cleanChatHistory();
        chatBox.innerHTML = "";
    });
    loadModels();
    cleanChatHistory();
})();
const constructPath = (endpoint, args) => {
    if (Array.isArray(endpoint)) {
        endpoint = endpoint.join("/");
    }
    let path = `${window.location.protocol}//${window.location.host}/api/${endpoint}`;
    // let path = `http://localhost:8000/api/${endpoint}`;
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
const queryApi = (method, endpoint, parameters, body, headers) => __awaiter(void 0, void 0, void 0, function* () {
    const path = constructPath(endpoint, parameters);
    const init = {
        method: method,
        headers: headers !== null && headers !== void 0 ? headers : {
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
        }
        else {
            init.body = JSON.stringify(body);
        }
    }
    const response = yield fetch(path, init);
    if (!response.ok) {
        throw new Error(response.statusText, { cause: yield response.json() });
    }
    return yield response.json();
});
//# sourceMappingURL=index.js.map