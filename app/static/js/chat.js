/**
 * Global AI Chat & Dual Comparison Workbench
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInputText");
  const sendBtn = document.getElementById("sendChatBtn");
  const tempSlider = document.getElementById("tempSlider");
  const tempValue = document.getElementById("tempValue");
  const clearBtn = document.getElementById("clearChatBtn");
  const exportBtn = document.getElementById("exportChatBtn");

  const singleModeRadio = document.getElementById("singleChatMode");
  const compareModeRadio = document.getElementById("compareChatMode");
  const singleControls = document.getElementById("singleProviderControls");
  const compareControls = document.getElementById("compareProviderControls");
  const singleList = document.getElementById("singleMessagesList");
  const compareList = document.getElementById("compareMessagesList");

  let conversationHistory = [];

  // Temperature display
  if (tempSlider && tempValue) {
    tempSlider.addEventListener("input", () => {
      tempValue.innerText = tempSlider.value;
    });
  }

  // Mode Toggle
  if (singleModeRadio && compareModeRadio) {
    singleModeRadio.addEventListener("change", () => {
      singleControls.classList.remove("d-none");
      compareControls.classList.add("d-none");
      singleList.classList.remove("d-none");
      compareList.classList.add("d-none");
    });

    compareModeRadio.addEventListener("change", () => {
      singleControls.classList.add("d-none");
      compareControls.classList.remove("d-none");
      singleList.classList.add("d-none");
      compareList.classList.remove("d-none");
    });
  }

  // Clear Chat
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      conversationHistory = [];
      singleList.innerHTML = '<div class="text-muted p-3 text-center">Conversation cleared.</div>';
      document.getElementById("p1Output").innerText = "Awaiting run...";
      document.getElementById("p2Output").innerText = "Awaiting run...";
      showToast("Chat cleared.", "info");
    });
  }

  // Export Chat
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(conversationHistory, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `chat_export_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast("Conversation exported as JSON.", "success");
    });
  }

  // Send Message
  if (form && input) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      const isCompareMode = compareModeRadio && compareModeRadio.checked;
      const systemPrompt = document.getElementById("chatSystemPrompt").value;
      const temperature = parseFloat(tempSlider.value);

      if (isCompareMode) {
        // Run Dual Comparison
        executeDualComparison(message, systemPrompt, temperature);
      } else {
        // Run Single Chat
        executeSingleChat(message, systemPrompt, temperature);
      }
      input.value = "";
    });

    // Enter to submit (Shift+Enter for newline)
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form.dispatchEvent(new Event("submit"));
      }
    });
  }

  // --- Single Chat Handler ---
  function executeSingleChat(message, systemPrompt, temperature) {
    appendUserBubble(message);
    conversationHistory.push({ role: "user", content: message });

    const provider = document.getElementById("chatProviderSelect").value;
    const model = document.getElementById("chatModelInput").value.trim();
    const stream = document.getElementById("streamToggle").checked;

    sendBtn.disabled = true;
    const startTime = performance.now();

    if (stream) {
      // SSE Stream
      const assistantBubble = appendAssistantBubble("");
      let fullContent = "";

      fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          provider,
          model: model || undefined,
          system_prompt: systemPrompt,
          temperature,
          messages: conversationHistory,
        })
      }).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function readStream() {
          reader.read().then(({ done, value }) => {
            if (done) {
              sendBtn.disabled = false;
              const elapsed = (performance.now() - startTime).toFixed(0);
              document.getElementById("metricLatency").innerText = `${elapsed} ms`;
              conversationHistory.push({ role: "assistant", content: fullContent });
              return;
            }

            const chunkStr = decoder.decode(value);
            const lines = chunkStr.split("\n\n");
            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.replace("data: ", ""));
                  if (data.chunk) {
                    fullContent += data.chunk;
                    assistantBubble.innerHTML = escapeHtml(fullContent).replace(/\n/g, "<br>");
                    scrollChatToBottom();
                  }
                  if (data.error) {
                    assistantBubble.innerHTML += `<div class="text-danger mt-2">Error: ${escapeHtml(data.error)}</div>`;
                  }
                } catch (e) {}
              }
            }
            readStream();
          }).catch(err => {
            sendBtn.disabled = false;
            assistantBubble.innerHTML += `<div class="text-danger mt-2">Stream failed: ${err.message}</div>`;
          });
        }
        readStream();
      }).catch(err => {
        sendBtn.disabled = false;
        showToast("Error initiating stream: " + err.message, "danger");
      });

    } else {
      // Sync Request
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          provider,
          model: model || undefined,
          system_prompt: systemPrompt,
          temperature,
        })
      })
        .then(r => r.json())
        .then(res => {
          sendBtn.disabled = false;
          if (res.response) {
            appendAssistantBubble(res.response);
            conversationHistory.push({ role: "assistant", content: res.response });
            document.getElementById("metricLatency").innerText = `${res.latency_ms} ms`;
            if (res.tokens) {
              document.getElementById("metricTokens").innerText = res.tokens.total ? `${res.tokens.total} tok` : "--";
            }
          } else {
            appendAssistantBubble("Error: " + (res.error || "Unknown response error"));
          }
          scrollChatToBottom();
        })
        .catch(err => {
          sendBtn.disabled = false;
          appendAssistantBubble("Network Error: " + err.message);
        });
    }
  }

  // --- Dual Comparison Handler ---
  function executeDualComparison(prompt, systemPrompt, temperature) {
    const p1Output = document.getElementById("p1Output");
    const p2Output = document.getElementById("p2Output");
    const p1Metrics = document.getElementById("p1Metrics");
    const p2Metrics = document.getElementById("p2Metrics");

    p1Output.innerText = "Querying Model 1 (Gemini)...";
    p2Output.innerText = "Querying Model 2 (Ollama)...";
    p1Metrics.innerText = "running...";
    p2Metrics.innerText = "running...";
    sendBtn.disabled = true;

    fetch("/api/chat/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        system_prompt: systemPrompt,
        temperature,
        provider1: document.getElementById("compareP1").value,
        model1: document.getElementById("compareM1").value,
        provider2: document.getElementById("compareP2").value,
        model2: document.getElementById("compareM2").value,
      })
    })
      .then(r => r.json())
      .then(data => {
        sendBtn.disabled = false;
        const res1 = data.results.first;
        const res2 = data.results.second;

        p1Output.innerText = res1.success ? res1.content : "Error: " + res1.error;
        p1Metrics.innerText = `${res1.latency_ms} ms | ${res1.tokens || '--'} tok`;

        p2Output.innerText = res2.success ? res2.content : "Error: " + res2.error;
        p2Metrics.innerText = `${res2.latency_ms} ms | ${res2.tokens || '--'} tok`;
      })
      .catch(err => {
        sendBtn.disabled = false;
        p1Output.innerText = "Request failed: " + err.message;
        p2Output.innerText = "Request failed: " + err.message;
      });
  }

  function appendUserBubble(text) {
    const html = `
      <div class="d-flex justify-content-end mb-3">
        <div class="p-3 rounded-3 bg-primary text-white" style="max-width: 80%;">
          ${escapeHtml(text).replace(/\n/g, "<br>")}
        </div>
      </div>
    `;
    singleList.insertAdjacentHTML("beforeend", html);
    scrollChatToBottom();
  }

  function appendAssistantBubble(text) {
    const bubbleId = "bubble_" + Date.now();
    const html = `
      <div class="d-flex gap-3 mb-3">
        <div class="p-2 rounded-circle bg-primary-subtle text-primary d-flex align-items-center justify-content-center" style="width: 36px; height: 36px; flex-shrink: 0;">
          <i class="bi bi-robot"></i>
        </div>
        <div class="p-3 rounded-3 card-custom bg-secondary-subtle bg-opacity-20" style="max-width: 80%;">
          <div id="${bubbleId}">${escapeHtml(text).replace(/\n/g, "<br>")}</div>
        </div>
      </div>
    `;
    singleList.insertAdjacentHTML("beforeend", html);
    scrollChatToBottom();
    return document.getElementById(bubbleId);
  }

  function scrollChatToBottom() {
    const box = document.getElementById("chatMessagesBox");
    if (box) box.scrollTop = box.scrollHeight;
  }
});
