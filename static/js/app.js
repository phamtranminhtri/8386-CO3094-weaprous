const API_URL = `${window.location.origin}/update-broadcast-peer`;
const chatBox = document.getElementById("chat-box");
const input = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");

// Tải tin nhắn
async function loadMessages() {
  try {
    const res = await fetch(API_URL);
    const data = await res.json();
    const msgs = data.msg;
    const username = data.username;

    chatBox.innerHTML = "";
    msgs.forEach((msg) => {
      const div = document.createElement("div");
      div.classList.add("message");
      if (msg.user === username) {
        div.classList.add("me");
      } else {
        div.classList.add("other");
      }

      div.innerHTML = `
        <span class="user">${msg.user}</span>
        <div class="text">${msg.text}</div>
      `;
      chatBox.appendChild(div);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (err) {
    console.error("❌ Lỗi khi tải tin:", err);
  }
}

// Tự động cập nhật tin nhắn mỗi 2 giây
setInterval(loadMessages, 2000);

// Tải lần đầu
loadMessages();