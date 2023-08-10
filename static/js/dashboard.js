// Helper function to capture image from the video stream
function captureImageFromVideo(video, canvas) {
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/png');
  }

  window.addEventListener('DOMContentLoaded', (event) => {
    // DOM elements
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startButton = document.getElementById('start');
    const captureButton = document.getElementById('capture');
    const submitButton = document.getElementById('submit');
    const checkImageText = document.getElementById('check-image-text');
    const hiddenImageInput = document.getElementById('hiddenImageInput');

    // MediaDevices API is supported
    if (navigator.mediaDevices) {
      const constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };

      // Start the video stream when the start button is clicked
      startButton.addEventListener('click', function() {
        navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
          video.srcObject = stream;
          video.style.display = 'block';
          captureButton.style.display = 'block';
        });
      });

      // Capture the image when the capture button is clicked
      captureButton.addEventListener('click', function() {
        const imageUrl = captureImageFromVideo(video, canvas);
        hiddenImageInput.value = imageUrl;
        checkImageText.style.display = 'block';
        video.style.display = 'none';
        captureButton.style.display = 'none';
      });

      // Submit the form when the submit button is clicked
      submitButton.addEventListener('click', function() {
        /* if (hiddenImageInput.value === '') {
          alert('Please take a picture before submitting.');
          event.preventDefault();
        }*/
      });
    } else {
      alert('Sorry, your browser does not support the MediaDevices API');
    }
  });
