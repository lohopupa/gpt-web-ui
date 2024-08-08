const sendButton = document.getElementById("sendButton") as HTMLButtonElement;
const themeButton = document.getElementById(
  "theme-button"
) as HTMLButtonElement;
const messageInput = document.getElementById(
  "messageInput"
) as HTMLInputElement;
const chatBox = document.getElementById("chatBox") as HTMLDivElement;
const selector = document.getElementById("model-select") as HTMLSelectElement;
const preloader = document.getElementById("preloader") as HTMLDivElement;

const getNextTheme = () => {
  const theme = localStorage.getItem("theme") ?? "light";
  return theme == "dark" ? "light" : "dark";
};

const applyTheme = (theme: string) => {
  document.body.classList.toggle("dark-theme", theme == "dark");
  localStorage.setItem("theme", theme);
  themeButton.innerHTML = getNextTheme() + " theme";
};

const theme = localStorage.getItem("theme") ?? "dark";
applyTheme(theme);

themeButton.addEventListener("click", () => applyTheme(getNextTheme()));

type Role = "system" | "user" | "assistant";
type Message = { role: Role; content: string };
type ChatHistory = Message[];

const API_PORT = 11433;
const API_HOST = "5.164.175.65";
const apiBaseUrl = `http://${API_HOST}:${API_PORT}/api`;
// const apiBaseUrl = `${window.location.protocol}//${window.location.host.split(":")[0]}:${API_PORT}/api`;

const chatHistory: ChatHistory = [];

const cleanChatHistory = () => {
  chatHistory.length = 0;
  chatHistory.push({
    role: "system",
    content:
      "Ты - ChatGPT, большая языковая модель. Пиши ответы только на русском языке",
  });
};

let selectedModel: string | undefined = undefined;

const renderChat = () => {
  chatBox.innerHTML = "";
  chatHistory.filter((c) => c.role != "system").forEach(renderMessage);
};

const renderMessage = (msg: Message) => {
  const messageElement = document.createElement("div");
  messageElement.className = "message " + msg.role;
  messageElement.textContent = msg.content;
  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight;
};

const addMessage = (msg: Message) => {
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

const appendBotMessage = (text: string, done: boolean) => {
  let messageBox = document.getElementById(
    "active_message_box"
  ) as HTMLDivElement;
  if (!messageBox) {
    messageBox = renderNewBotMessage();
  }
  messageBox.innerHTML += text;
  if (done) {
    addMessage({ content: messageBox.innerHTML, role: "assistant" });
    messageBox.id = "";
  }
};

const queryChat = async (useOutput: boolean) => {
  const apiUrl = `${apiBaseUrl}/chat`;
  const headers = { "Content-Type": "application/json" };

  try {
    const response = await fetch(apiUrl, {
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
    if (!useOutput) return;

    renderNewBotMessage();

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
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
              appendBotMessage(data.message.content, data.done ?? false);
            }
            if (data.done) {
              console.log("Complete response received.");
              return;
            }
          } catch (error) {
            console.error("Error decoding JSON:", error);
          }
        }
      }
    }

    if (buffer.length > 0) {
      try {
        const data = JSON.parse(buffer);
        if (data.response) {
          appendBotMessage(data.message.content, data.done ?? false);
        }
      } catch (error) {
        console.error("Error decoding JSON:", buffer, error);
      }
    }
  } catch (error) {
    console.error("Request failed:", error);
  }
};


const queryChatGenerate = async () => {
  const apiUrl = `${apiBaseUrl}/generate`;
  const headers = { "Content-Type": "application/json" };

  try {
    const response = await fetch(apiUrl, {
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
    const resp_json = await response.json()

    renderNewBotMessage();
    appendBotMessage(resp_json["response"], resp_json["done"]);
  }
  catch (e) {
    console.error(e)
  }
}

const addModelName = (model: string) => {
  const newOption = document.createElement("option");
  newOption.value = model;
  newOption.text = `Model ${model}`;
  selector.appendChild(newOption);
};

const loadModels = async () => {
  try {
    const resp = await fetch(`${apiBaseUrl}/tags`, {
      headers: { "Content-Type": "application/json" },
    });
    const resp_json = await resp.json();
    resp_json.models.forEach((r: { model: string }) => {
      addModelName(r.model);
    });
  } catch (error) {
    console.error("Failed to load models:", error);
  }
};

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
    const message = messageInput.value.trim();
    // if (!selectedModel) {
    //   alert("Model was not selected");
    //   return;
    // }
    if (message) {
      const msg: Message = { role: "user", content: message };
      renderMessage(msg);
      addMessage(msg);
      queryChatGenerate();
    }

    messageInput.value = "";
  });

  messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendButton.click();
    }
  });

  selector.addEventListener("change", (e) => {
    const target = e.target as HTMLSelectElement;
    selectedModel = target.value;
    loadModel();
    cleanChatHistory();
    chatBox.innerHTML = "";
  });

  loadModels();
  cleanChatHistory();
})();
