const chatBox = document.getElementById("chatBox");
const sendBtn = document.getElementById("sendBtn");
const input = document.getElementById("userInput");

// ✅ 페이지 진입 시 1초 후 첫 인사 출력
window.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    addMessage(
      "안녕하세요! 초보운전자를 위한 운전 멘토 바선생입니다. 운전 중 궁금한 점이나 헷갈리는 상황이 있다면 언제든지 물어보세요!",
      "bot"
    );
  }, 600);
});

sendBtn.addEventListener("click", async () => {
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user");
  input.value = "";

  const loadingMessage = addMessage("바선생이 고민 중이에요... 🤔", "bot");

  try {
    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    chatBox.removeChild(loadingMessage);
    addMessage(data.response, "bot");
  } catch (error) {
    chatBox.removeChild(loadingMessage);
    addMessage("서버에 문제가 발생했어요. 나중에 다시 시도해주세요!", "bot");
    console.error(error);
  }
});

function addMessage(text, type) {
  const row = document.createElement("div");
  row.className = `chat-row ${type}`;

  const avatar = document.createElement("img");
  avatar.className = type === "bot" ? "avatar-left" : "avatar-right";
  avatar.src = type === "bot" ? "mentor.png" : "driver.png";
  avatar.alt = type;

  const wrapper = document.createElement("div");
  wrapper.className = `chat-bubble ${type}`;

  const bubble = document.createElement("div");
  bubble.textContent = text;

  const meta = document.createElement("div");
  meta.className = "chat-meta";
  meta.textContent = getTime();

  wrapper.appendChild(bubble);
  wrapper.appendChild(meta);

  row.appendChild(avatar);
  row.appendChild(wrapper);

  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;

  return row;
}

function getTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendBtn.click();
  }
});
