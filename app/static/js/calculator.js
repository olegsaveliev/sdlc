// Set timestamp
document.getElementById('timestamp').textContent = new Date().toLocaleString();

// Track selected operation
let selectedOperation = null;

function selectOperation(operation) {
    selectedOperation = operation;

    // Remove active class from all operation buttons
    document.querySelectorAll('.btn-add, .btn-subtract, .btn-multiply, .btn-divide').forEach(btn => {
        btn.classList.remove('active');
    });

    // Add active class to selected button
    const buttonClass = `.btn-${operation}`;
    document.querySelector(buttonClass).classList.add('active');
}

function createSaluteAnimation(x, y) {
    const container = document.createElement('div');
    container.className = 'salute-container';
    document.body.appendChild(container);

    const emojis = ['🎉', '✨', '⭐', '🌟', '💫', '🎊'];
    const particleCount = 12;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'salute-particle';
        particle.textContent = emojis[Math.floor(Math.random() * emojis.length)];

        const angle = (Math.PI * 2 * i) / particleCount;
        const distance = 100 + Math.random() * 50;
        const tx = Math.cos(angle) * distance;
        const ty = Math.sin(angle) * distance;
        const rotate = Math.random() * 360;

        particle.style.left = x + 'px';
        particle.style.top = y + 'px';
        particle.style.setProperty('--tx', tx + 'px');
        particle.style.setProperty('--ty', ty + 'px');
        particle.style.setProperty('--rotate', rotate + 'deg');

        container.appendChild(particle);
    }

    setTimeout(() => {
        container.remove();
    }, 1000);
}

async function calculateResult() {
    if (!selectedOperation) {
        const error = document.getElementById('error');
        error.textContent = 'Please select an operation (+, -, ×, ÷)';
        error.style.display = 'block';
        setTimeout(() => {
            error.style.display = 'none';
        }, 2000);
        return;
    }

    const num1 = parseFloat(document.getElementById('num1').value);
    const num2 = parseFloat(document.getElementById('num2').value);
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const resultValue = document.getElementById('resultValue');

    // Reset states
    loading.style.display = 'block';
    error.style.display = 'none';
    resultValue.textContent = '-';

    // Validate inputs
    if (isNaN(num1) || isNaN(num2)) {
        error.textContent = 'Please enter valid numbers';
        error.style.display = 'block';
        loading.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/${selectedOperation}?a=${num1}&b=${num2}`);
        const data = await response.json();

        if (response.ok) {
            resultValue.textContent = data.result;

            // Animate result
            resultValue.style.transform = 'scale(1.2)';
            setTimeout(() => {
                resultValue.style.transform = 'scale(1)';
            }, 200);

            // Trigger salute animation
            const equalsButton = document.querySelector('.btn-equals');
            const rect = equalsButton.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            createSaluteAnimation(centerX, centerY);
        } else {
            error.textContent = data.detail || 'Calculation failed';
            error.style.display = 'block';
        }
    } catch (err) {
        error.textContent = 'Error connecting to API: ' + err.message;
        error.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}

function reset() {
    const resultValue = document.getElementById('resultValue');
    const error = document.getElementById('error');
    const loading = document.getElementById('loading');

    // Reset input fields
    document.getElementById('num1').value = 0;
    document.getElementById('num2').value = 0;

    // Reset result display
    resultValue.textContent = 0;
    error.style.display = 'none';
    loading.style.display = 'none';

    // Reset selected operation
    selectedOperation = null;
    document.querySelectorAll('.btn-add, .btn-subtract, .btn-multiply, .btn-divide').forEach(btn => {
        btn.classList.remove('active');
    });
}

// Allow Enter key to trigger calculation
document.getElementById('num2').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        calculateResult();
    }
});
