"use strict";

const form = document.querySelector("#ask");
const input = document.querySelector("#question");
const messages = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const scroll = document.querySelector("#scroll");
const send = document.querySelector("#send");
const reset = document.querySelector("#reset");

function textElement(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

function message(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const label = role === "user" ? "Вы" : "Покерный тренер";
  const body = textElement("p", text, "message-text");
  article.append(textElement("h2", label), body);
  messages.append(article);
  return { article, body };
}

function showSources(article, sources) {
  if (!sources.length) return;
  const section = document.createElement("details");
  section.className = "sources";
  section.append(textElement("summary", `Источники · ${sources.length}`));
  const list = document.createElement("ul");
  for (const source of sources) {
    const item = document.createElement("li");
    item.append(textElement("strong", `${source.id} · ${source.title}`), textElement("p", source.text));
    list.append(item);
  }
  section.append(list);
  article.append(section);
}

function toLatest() {
  scroll.scrollTop = scroll.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (send.disabled || !question) return;
  send.disabled = true;
  reset.disabled = true;
  welcome.hidden = true;
  message("user", question);
  input.value = "";
  const reply = message("assistant", "Ищу ответ в документах…");
  reply.article.classList.add("pending");
  toLatest();
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    reply.body.textContent = result.answer;
    showSources(reply.article, result.sources);
  } catch (error) {
    reply.body.textContent = error instanceof TypeError
      ? "Не удалось подключиться к серверу. Проверьте запуск и попробуйте снова."
      : error.message;
    reply.article.classList.add("error");
    if (!input.value.trim()) input.value = question;
  } finally {
    reply.article.classList.remove("pending");
    send.disabled = false;
    reset.disabled = false;
    toLatest();
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

for (const button of document.querySelectorAll(".examples button")) {
  button.addEventListener("click", () => {
    input.value = button.textContent.trim();
    input.focus();
  });
}

reset.addEventListener("click", () => {
  messages.replaceChildren();
  welcome.hidden = false;
  input.value = "";
  scroll.scrollTop = 0;
  input.focus();
});

const pageUrl = new URL(window.location.href);
const incomingQuestion = pageUrl.searchParams.get("question");
if (incomingQuestion) {
  input.value = incomingQuestion.slice(0, input.maxLength);
  pageUrl.searchParams.delete("question");
  history.replaceState(null, "", pageUrl);
  if (document.referrer && new URL(document.referrer).href.split(/[?#]/)[0] === new URL("prototype.html", location.href).href) {
    form.requestSubmit();
  }
}
