(function () {
  const script = document.createElement("script");
  script.src = "https://cdn.botframework.com/botframework-webchat/latest/webchat.js";
  document.head.appendChild(script);
function applyChatStyles() {
  const existing = document.getElementById("custom-webchat-style");
  if (existing) {
    existing.remove();
  }

  const style = document.createElement("style");
  style.id = "custom-webchat-style";
  style.innerHTML = `
    #webchat,
    #webchat * {
      font-family: "Segoe UI", Arial, sans-serif !important;
      color: #555 !important;
    }

    #webchat p,
    #webchat li,
    #webchat span,
    #webchat div,
    #webchat a {
      font-family: "Segoe UI", Arial, sans-serif !important;
      font-size: 15px !important;
      line-height: 1.4 !important;
      color: #555 !important;
      font-weight: 400 !important;
    }

    #webchat a {
      text-decoration: underline !important;
    }

    #webchat ol,
    #webchat ul {
      margin: 6px 0 !important;
      padding-left: 20px !important;
    }

    #webchat li {
      margin: 2px 0 !important;
    }
  `;

  document.head.appendChild(style);
}

function showToast(message, type = "success") {
  const toast = document.getElementById("toast");

  toast.innerText = message;
  toast.className = "toast show " + type;

  setTimeout(() => {
    toast.className = "toast hidden";
  }, 3000);
}

  const button = document.createElement("button");
  button.innerHTML = "💬";
  button.style.position = "fixed";
  button.style.bottom = "20px";
  button.style.right = "20px";
  button.style.width = "60px";
  button.style.height = "60px";
  button.style.borderRadius = "50%";
  button.style.border = "none";
  button.style.background = "#e53935";
  button.style.color = "white";
  button.style.fontSize = "28px";
  button.style.cursor = "pointer";
  button.style.boxShadow = "0 4px 12px rgba(0,0,0,0.2)";
  button.style.zIndex = "9999";
  document.body.appendChild(button);

  const chatWrapper = document.createElement("div");
  chatWrapper.style.position = "fixed";
  chatWrapper.style.bottom = "90px";
  chatWrapper.style.right = "20px";
  chatWrapper.style.width = "360px";
  chatWrapper.style.height = "500px";
  chatWrapper.style.background = "white";
  chatWrapper.style.borderRadius = "16px";
  chatWrapper.style.boxShadow = "0 8px 24px rgba(0,0,0,0.2)";
  chatWrapper.style.overflow = "hidden";
  chatWrapper.style.display = "none";
  chatWrapper.style.flexDirection = "column";
  chatWrapper.style.zIndex = "9999";
  document.body.appendChild(chatWrapper);

  const header = document.createElement("div");
  header.style.height = "60px";
  header.style.background = "#e53935";
  header.style.color = "white";
  header.style.display = "flex";
  header.style.alignItems = "center";
  header.style.justifyContent = "space-between";
  header.style.padding = "0 16px";
  header.style.fontFamily = "Arial, sans-serif";
  header.style.fontSize = "18px";
  header.style.fontWeight = "bold";
  header.innerText = "Chat podrška";

  const closeBtn = document.createElement("button");
  closeBtn.innerHTML = "✕";
  closeBtn.style.background = "transparent";
  closeBtn.style.border = "none";
  closeBtn.style.color = "white";
  closeBtn.style.fontSize = "20px";
  closeBtn.style.cursor = "pointer";
  closeBtn.style.marginLeft = "auto";

  header.appendChild(closeBtn);
  chatWrapper.appendChild(header);

  const chatContainer = document.createElement("div");
  chatContainer.id = "webchat";
  chatContainer.style.flex = "1";
  chatContainer.style.minHeight = "0";
  chatWrapper.appendChild(chatContainer);

  let initialized = false;

async function initChat() {
  const res = await fetch("/api/token");
  const data = await res.json();

  const styleSet = window.WebChat.createStyleSet({
    hideUploadButton: true,
    avatarSize: 40,
    bubbleBorderRadius: 12,
    bubbleMaxWidth: 280,
    sendBoxBorderTop: "1px solid #eee",
    backgroundColor: "#ffffff",
    showAvatarInGroup: true
  });

  styleSet.textContent = {
    ...styleSet.textContent,
    fontFamily: '"Segoe UI", Arial, sans-serif',
    fontSize: '15px',
    lineHeight: '1.4',
    color: '#222'
  };

  styleSet.markdownText = {
    ...styleSet.markdownText,
    fontFamily: '"Segoe UI", Arial, sans-serif',
    fontSize: '15px',
    lineHeight: '1.4',
    color: '#555'
  };

  window.WebChat.renderWebChat(
    {
      directLine: window.WebChat.createDirectLine({
        token: data.token,
        domain: "https://europe.directline.botframework.com/v3/directline"
      }),
      userID: "user1",
      username: "TI",
      styleSet,
      styleOptions: {
        botAvatarImage: window.location.origin + "/banner.png",
        botAvatarInitials: "IT",
        userAvatarInitials: "TI",
        avatarSize: 40,
        showAvatarInGroup: true
      }
    },
    chatContainer
  );

  applyChatStyles();
}
  button.addEventListener("click", async () => {
    if (chatWrapper.style.display === "none") {
      chatWrapper.style.display = "flex";
      if (!initialized) {
        if (window.WebChat) {
          await initChat();
          initialized = true;
        } else {
          script.onload = async () => {
            await initChat();
            initialized = true;
          };
        }
      }
    } else {
      chatWrapper.style.display = "none";
    }
  });

  closeBtn.addEventListener("click", () => {
    chatWrapper.style.display = "none";
  });

document.addEventListener("DOMContentLoaded", () => {
  const openChatBtn = document.getElementById("openChat");
  const syncBtn = document.getElementById("syncDocs");

  if (openChatBtn) {
    openChatBtn.addEventListener("click", () => {
      button.click();
    });
  }

  if (syncBtn) {
    syncBtn.addEventListener("click", async () => {
      syncBtn.disabled = true;
      const originalText = syncBtn.innerText;
      syncBtn.innerText = "⟳ Sync u toku...";
      syncBtn.style.transform = "scale(0.97)";
      syncBtn.style.opacity = "0.85";
     

      try {
        const res = await fetch("/api/sync-docs", {
          method: "POST"
        });

        const data = await res.json();

        if (data.success) {
          showToast(
          "Sync uspešan ✔\n" +
          "Obrađeni: " + data.result.processed.length +
          " | Preskočeni: " + data.result.skipped.length
        );
        } else {
          showToast("Greška: " + data.message, "error");
        }
      } catch (err) {
        showToast("Grešk prilikom synca ");
      } finally {
        syncBtn.disabled = false;
        syncBtn.innerText = originalText;
        syncBtn.style.transform = "";
        syncBtn.style.opacity = "";
        
      }
    });
  }
})})();