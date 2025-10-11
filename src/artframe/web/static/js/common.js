async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();
        return result;
    } catch (error) {
        console.error(`API call failed: ${endpoint}`, error);
        throw error;
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

async function handleButtonAction(button, actionFn, successMessage) {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Working...';

    try {
        await actionFn();
        showNotification(successMessage, 'success');
    } catch (error) {
        showNotification(error.message || 'Action failed', 'error');
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

function formatTimestamp(isoString) {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleString();
}

function setElementContent(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

function showError(elementId, message) {
    setElementContent(elementId, `<p class="error">Error: ${message}</p>`);
}

function showLoading(elementId, message = 'Loading...') {
    setElementContent(elementId, `<p class="loading">${message}</p>`);
}

function showInfo(elementId, message) {
    setElementContent(elementId, `<p class="info">${message}</p>`);
}