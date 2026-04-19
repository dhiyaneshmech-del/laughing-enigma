document.addEventListener('DOMContentLoaded', () => {
    const probabilityInput = document.getElementById('probability');
    const probabilityValue = document.getElementById('probabilityValue');
    const form = document.getElementById('surveyForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');

    // Update range value display
    probabilityInput.addEventListener('input', (e) => {
        probabilityValue.textContent = e.target.value;
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Hide previous messages
        successMessage.classList.add('hidden');
        errorMessage.classList.add('hidden');
        
        // Form data
        const formData = {
            name: document.getElementById('name').value.trim(),
            email: document.getElementById('email').value.trim(),
            constituency: document.getElementById('constituency').value.trim(),
            party: document.getElementById('party').value,
            probability: parseInt(probabilityInput.value, 10)
        };

        // Basic validation
        if (!formData.name || !formData.email || !formData.constituency || !formData.party) {
            showError('Please fill in all required fields.');
            return;
        }

        // UI Loading state
        setLoading(true);

        try {
            // Send request to the specific Render backend URL
            const response = await fetch('https://laughing-enigma-5.onrender.com/api/submit-survey', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                // Success
                form.reset();
                probabilityValue.textContent = '50';
                successMessage.classList.remove('hidden');
                
                // Hide inputs but keep panel
                Array.from(form.children).forEach(child => {
                    if (child.id !== 'successMessage') {
                        child.style.display = 'none';
                    }
                });
            } else {
                // Backend validation error
                showError(result.detail || 'Failed to submit survey. Please try again.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            showError('Network error. Please make sure the server is running and try again.');
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        submitBtn.disabled = isLoading;
        if (isLoading) {
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
        } else {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    }

    function showError(msg) {
        errorMessage.querySelector('p').textContent = msg;
        errorMessage.classList.remove('hidden');
    }
});
