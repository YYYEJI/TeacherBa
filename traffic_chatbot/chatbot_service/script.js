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

// ✅ 메시지 전송 시: 바로 고민 중 → 3초 후 응답
sendBtn.addEventListener("click", () => {
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user");
  input.value = "";

  // UX 로딩 메시지: 고민 중
  const loadingMessage = addMessage("바선생이 고민 중이에요... 🤔", "bot");

  setTimeout(() => {
    const reply = generateFakeReply(message);
    chatBox.removeChild(loadingMessage); // 이전 고민 중 메시지 삭제
    addMessage(reply, "bot");
  }, 3000);
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

  return row; // → 로딩 메시지 삭제를 위해 반환
}

function getTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

function generateFakeReply(input) {
  if (input.includes("비보호")) {
    return "비보호 좌회전은 녹색 신호에서 보행자와 충돌하지 않을 때 조심스럽게 좌회전하는 거예요.";
  }
  if (input.includes("깜빡이는 어느시점에 켜야돼?")) {
    return "차선 변경 30m 전에는 꼭 깜빡이를 켜주세요! 다른 운전자에게 신호를 주는 중요한 예절이에요.";
  }
  return "죄송해요, 해당 내용은 아직 학습하지 못했어요. 다른 질문이 있다면 언제든지 물어보세요!";
}

// ✅ Shift + Enter → 줄바꿈 / Enter → 메시지 전송
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendBtn.click();
  }
});

