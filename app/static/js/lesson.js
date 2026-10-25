/**
 * Lesson Page Interactive Logic: Lab runner, quiz evaluator, completion toggle
 */

document.addEventListener("DOMContentLoaded", () => {
  initLessonCompletion();
  initLabRunner();
  initQuizEvaluator();
});

// --- Lesson Completion Toggle ---
function initLessonCompletion() {
  const btn = document.getElementById("markCompleteBtn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const lessonId = btn.getAttribute("data-lesson-id");
    btn.disabled = true;

    fetch(`/api/lessons/${lessonId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    })
      .then(r => r.json())
      .then(data => {
        btn.disabled = false;
        if (data.success) {
          const isDone = data.is_completed;
          btn.className = isDone ? "btn btn-sm btn-success d-inline-flex align-items-center gap-1" : "btn btn-sm btn-outline-success d-inline-flex align-items-center gap-1";
          document.getElementById("markCompleteIcon").className = isDone ? "bi bi-check-circle-fill" : "bi bi-check-circle";
          document.getElementById("markCompleteText").innerText = isDone ? "Completed" : "Mark Complete";
          showToast(isDone ? "Lesson marked as complete! 🎉" : "Lesson marked as incomplete.", isDone ? "success" : "info");
        }
      })
      .catch(err => {
        btn.disabled = false;
        showToast("Error updating lesson progress.", "danger");
      });
  });
}

// --- Lab Runner & Parameter Execution ---
function initLabRunner() {
  const runBtn = document.getElementById("runLabBtn");
  const resetBtn = document.getElementById("resetLabParamsBtn");
  const paramsEditor = document.getElementById("labParamsEditor");
  const providerSelect = document.getElementById("labProviderSelect");
  const consoleEl = document.getElementById("actualOutputConsole");
  const timerEl = document.getElementById("labExecutionTimer");

  if (!runBtn || !paramsEditor || !consoleEl) return;

  const defaultParams = paramsEditor.value;

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      paramsEditor.value = defaultParams;
      showToast("Parameters reset to lesson defaults.", "info");
    });
  }

  runBtn.addEventListener("click", () => {
    const labId = runBtn.getAttribute("data-lab-id");
    let parsedParams = {};

    try {
      parsedParams = JSON.parse(paramsEditor.value.trim());
    } catch (e) {
      showToast("Invalid JSON in parameters editor: " + e.message, "danger");
      return;
    }

    // Attach provider choice
    if (providerSelect) {
      parsedParams.provider = providerSelect.value;
    }

    // UI Loading State
    runBtn.disabled = true;
    document.getElementById("runLabIcon").className = "spinner-border spinner-border-sm";
    document.getElementById("runLabText").innerText = "Executing...";
    consoleEl.innerText = "Executing lab handler on server...\nConnecting to AI provider...";
    if (timerEl) timerEl.innerText = "";

    const startTime = performance.now();

    fetch(`/api/labs/${labId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsedParams)
    })
      .then(r => r.json())
      .then(res => {
        runBtn.disabled = false;
        document.getElementById("runLabIcon").className = "bi bi-play-fill fs-5";
        document.getElementById("runLabText").innerText = "9. Run Example";

        const elapsed = (performance.now() - startTime).toFixed(0);
        if (timerEl) timerEl.innerText = `Duration: ${res.execution_time_ms || elapsed} ms`;

        if (res.status === "success" || !res.error) {
          consoleEl.innerText = typeof res.output === "object" 
            ? JSON.stringify(res.output, null, 2) 
            : String(res.output);
          showToast("Lab executed successfully!", "success");
        } else {
          consoleEl.innerText = "Execution Error:\n" + (res.error || JSON.stringify(res.output, null, 2));
          showToast("Execution returned an error.", "warning");
        }

        // Activate actual tab
        const actualTab = document.getElementById("actual-tab");
        if (actualTab) {
          bootstrap.Tab.getOrCreateInstance(actualTab).show();
        }
      })
      .catch(err => {
        runBtn.disabled = false;
        document.getElementById("runLabIcon").className = "bi bi-play-fill fs-5";
        document.getElementById("runLabText").innerText = "9. Run Example";
        consoleEl.innerText = "Network / Server Error:\n" + err.message;
        showToast("Server connection failed.", "danger");
      });
  });
}

