document.addEventListener('DOMContentLoaded', function() {
    const predictionForm = document.getElementById('predictionForm');
    const resultDiv = document.getElementById('result');
    const progressBar = document.querySelector('.progress-bar');
    const probabilitySpan = document.getElementById('probability');
    const messageP = document.getElementById('message');

    // Add input validation for hours and minutes
    const hoursInput = document.getElementById('hours');
    const minutesInput = document.getElementById('minutes');

    // Validate hours input (24-hour format)
    hoursInput.addEventListener('input', function() {
        let value = parseInt(this.value);
        if (!isNaN(value)) {
            if (value < 0) this.value = '0';
            if (value > 23) this.value = '23';
        }
    });

    // Validate minutes input
    minutesInput.addEventListener('input', function() {
        let value = parseInt(this.value);
        if (!isNaN(value)) {
            if (value < 0) this.value = '0';
            if (value > 59) this.value = '59';
        }
    });

    // Format time when moving to next input
    hoursInput.addEventListener('blur', function() {
        if (this.value) {
            this.value = this.value.padStart(2, '0');
        }
    });

    minutesInput.addEventListener('blur', function() {
        if (this.value) {
            this.value = this.value.padStart(2, '0');
        }
    });

    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Format time for submission
        let hours = document.getElementById('hours').value;
        let minutes = document.getElementById('minutes').value;
        
        // Add leading zeros only when submitting
        hours = hours.padStart(2, '0');
        minutes = minutes.padStart(2, '0');
        
        const timeString = `${hours}:${minutes}`;

        // Show loading state
        const submitButton = predictionForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Predicting...';
        
        const formData = {
            team: document.getElementById('team').value,
            opponent: document.getElementById('opponent').value,
            venue: document.querySelector('input[name="venue"]:checked').value,
            time: timeString,
            day: document.getElementById('day').value
        };

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                // Reset progress bar animation
                progressBar.style.width = '0%';
                progressBar.style.transition = 'none';
                progressBar.offsetHeight; // Trigger reflow
                progressBar.style.transition = 'width 1s ease-in-out';

                // Update probability and message
                setTimeout(() => {
                    progressBar.style.width = `${result.probability}%`;
                    
                    // Set color based on probability category
                    if (result.category === 'high') {
                        progressBar.style.backgroundColor = '#28a745';  // Green
                    } else if (result.category === 'medium') {
                        progressBar.style.backgroundColor = '#ffc107';  // Yellow
                    } else {
                        progressBar.style.backgroundColor = '#dc3545';  // Red
                    }
                }, 100);

                probabilitySpan.textContent = result.probability;
                messageP.textContent = result.message;

                // Show result section with fade-in effect
                resultDiv.style.opacity = '0';
                resultDiv.style.display = 'block';
                setTimeout(() => {
                    resultDiv.style.opacity = '1';
                }, 10);

                // Scroll to result
                resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            alert('Error making prediction: ' + error.message);
        } finally {
            // Reset button state
            submitButton.disabled = false;
            submitButton.innerHTML = 'Predict';
        }
    });

    // Prevent selecting same team as opponent
    document.getElementById('team').addEventListener('change', function() {
        const opponent = document.getElementById('opponent');
        Array.from(opponent.options).forEach(option => {
            option.disabled = option.value === this.value;
        });
    });

    document.getElementById('opponent').addEventListener('change', function() {
        const team = document.getElementById('team');
        Array.from(team.options).forEach(option => {
            option.disabled = option.value === this.value;
        });
    });
}); 