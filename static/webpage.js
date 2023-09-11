// 파일 다운로드
const fileDownloadDiv = document.getElementById("file-download");
const downloadButton = fileDownloadDiv.querySelector("#downloadButton");
downloadButton.addEventListener("click", async () => {
  const fileNameInput = fileDownloadDiv.querySelector("#fileNameInput").value;
  if (!fileNameInput) {
    alert("파일 이름을 입력하세요.");
    return;
  }

  try {
    const response = await fetch(`/download/${fileNameInput}`);
    const blob = await response.blob();

    const a = document.createElement("a");
    const url = window.URL.createObjectURL(blob);
    a.href = url;
    a.download = fileNameInput;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    alert("파일 다운로드 에러:", error);
  }
});

// 오디오 관련 변수
let mediaRecorder;
let audioChunks = [];
let isPaused = false;

// 오디오 관련 버튼
const audioUploadDiv = document.getElementById("audio-upload");
const startRecordButton = audioUploadDiv.querySelector("#startRecord");
const pauseRecordButton = audioUploadDiv.querySelector("#pauseRecord");
const stopRecordButton = audioUploadDiv.querySelector("#stopRecord");
const uploadButton = audioUploadDiv.querySelector("#upload");
const messages = audioUploadDiv.querySelector("#messages");

// 결과 로그 출력 함수
function log(msg) {
  const newMessageDiv = document.createElement("div");
  newMessageDiv.textContent = msg;
  messages.appendChild(newMessageDiv);
}

// 녹음 시작 버튼 클릭 이벤트
startRecordButton.addEventListener("click", async () => {
  try {
    audioChunks.length = 0; // 이전의 audio chunks를 모두 삭제
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
    });
    mediaRecorder = new MediaRecorder(stream);

    // 녹음기가 데이터를 받을 때마다 audioChunks에 저장
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    });

    // mediaRecorder.ondataavailable = (event) => {
    //   audioChunks.push(event.data); // 오디오 데이터가 취득될 때마다 배열에 담아둔다.
    // };

    // 녹음기가 녹음을 멈추면 audioChunks를 하나의 Blob으로 만들고 오디오 플레이어에 추가
    mediaRecorder.addEventListener("stop", () => {
      mediaRecorder.stop();
      const audioBlob = new Blob(audioChunks, { type: "audio/*" });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.controls = true;

      fileName = audioUploadDiv.querySelector("#file-name").value;
      playerlist = audioUploadDiv.querySelector("#audio-player");

      // 기존 자식 요소 삭제
      while (playerlist.firstChild) {
        playerlist.removeChild(playerlist.firstChild);
      }

      const audioContainer = document.createElement("div");
      audioContainer.appendChild(audio);

      const fileNameElement = document.createElement("span");
      fileNameElement.textContent = ` (${fileName})`;
      audioContainer.appendChild(fileNameElement);
      playerlist.appendChild(audioContainer);

      uploadButton.disabled = false;
    });

    mediaRecorder.start();
    startRecordButton.disabled = true;
    pauseRecordButton.disabled = false;
    stopRecordButton.disabled = false;
  } catch (error) {
    log("마이크로폰 관련 에러:", error);
  }
});

// 일시정지 버튼 클릭 이벤트
pauseRecordButton.addEventListener("click", () => {
  if (!isPaused) {
    mediaRecorder.pause();
    isPaused = true;
    pauseRecordButton.textContent = "재개";
  } else {
    mediaRecorder.resume();
    isPaused = false;
    pauseRecordButton.textContent = "일시정지";
  }
});

// 녹음 정지 버튼 클릭 이벤트
stopRecordButton.addEventListener("click", () => {
  mediaRecorder.stop();
  startRecordButton.disabled = false;
  pauseRecordButton.disabled = true;
  stopRecordButton.disabled = true;
});

// 파일 전송 버튼 클릭 이벤트
uploadButton.addEventListener("click", async () => {
  // 파일 이름 가져오기
  fileNameInput = audioUploadDiv.querySelector("#file-name");
  const audioFile = audioUploadDiv.querySelector("#audio").files[0];
  const audioFileName = audioFile.name;
  console.log(audioFileName);

  // 브라우저 녹음문제로 임시 비활성화
  // const audioBlob = new Blob(audioChunks, {type: "audio/*"});
  const formData = new FormData();
  // formData.append("audio", audioBlob, fileNameInput.value);
  formData.append("audio", audioFile, audioFileName);

  let content = "";
  try {
    const response = await fetch("/upload/stt", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    content = data.message + ` (${data.fileName})`;
    audioUploadDiv.querySelector("#stt-text").innerText = data.stt_text;
    audioUploadDiv.querySelector("#stt-result").innerText = JSON.stringify(
      data.stt_result
    );
  } catch (error) {
    const newMessageDiv = document.createElement("div");
    content = fileNameInput.value + " 파일 업로드 에러: " + error;
  } finally {
    log(content);
  }
});

// audioMask 버튼 클릭 이벤트
const maskAudioDiv = document.getElementById("mask-audio");
const maskAudioButton = maskAudioDiv.querySelector("#maskAudio");

maskAudioButton.addEventListener("click", async () => {
  const audio = maskAudioDiv.querySelector("#audio").files[0];
  const data = maskAudioDiv.querySelector("#data").value;

  const formData = new FormData();
  formData.append("audio", audio);
  formData.append("data", data);

  let content = "";
  try {
    const response = await fetch("/upload/mask-audio", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      let audio = document.createElement("audio");
      audio.controls = true;
      audio.src = audioUrl;
      maskAudioDiv.querySelector("#masked-audio").appendChild(audio);
    }
  } catch (error) {
    content = "오디오 마스킹 에러: " + error;
  } finally {
    log(content);
  }
});

const copyButton = audioUploadDiv.querySelector("#copy-stt");
copyButton.addEventListener("click", function () {
  const range = document.createRange();
  const targetDiv = audioUploadDiv.querySelector("#stt-result");
  let tmpInput = document.createElement("input");
  tmpInput.value = targetDiv.innerText;
  document.body.appendChild(tmpInput);
  tmpInput.select();
  document.execCommand("copy");
  document.body.removeChild(tmpInput);
  alert("내용이 복사되었습니다.");
});