// --- Knowledge-Check Quiz Evaluator ---
function initQuizEvaluator() {
  const submitBtn = document.getElementById("submitQuizBtn");
  const form = document.getElementById("lessonQuizForm");
  const resultMsg = document.getElementById("quizResultMsg");
  const scoreBadge = document.getElementById("quizScoreBadge");

  if (!submitBtn || !form) return;

  submitBtn.addEventListener("click", () => {
    const formData = new FormData(form);
    const answers = {};

    for (const [key, val] of formData.entries()) {
      if (key.startsWith("quiz_")) {
        const qId = key.replace("quiz_", "");
        answers[qId] = parseInt(val, 10);
      }
    }

    const questionBlocks = document.querySelectorAll(".quiz-question-block");
    if (Object.keys(answers).length < questionBlocks.length) {
      showToast("Please answer all questions before submitting.", "warning");
      return;
    }

    const lessonId = document.getElementById("markCompleteBtn").getAttribute("data-lesson-id");
    submitBtn.disabled = true;
    submitBtn.innerText = "Grading...";

    fetch(`/api/lessons/${lessonId}/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers })
    })
      .then(r => r.json())
      .then(res => {
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit Quiz Answers";

        if (res.success) {
          // Update score badge
          if (scoreBadge) {
            scoreBadge.innerText = `Score: ${res.score}/${res.total} (${res.percentage}%)`;
            scoreBadge.className = res.passed ? "badge bg-success" : "badge bg-warning text-dark";
          }

          if (resultMsg) {
            resultMsg.innerText = res.passed 
              ? `Passed! ${res.percentage}%. Great job! Lesson marked complete.` 
              : `Score: ${res.percentage}%. Review the feedback below and try again.`;
            resultMsg.className = res.passed ? "small fw-bold text-success" : "small fw-bold text-warning";
          }

          // Render per-question feedback
          res.feedback.forEach(fb => {
            const block = document.getElementById(`question_block_${fb.question_id}`);
            if (!block) return;

            // Reset options classes
            block.querySelectorAll(".quiz-option-card").forEach(el => {
              el.classList.remove("correct", "incorrect");
            });

            // Highlight chosen
            if (fb.user_choice !== null) {
              const chosenLabel = document.getElementById(`label_q_${fb.question_id}_${fb.user_choice}`);
              if (chosenLabel) {
                chosenLabel.classList.add(fb.is_correct ? "correct" : "incorrect");
              }
            }

            // Highlight correct
            const correctLabel = document.getElementById(`label_q_${fb.question_id}_${fb.correct_index}`);
            if (correctLabel) {
              correctLabel.classList.add("correct");
            }

            // Show explanation
            const expBox = document.getElementById(`explanation_${fb.question_id}`);
            if (expBox) {
              expBox.innerText = "Explanation: " + fb.explanation;
              expBox.classList.remove("d-none");
            }
          });

          if (res.passed) {
            showToast("Quiz Passed! Lesson automatically marked complete. 🎉", "success");
            const completeBtn = document.getElementById("markCompleteBtn");
            if (completeBtn) {
              completeBtn.className = "btn btn-sm btn-success d-inline-flex align-items-center gap-1";
              document.getElementById("markCompleteIcon").className = "bi bi-check-circle-fill";
              document.getElementById("markCompleteText").innerText = "Completed";
            }
          } else {
            showToast("Quiz submitted. Review the explanations below.", "info");
          }
        } else {
          showToast(res.error || "Quiz grading error.", "danger");
        }
      })
      .catch(err => {
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit Quiz Answers";
        showToast("Failed to submit quiz.", "danger");
      });
  });
}
