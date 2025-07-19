// UI utilities for both main and renderer processes
function getElement(id) {
    try {
        return document.getElementById(id);
    } catch (e) {
        return null;
    }
}

function showLoading(text = 'Loading...') {
    const loadingText = getElement('loading-text');
    const loadingOverlay = getElement('loading-overlay');
    if (loadingText) loadingText.textContent = text;
    if (loadingOverlay) loadingOverlay.classList.add('active');
}

function hideLoading() {
    const loadingText = getElement('loading-text');
    const loadingOverlay = getElement('loading-overlay');
    if (loadingText) loadingText.textContent = '';
    if (loadingOverlay) loadingOverlay.classList.remove('active');
}

function resetUI() {
   
    const containerInfo = getElement('container-info')
    if (containerInfo) {
        // hide this element
        containerInfo.classList.add('hidden');
        containerInfo.innerHTML = '';
    }
    
    // Hide service info
    const serviceInfoSection = getElement('service-info');
    if (serviceInfoSection) serviceInfoSection.classList.add('hidden');
    
    // Reset container select
    const containerSelect = getElement('container-select');
    if (containerSelect) containerSelect.textContent = 'No container selected';
    
    // Hide app container and show login container
    const appContainer = getElement('app-container');
    const loginContainer = getElement('login-container');
    if (appContainer) appContainer.classList.add('hidden');
    if (loginContainer) loginContainer.classList.remove('hidden');
}

module.exports = {
    showLoading,
    hideLoading,
    resetUI
};
