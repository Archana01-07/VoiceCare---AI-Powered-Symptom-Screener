// Add this to your existing script.js
document.addEventListener('DOMContentLoaded', () => {
  // Animate elements on page load
  gsap.from('.navbar', { duration: 0.8, y: -50, opacity: 0, ease: 'power3.out' });
  gsap.from('.symptom-form', { duration: 0.8, y: 20, opacity: 0, delay: 0.2, ease: 'power3.out' });
  
  // Add floating animation to microphone button
  const micBtn = document.getElementById('micBtn');
  if (micBtn) {
    gsap.to(micBtn, {
      y: -5,
      duration: 1.5,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut'
    });
  }
});

// Enhanced speech recognition with visual feedback
// Replace the existing micBtn event listener with this improved version:
document.getElementById("micBtn")?.addEventListener("click", () => {
    const micBtn = document.getElementById("micBtn");
    const symptomsInput = document.getElementById("symptoms");
    const originalContent = micBtn.innerHTML;
    
    // Visual feedback
    micBtn.innerHTML = '<i class="fas fa-microphone-alt"></i> Listening...';
    micBtn.disabled = true;
    
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";
    
    // Timeout handling
    const timeout = setTimeout(() => {
        recognition.stop();
        showFeedback(micBtn, '<i class="fas fa-hourglass-end"></i> Timeout', 'var(--warning)');
    }, 8000); // 8-second timeout

    recognition.onstart = () => {
        symptomsInput.placeholder = "Speak now...";
    };

    recognition.onresult = (event) => {
        clearTimeout(timeout);
        const transcript = event.results[0][0].transcript;
        symptomsInput.value = transcript;
        showFeedback(micBtn, '<i class="fas fa-check-circle"></i> Success', 'var(--success)');
    };

    recognition.onerror = (event) => {
        clearTimeout(timeout);
        console.error("Speech recognition error", event.error);
        let message = '<i class="fas fa-exclamation-circle"></i> Error';
        if (event.error === 'no-speech') {
            message = '<i class="fas fa-microphone-slash"></i> No speech';
        }
        showFeedback(micBtn, message, 'var(--warning)');
    };

    recognition.onend = () => {
        clearTimeout(timeout);
        symptomsInput.placeholder = "Describe your symptoms...";
        micBtn.disabled = false;
    };

    recognition.start();

    function showFeedback(element, html, color) {
        element.innerHTML = html;
        element.style.backgroundColor = color;
        setTimeout(() => {
            element.innerHTML = originalContent;
            element.style.backgroundColor = '';
        }, 2000);
    }
});
// Replace the existing symptom form handler with this:
// Replace the existing symptom form handler with this:
document.getElementById("symptomForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const symptoms = document.getElementById("symptoms").value;
    const resultDiv = document.getElementById("result");
    
    if (!symptoms.trim()) {
        resultDiv.innerHTML = '<div class="alert error">Please describe your symptoms</div>';
        return;
    }

    resultDiv.innerHTML = '<div class="loading">Analyzing symptoms...</div>';
    
    try {
        const response = await fetch("/check", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ symptoms: symptoms })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        let html = `<div class="result-card">
            <div class="severity-tag ${data.severity === 'severe' ? 'severe' : 'mild'}">
                ${data.severity.toUpperCase()}
            </div>`;
        
        if (data.type === "home_care") {
            html += `<h3>Home Care Recommendation</h3>
                    <p>${data.advice}</p>
                    <div class="remedy-box">
                        <h4>💊 Recommended Remedies:</h4>
                        <ul>${data.remedies.map(r => `<li>${r}</li>`).join('')}</ul>
                    </div>`;
            
            if (data.exercises.length > 0) {
                html += `<div class="exercise-box">
                          <h4>🧘 Helpful Exercises:</h4>
                          <ul>${data.exercises.map(e => `<li>${e}</li>`).join('')}</ul>
                        </div>`;
            }
        } 
        else {
            html += `<h3>Urgent Care Needed</h3>
                    <p>${data.advice}</p>
                    <div class="clinic-info">
                        <h4>🏥 Recommended Clinic:</h4>
                        <p><strong>${data.clinic.name}</strong></p>
                        <p>📍 ${data.clinic.location}</p>
                        <p>📞 ${data.clinic.phone}</p>
                        ${data.clinic.hours ? `<p>⏰ ${data.clinic.hours}</p>` : ''}
                    </div>`;
        }
        
        html += "</div>";
        resultDiv.innerHTML = html;
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert error">
            <i class="fas fa-exclamation-circle"></i> Error: ${error.message}
        </div>`;
        console.error("Error:", error);
    }
});