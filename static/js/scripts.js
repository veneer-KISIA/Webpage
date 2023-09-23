
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
  const browseButton = document.getElementById('browseButton');
  const audioFileInput = document.getElementById('audioFile');

  // Function to handle file upload
  async function handleFileUpload(selectedFile) {
    if (!selectedFile) {
      alert('파일을 선택하세요.');
      return;
    }

    const formData = new FormData();
    formData.append("audio", selectedFile);

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const fileName = data.fileName;

        const fileData = { fileName: fileName };
        console.log(data)

        // Send the POST request to '/mask'
        fetch('/mask', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(fileData)
        })
          .then(response => {
            if (!response.ok) {
              throw new Error(`Fail while masking. ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            const stt_text = data.stt_text;
            document.getElementById("stt-text").innerText = stt_text;

            const masked_text = data.ner_text;
            console.log('masked_text:', masked_text);
            document.getElementById("masked-text").innerText = masked_text;

            const maskedFileName = data.fileName;
            if (maskedFileName == null) { // NER server error
              return;
            }
            const maskedFileData = { fileName: maskedFileName };

            // Send the POST request to '/download/masked'
            fetch('/download/masked', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(maskedFileData)
            })
              .then(response => response.json())
              .then(data => {
                const audioData = document.getElementById("#masked-audio").files[0];

                maskAudio(audioData, JSON.stringify(data.stt_result))
                  .then((audioBlob) => {
                    const audioUrl = URL.createObjectURL(audioBlob);

                    let audio = document.createElement("audio");
                    audio.controls = true;
                    audio.src = audioUrl;
                    audioUploadDiv.querySelector("#masked-audio").appendChild(audio);
                  })
                  .catch((error) => {
                    console.error('There was a problem with the fetch operation:', error);
                  });
              })
              .catch(error => {
                console.error('Error:', error);
                return;
              });
          })
          .catch(error => {
            console.error('Error:', error);
            alert(error)
          });
      } else {
        alert(`File upload fail. ${response.status}`);
      }
    } catch (error) {
      console.error('Error while uploading file:', error);
      alert('File upload fail.');
    }
  }

  // Event listeners
  browseButton.addEventListener('click', function () {
    audioFileInput.click();
  });

  audioFileInput.addEventListener('change', async function (event) {
    const selectedFile = event.target.files[0];
    await handleFileUpload(selectedFile);
  });
});
