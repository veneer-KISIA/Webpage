
window.addEventListener('DOMContentLoaded', event => {

  // Navbar shrink function
  var navbarShrink = function () {
      const navbarCollapsible = document.body.querySelector('#mainNav');
      if (!navbarCollapsible) {
          return;
      }
      if (window.scrollY === 0) {
          navbarCollapsible.classList.remove('navbar-shrink')
      } else {
          navbarCollapsible.classList.add('navbar-shrink')
      }

  };

  // Shrink the navbar 
  navbarShrink();

  // Shrink the navbar when page is scrolled
  document.addEventListener('scroll', navbarShrink);

  // Activate Bootstrap scrollspy on the main nav element
  const mainNav = document.body.querySelector('#mainNav');
  if (mainNav) {
      new bootstrap.ScrollSpy(document.body, {
          target: '#mainNav',
          rootMargin: '0px 0px -40%',
      });
  };

  // Collapse responsive navbar when toggler is visible
  const navbarToggler = document.body.querySelector('.navbar-toggler');
  const responsiveNavItems = [].slice.call(
      document.querySelectorAll('#navbarResponsive .nav-link')
  );
  responsiveNavItems.map(function (responsiveNavItem) {
      responsiveNavItem.addEventListener('click', () => {
          if (window.getComputedStyle(navbarToggler).display !== 'none') {
              navbarToggler.click();
          }
      });
  });

});

document.addEventListener('DOMContentLoaded', function () {
// Browse 버튼 클릭 시 파일 입력 클릭 트리거
const browseButton = document.getElementById('browseButton');
const audioFileInput = document.getElementById('audioFile');

browseButton.addEventListener('click', function () {
  audioFileInput.click();
});

// 파일 입력 상태 변화(파일 선택) 감지
audioFileInput.addEventListener('change', async function (event) {
  const selectedFile = event.target.files[0];

  // 파일이 선택되지 않았을 경우 처리
  if (!selectedFile) {
    alert('파일을 선택하세요.');
    return;
  }

  // FormData 객체를 사용하여 파일 업로드 준비
  const formData = new FormData();
  formData.append("audio", selectedFile);

  try {
    // 서버로 파일 업로드 요청 보내기
    const response = await fetch("/upload/stt", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      // 업로드 성공 시 처리
      const data = await response.json();

      // 받아온 데이터를 처리하고 필요한 작업 수행
      // 예: 결과 표시, 추가 작업 등
      const content = data.message + ` (${data.fileName})`;
      document.getElementById("stt-text").innerText = data.stt_text;
      // audioUploadDiv.querySelector("#stt-text").innerText = data.stt_text;
      // audioUploadDiv.querySelector("#stt-result").innerText = JSON.stringify(data.stt_result);

      raw_text = data.stt_text;
      masked_text = data.ner_text;
      console.log('masked_text:', masked_text);
      document.getElementById("masked-text").innerText = masked_text;

      data.stt_result.text = masked_text;
      console.log("data.stt_result", data.stt_result);

      const audioData = document.getElementById("#masked-audio").files[0];

      const audioBlob = maskAudio(audioData, JSON.stringify(data.stt_result)).then((audioBlob) => {

        console.log("audioBlob", audioBlob.length);
        console.log("audioBlob", audioBlob);
        const audioUrl = URL.createObjectURL(audioBlob);

        let audio = document.createElement("audio");
        audio.controls = true;
        audio.src = audioUrl;
        audioUploadDiv.querySelector("#masked-audio").appendChild(audio);
      })
      .catch((error) => {
        console.error('There was a problem with the fetch operation:', error);
      });

      alert('파일 업로드 완료!');
    } else {
      // 업로드 실패 시 처리
      alert('파일 업로드 실패.');
    }
  } catch (error) {
    console.error('파일 업로드 중 오류 발생:', error);
    alert('파일 업로드 중 오류가 발생했습니다.');
  }
});
});