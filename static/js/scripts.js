window.addEventListener("DOMContentLoaded", (event) => {
  // Navbar shrink function
  var navbarShrink = function () {
    const navbarCollapsible = document.body.querySelector("#mainNav");
    if (!navbarCollapsible) {
      return;
    }
    if (window.scrollY === 0) {
      navbarCollapsible.classList.remove("navbar-shrink");
    } else {
      navbarCollapsible.classList.add("navbar-shrink");
    }
  };

  // Shrink the navbar
  navbarShrink();

  // Shrink the navbar when page is scrolled
  document.addEventListener("scroll", navbarShrink);

  // Activate Bootstrap scrollspy on the main nav element
  const mainNav = document.body.querySelector("#mainNav");
  if (mainNav) {
    new bootstrap.ScrollSpy(document.body, {
      target: "#mainNav",
      rootMargin: "0px 0px -40%",
    });
  }

  // Collapse responsive navbar when toggler is visible
  const navbarToggler = document.body.querySelector(".navbar-toggler");
  const responsiveNavItems = [].slice.call(
    document.querySelectorAll("#navbarResponsive .nav-link")
  );
  responsiveNavItems.map(function (responsiveNavItem) {
    responsiveNavItem.addEventListener("click", () => {
      if (window.getComputedStyle(navbarToggler).display !== "none") {
        navbarToggler.click();
      }
    });
  });
});

// document 로드 후 실행
function onLoad() {
  const browseButton = document.getElementById("browseButton");
  const audioFileInput = document.getElementById("audioFile");

  // Event listeners
  browseButton.addEventListener("click", function () {
    audioFileInput.click();
  });

  audioFileInput.addEventListener("change", async function (event) {
    const selectedFile = event.target.files[0];
    await handleFileUpload(selectedFile);
  });
}

document.addEventListener("DOMContentLoaded", onLoad);

async function handleFileUpload(selectedFile) {
  // 파일 업로드
  const data = await uploadAudioFile(selectedFile);

  // 오디오 마스킹
  const response_data = await maskAudioFile(data.fileName);

  // STT 결과 표시
  showSTTResult(response_data.stt_text, response_data.ner_text);

  // 마스킹된 오디오 파일 다운로드
  const audioBlob = await downloadMaskedAudioFile(response_data.fileName);

  // 오디오 플레이어 생성
  createAudioPlayer(audioBlob);

  //API 결과 표시
  const moderation_data = response_data.moderation;
  showAPIresult(moderation_data);
}

async function uploadAudioFile(selectedFile) {
  if (!selectedFile) {
    alert("파일을 선택하세요.");
    return;
  }

  const formData = new FormData();
  formData.append("audio", selectedFile);
  const response = await fetch("/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`파일 업로드 실패 (/upload) ${response.status}`);
  }

  return await response.json();
}

async function maskAudioFile(fileName) {
  const fileData = { fileName: fileName };

  // Send the POST request to '/mask'
  const response = await fetch("/mask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(fileData),
  });

  if (!response.ok) {
    alert("마스킹 오류: mp3파일 확인")
    throw new Error(`마스킹 오류 (/mask) ${response.status}`);
  }

  return await response.json();
}

function showSTTResult(stt_text, ner_text) {
  document.getElementById("stt-text").innerText = stt_text;

  const masked_text = ner_text;
  console.log("masked_text:", masked_text);
  document.getElementById("masked-text").innerText = masked_text;
}

async function downloadMaskedAudioFile(fileName) {
  if (fileName == null) {
    throw new Error(`NER 서버 에러. ${response.status}`);
  }
  const maskedFileData = { fileName: fileName };

  // Send the POST request to '/download/masked'
  const response = await fetch("/download/masked", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(maskedFileData),
  });

  if (!response.ok) {
    throw new Error(
      `마스킹된 오디오 다운로드 실패 (/download/masked) ${response.status}`
    );
  }

  return await response.blob();
}

function createAudioPlayer(audioBlob) {
  const audioUrl = URL.createObjectURL(audioBlob);

  let audio = document.createElement("audio");
  audio.controls = true;
  audio.src = audioUrl;
  document.getElementById("masked-audio").innerText = "";
  document.getElementById("masked-audio").appendChild(audio);
}

function showAPIresult(moderation_data) {
  const progressBarsContainer = document.getElementById("api-result");
  
  if (moderation_data == null) {
    const text = document.createElement("text");
    text.textContent = 'API Error';
    progressBarsContainer.appendChild(text);
  }
  else {
    moderation_data.forEach((item) => {
      const textSpan = document.createElement("span");
      textSpan.textContent = `${item.name}: ${(item.confidence * 100).toFixed()}%`;
  
      const container = document.createElement("div");
      container.classList.add("progress-container");
  
      const progressBar = document.createElement("progress");
      progressBar.value = item.confidence;
      progressBar.max = 1;
  
      container.appendChild(textSpan);
      container.appendChild(progressBar);
  
      progressBarsContainer.appendChild(container);
    });
  }
  
}
