const sendButton = document.getElementById("sendButton") as HTMLButtonElement;
const addCategotyButton = document.getElementById("loadButton") as HTMLButtonElement;
const themeButton = document.getElementById(
  "theme-button"
) as HTMLButtonElement;
const messageInput = document.getElementById(
  "messageInput"
) as HTMLInputElement;
const chatBox = document.getElementById("chatBox") as HTMLDivElement;
const modelsSelector = document.getElementById("model-select") as HTMLSelectElement;
const categorySelector = document.getElementById("category-select") as HTMLDivElement;
const preloader = document.getElementById("preloader") as HTMLDivElement;
const loadFilesElement = document.getElementById("load-files") as HTMLInputElement;

const selectedCategories: string[] = []

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


const queryGenerate = async () => {
  const resp = await queryApi(
    "POST",
    "generate",
    undefined,
    {
      model: selectedModel,
      query: chatHistory[chatHistory.length - 1].content,
      categories: selectedCategories,

    })

  renderNewBotMessage();
  appendBotMessage(resp["response"], resp["done"]);
}

const addModelName = (model: string) => {
  const newOption = document.createElement("option");
  newOption.value = model;
  newOption.text = `Model ${model}`;
  modelsSelector.appendChild(newOption);
};

const loadModels = async () => {
  const models = await queryApi("GET", "models").catch(console.error) as string[]
  models.forEach(addModelName)
};

const addCategoryLable = (category: string) => {
  const catLabel = document.createElement("label");
  catLabel.className = "toggle-container"
  const chekBox = document.createElement("input");
  chekBox.type = "checkbox"
  chekBox.addEventListener("change", (event: Event) => {
    const target = event.target as HTMLInputElement;
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
  span.className = "toggle-label"
  span.innerHTML = category
  catLabel.appendChild(chekBox)
  catLabel.appendChild(span)
  categorySelector.appendChild(catLabel);
};

const loadCategories = async () => {
  const cats = await queryApi("GET", "categories") as string[]
  categorySelector.innerHTML = ""
  cats.forEach(addCategoryLable)
}

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


type QueryMethod = "GET" | "POST" | "DELETE" | "PUT" | "PATCH";
type BasicTypes = string | number | boolean | null

type Prms = {
  [key: string]: BasicTypes
}

const constructPath = (
  endpoint: string | string[],
  args?: Prms
) => {
  if (Array.isArray(endpoint)) {
    endpoint = endpoint.join("/")
  }
  let path = `${window.location.protocol}//${window.location.host}/api/${endpoint}`;
  // let path = `http://speccy49home.ddns.net:5000/api/${endpoint}`;
  // let path = `http://5.164.181.30:5000/api/${endpoint}`;

  if (args)
    path +=
      "?" +
      Object.entries(args)
        .filter(([k, v]) => v != undefined)
        .map(([k, v]) => `${k}=${encodeURIComponent(v!)}`)
        .join("&");
  return path;
};

const alertError = (message: string) => {
  return (e: any) => {
    e = e as Error
    const cause = e.cause ? (e.cause as { detail: string })["detail"] : null
    alert(message + " " + cause)
  }
}


const queryApi = async (method: QueryMethod, endpoint: string | string[], parameters?: Prms, body?: {} | File | File[], headers?: HeadersInit) => {
  const path = constructPath(endpoint, parameters);
  const init: RequestInit = {
    method: method,
    headers: headers ?? {
      accept: "application/json",
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "true",
    },
  };
  if (["POST", "PUT", "PATCH"].includes(method) && body) {
    if (body instanceof File) {
      const formData = new FormData()
      formData.append("file", body)
      init.body = formData;
    } else if (Array.isArray(body) && body.every(item => item instanceof File)) {
      const formData = new FormData();
      body.forEach((file) => {
        console.log(file)
        formData.append('files', file);
      });
      init.body = formData;
      console.log(init)
    } else {
      init.body = JSON.stringify(body);
    }
  }
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(response.statusText, { cause: await response.json() });
  }
  return await response.json()
}

const addCategory = () => {
  loadFilesElement.click()
}

(() => {
  sendButton.addEventListener("click", () => {
    console.log("CLICK")
    const message = messageInput.value.trim();
    if (!selectedModel) {
      alert("Model was not selected");
      return;
    }
    if (message) {
      const msg: Message = { role: "user", content: message };
      renderMessage(msg);
      addMessage(msg);
      queryGenerate();
    }

    messageInput.value = "";
  });

  addCategotyButton.addEventListener("click", () => {
    addCategory()
  })

  messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendButton.click();
    }
  });

  modelsSelector.addEventListener("change", (e) => {
    const target = e.target as HTMLSelectElement;
    selectedModel = target.value;
    loadModel();
    cleanChatHistory();
    chatBox.innerHTML = "";
  });
  loadFilesElement.addEventListener("change", (e) => {
    const target = e.target as HTMLInputElement;
    const files = target.files;

    if (!files) {
      console.log('No files selected.');
      return;
    }

    if (files.length === 0) {
      console.log('No files selected.');
      return;
    }
    const category = prompt("New category name")
    if (!category) return
    queryApi("POST", "upload_files", { category: category }, Array.from(files), {})
      .then(() => {
        alert("DONE!")
        loadCategories()
        loadFilesElement.innerHTML = ""
      })
      .catch(console.error)
  })



  loadCategories()
  loadModels();
  cleanChatHistory();
})();
