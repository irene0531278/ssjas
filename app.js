let latestAnalysis = null;
let timerSeconds = 25 * 60;
let timerInterval = null;
let timerRunning = false;

const $ = (id) => document.getElementById(id);
const timerDisplay = $("timerDisplay");

function showTimer() {
  const m = Math.floor(timerSeconds / 60).toString().padStart(2, "0");
  const s = (timerSeconds % 60).toString().padStart(2, "0");
  timerDisplay.textContent = `${m}:${s}`;
}

function getFormData() {
  return {
    study_minutes: Number($("study_minutes").value),
    accuracy: Number($("accuracy").value),
    sleep_hours: Number($("sleep_hours").value),
    posture_score: Number($("posture_score").value),
    fatigue: Number($("fatigue").value),
    focus: Number($("focus").value)
  };
}

$("analysisForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  button.textContent = "AI 분석 중...";
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(getFormData())
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "분석에 실패했어.");
    latestAnalysis = result;

    $("recommendedTime").innerHTML = `${result.recommended_minutes}<small>분</small>`;
    $("breakTime").innerHTML = `${result.break_minutes}<small>분</small>`;
    $("predictedScore").innerHTML = `${result.predicted_score}<small>/100</small>`;
    $("feedbackList").innerHTML = "";
    result.messages.forEach((message) => {
      const li = document.createElement("li");
      li.textContent = message;
      $("feedbackList").appendChild(li);
    });
    $("modelNote").textContent = result.model_note;
    $("resultSection").classList.remove("hidden");
    $("saveSection").classList.remove("hidden");
    timerSeconds = result.recommended_minutes * 60;
    showTimer();
    $("timerCaption").textContent = `AI 추천 시간 ${result.recommended_minutes}분으로 설정했어.`;
    $("actualMinutes").value = result.recommended_minutes;
    $("resultSection").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "✦ AI 분석 및 맞춤 계획 생성";
  }
});

$("startTimer").addEventListener("click", () => {
  if (timerRunning) return;
  timerRunning = true;
  timerInterval = setInterval(() => {
    if (timerSeconds > 0) {
      timerSeconds--;
      showTimer();
    } else {
      clearInterval(timerInterval);
      timerRunning = false;
      $("timerCaption").textContent = "학습 시간이 끝났어. 잠시 쉬고 몸 상태를 확인해 봐.";
      alert("학습 시간이 끝났어! 추천된 휴식 시간을 가져 봐.");
    }
  }, 1000);
});

$("pauseTimer").addEventListener("click", () => {
  clearInterval(timerInterval);
  timerRunning = false;
});
$("resetTimer").addEventListener("click", () => {
  clearInterval(timerInterval);
  timerRunning = false;
  timerSeconds = latestAnalysis ? latestAnalysis.recommended_minutes * 60 : 25 * 60;
  showTimer();
});

$("checkinBtn").addEventListener("click", () => {
  const focus = Number($("liveFocus").value);
  const fatigue = Number($("liveFatigue").value);
  const posture = Number($("livePosture").value);
  const messages = [];
  if (focus <= 2) messages.push("집중도가 낮아졌어. 잠시 쉬거나 학습 환경을 정리해 봐.");
  else messages.push("집중도는 괜찮아 보여. 현재 학습 흐름을 이어가 봐.");
  if (fatigue >= 4) messages.push("피로도가 높아. 타이머를 멈추고 충분히 쉬는 게 좋아.");
  if (posture <= 2) messages.push("허리를 편하게 세우고 발을 바닥에 둔 뒤 화면 높이를 조정해 봐.");
  $("liveFeedback").textContent = messages.join(" ");
});

$("saveBtn").addEventListener("click", async () => {
  if (!latestAnalysis) {
    $("saveMessage").textContent = "먼저 AI 분석을 실행해 줘.";
    return;
  }
  const payload = {
    ...latestAnalysis.input,
    predicted_score: latestAnalysis.predicted_score,
    recommended_minutes: latestAnalysis.recommended_minutes,
    actual_minutes: Number($("actualMinutes").value),
    notes: $("notes").value
  };
  try {
    const response = await fetch("/api/session", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "저장 실패");
    $("saveMessage").textContent = result.message + " 페이지를 새로고침하면 기록을 볼 수 있어.";
    $("saveMessage").style.color = "#27966c";
  } catch (error) {
    $("saveMessage").textContent = error.message;
  }
});

async function loadChart() {
  try {
    const response = await fetch("/api/history");
    const rows = await response.json();
    const ordered = rows.reverse();
    const canvas = $("historyChart");
    if (!canvas || typeof Chart === "undefined") return;
    new Chart(canvas, {
      type: "line",
      data: {
        labels: ordered.map(row => row.created_at),
        datasets: [
          {label: "정답률(%)", data: ordered.map(row => row.accuracy), borderWidth: 2, tension: .3},
          {label: "AI 예상 점수", data: ordered.map(row => row.predicted_score), borderWidth: 2, tension: .3}
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {y: {beginAtZero: true, max: 100}},
        plugins: {legend: {position: "bottom"}}
      }
    });
  } catch (error) {
    console.error("그래프 로딩 오류:", error);
  }
}
showTimer();
loadChart();
