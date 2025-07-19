
let currentContainerId = null
let refreshInterval = null
let containerState = {
  exists: false,
  running: false
}
let redirectAgent = {
  ip: null,
  port: null
}
let portInfo = null


const containerInfo = document.getElementById('container-info')
const actionButtons = document.querySelectorAll('#create-btn, #start-btn, #stop-btn, #restart-btn, #remove-btn')
const serviceButtons = document.querySelectorAll('.service-btn')
const serviceInfoSection = document.getElementById('service-info')
const serviceTitle = document.getElementById('service-title')
const serviceContent = document.getElementById('service-content')

const containerSelect = document.getElementById('container-select')
const createButton = document.getElementById('create-btn')
const startButton = document.getElementById('start-btn')
const stopButton = document.getElementById('stop-btn')
const removeButton = document.getElementById('remove-btn')


// Generate container name from username
const getContainerName = async (username) => {
  const hash = await window.electronAPI.generateUserHash(username)
  return `code-server-${username}-${hash}`
}

const updateButtonStates = () => {
  console.log('Updating button states:', containerState)

  try {
    // When container is not available, only create button should be active
    if (!containerState.exists) {
      createButton.style.display = 'block'
      createButton.disabled = false

      // Hide all other action buttons
      const actionButtons = document.querySelectorAll('#start-btn, #stop-btn, #restart-btn, #remove-btn')
      actionButtons.forEach(btn => {
        btn.style.display = 'none'
        btn.disabled = true
      })
      return
    }

    // When container exists
    createButton.style.display = 'none'
    createButton.disabled = true

    // Show all action buttons
    const actionButtons = document.querySelectorAll('#start-btn, #stop-btn, #restart-btn, #remove-btn')
    actionButtons.forEach(btn => {
      btn.style.display = 'block'
      btn.disabled = false
    })

    // Update button states based on container running state
    if (containerState.running) {
      startButton.disabled = true
      stopButton.disabled = false
      removeButton.disabled = true // Can't remove while running
    } else {
      startButton.disabled = false
      stopButton.disabled = true
      removeButton.disabled = true // Can remove when stopped
    }
  } catch (error) {
    console.error('Error updating button states:', error)
  }
}

// Fetch available containers
const fetchContainers = async () => {
  try {
    const userData = getSession()
    const container_name = await getContainerName(userData.username)
    const response = await window.electronAPI.getContainerInfo(container_name)
    console.log('Container Info Response:', response)

    if (!response || !response.container) {
      throw new Error('Invalid container info response')
    }

    const containers = Array.isArray(response.container) ? response.container : [response.container]

    console.log(containers)

    // Set the first container as selected and update the h2 text
    if (containers.length > 0) {
      const container = containers[0]
      containerSelect.textContent = container.name
      currentContainerId = container.id

      // Update container state
      containerState.exists = true
      containerState.running = container.status === 'running'

      // Start stats updates
      updateStats()
      if (refreshInterval)
        clearInterval(refreshInterval)

      refreshInterval = setInterval(updateStats, 150000)
    } else {
      containerSelect.textContent = 'No container selected'
      currentContainerId = null
      containerState.exists = false
      containerState.running = false
    }

    updateButtonStates()
  } catch (error) {
    console.error('Error fetching containers:', error)
  }
}

// Update container stats
const updateStats = async () => {
  try {
    const userData = getSession()
    const container_name = await getContainerName(userData.username)

    const response = await window.electronAPI.getContainerStats(container_name)
    console.log('Container Stats:', JSON.stringify(response, null, 2))

    if (!response) {
      throw new Error('No stats received from container')
    }

    const stats = response.stats

    const cpuUsage = stats.cpu_usage || 0
    const memoryUsage = stats.memory_usage || 0
    const memoryUsed = stats.memory_used || 0
    const memoryLimit = stats.memory_limit || 0

    containerInfo.classList.remove('hidden');
    containerInfo.innerHTML = `
    <style>
      .metrics-container {
        padding: 0.5rem 0;
      }
      
      .metric-item {
        margin-bottom: 1.5rem;
      }
      
      .progress-label {
        color: rgba(0, 0, 0, 0.87);
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .progress-label span {
        color: rgba(0, 0, 0, 0.6);
        font-size: 0.75rem;
      }
      
      .progress-track {
        height: 4px;
        background-color: rgba(0, 0, 0, 0.08);
        border-radius: 2px;
        overflow: hidden;
        position: relative;
      }
      
      .progress-bar {
        height: 100%;
        background-color: #1976d2;
        position: absolute;
        top: 0;
        left: 0;
        transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      
      .memory-stats {
        display: flex;
        justify-content: space-between;
        margin-top: 2rem;
        color: rgba(0, 0, 0, 0.6);
        font-size: 0.875rem;
      }
    </style>
    
    <div class="metrics-container" id="cpu-progress">
      <div class="metric-item">
        <div class="progress-label">
          CPU Usage
          <span>${cpuUsage.toFixed(1)}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-bar" style="width: ${cpuUsage}%"></div>
        </div>
      </div>
      
      <div class="metric-item" id="memory-progress">
        <div class="progress-label">
          Memory Usage
          <span>${memoryUsage.toFixed(1)}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-bar" style="width: ${memoryUsage}%"></div>
        </div>
      </div>
      
      <div class="memory-stats" id="memory-stats">
        <div>Used: ${memoryUsed.toFixed(2)} MB</div>
        <div>Total: ${memoryLimit.toFixed(2)} MB</div>
      </div>
    </div>
  `
  } catch (error) {
    console.error('Error updating stats:', error)
  }
}

// Add port information to container info section
const updatePortInfo = async () => {
  if (!currentContainerId || !containerState.exists) return;

  try {

    const portInfoHtml = `
      <div class="space-y-2">
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span class="font-medium">Code Server</span>
          <span class="text-blue-600">${portInfo.code_port}</span>
        </div>
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span class="font-medium">SSH</span>
          <span class="text-blue-600">${portInfo.ssh_port}</span>
        </div>
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span class="font-medium">SPICE</span>
          <span class="text-blue-600">${portInfo.spice_port}</span>
        </div>
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span class="font-medium">File Manager UI</span>
          <span class="text-blue-600">${portInfo.fm_ui_port}</span>
        </div>
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span class="font-medium">File Manager</span>
          <span class="text-blue-600">${portInfo.fm_port}</span>
        </div>
      </div>
    `;

    // Update modal content
    const modalPortInfo = document.getElementById('modal-port-info');
    if (modalPortInfo) {
      modalPortInfo.innerHTML = portInfoHtml;
    }
  } catch (error) {
    console.error('Error fetching port information:', error);
  }
};

// Show about information
const showAbout = () => {
  serviceInfoSection.classList.remove('hidden')
  serviceTitle.textContent = 'About'
  serviceContent.innerHTML = `
    <div class="mb-2">This is the CXL Remote Development interface.</div>
    <div class="mb-2">Version: 1.0.0</div>
    <div>Placeholder for about information</div>
  `
}

// Handle container actions
const handleContainerAction = async (action) => {
  if (!currentContainerId && action !== 'create') return

  try {
    window.electronAPI.showLoading()
    await window.electronAPI.containerAction(action, currentContainerId)

    // Refresh container state after action
    await fetchContainers()
    await refreshContainerState()
  } catch (error) {
    console.error(`Error performing container action ${action}:`, error)
  } finally {
    window.electronAPI.hideLoading()
  }
}

// Handle create container form submission
const handleCreateContainer = async (e) => {
  e.preventDefault()

  try {
    window.electronAPI.showLoading()
    const userInfo = await getUserInfo()
    await window.electronAPI.containerCreate(userInfo.username, userInfo.sessionToken)

    // Refresh container list after creation
    await fetchContainers()
  } catch (error) {
    console.error('Error creating container:', error)
  } finally {
    window.electronAPI.hideLoading()
  }
}

// Handle logout
const handleLogout = async () => {
  try {
    window.electronAPI.showLoading('Logging out...')

    // Stop any running intervals
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }

    // Reset container state
    containerState = {
      exists: false,
      running: false
    }
    currentContainerId = null
    portInfo = null
    redirectAgent = {
      ip: null,
      port: null
    }

    // Clear session
    const userInfo = await getUserInfo()
    if (userInfo) {
      await window.electronAPI.logout(userInfo.userId)
    }
    clearSession()

    // Reset UI elements
    containerSelect.textContent = 'No container selected'
    serviceInfoSection.classList.add('hidden')

    updateButtonStates()

    window.electronAPI.resetUI()

    // Show login screen
    document.getElementById('app-container').classList.add('hidden')
    document.getElementById('login-container').classList.remove('hidden')
  } catch (error) {
    console.error('Error during logout:', error)
  } finally {
    window.electronAPI.hideLoading()
  }
}

// Setup event listeners
const aboutButton = document.getElementById('about-btn')
const logoutButton = document.getElementById('logout-btn')

if (aboutButton) {
  aboutButton.addEventListener('click', showAbout)
}

if (logoutButton) {
  logoutButton.addEventListener('click', handleLogout)
}

actionButtons.forEach(button => {
  button.addEventListener('click', () => {
    const action = button.id.replace('-btn', '')
    handleContainerAction(action)
  })
})

// Auth-related functions
const loginForm = document.getElementById('login-form')
const loginError = document.getElementById('login-error')
const loginContainer = document.getElementById('login-container')
const appContainer = document.getElementById('app-container')

// Session management
const saveSession = (userData) => {
  localStorage.setItem('user', JSON.stringify(userData))
}

const clearSession = () => {
  localStorage.removeItem('user')
}

const getSession = () => {
  const userData = localStorage.getItem('user')
  return userData ? JSON.parse(userData) : null
}

const validateSession = async () => {
  const userData = getSession()
  if (!userData) return false

  try {
    const response = await window.electronAPI.validateSession(userData.id, userData.session_token)
    return response.valid
  } catch (error) {
    console.error('Session validation failed:', error)
    return false
  }
}

const getUserInfo = async () => {
  try {
    const userData = getSession()
    if (!userData) return false

    const response = await window.electronAPI.getUserInfo(userData.id, userData.session_token)
    return response
  } catch (error) {
    console.error('Invalid user info:', error)
    return false
  }
}

const handleLogin = async (e) => {
  e.preventDefault()
  loginError.classList.add('hidden')

  const username = document.getElementById('username').value
  const password = document.getElementById('password').value

  try {
    const response = await window.electronAPI.login(username, password)
    if (response.success) {
      saveSession(response.user)
      loginContainer.classList.add('hidden')
      appContainer.classList.remove('hidden')
      await initApp()
    } else {
      loginError.textContent = response.error || 'Login failed'
      loginError.classList.remove('hidden')
    }
  } catch (error) {
    loginError.textContent = error.message || 'Login failed'
    loginError.classList.remove('hidden')
  }
}

// Initialize app
const initApp = async () => {

  const userInfo = await getUserInfo()
  
  if (userInfo && userInfo.success && userInfo.redirect_url) {
    const url = new URL(userInfo.redirect_url)
    redirectAgent.ip = url.hostname
    redirectAgent.port = url.port
    console.log('Redirect agent IP:', redirectAgent.ip)
    console.log('Redirect agent port:', redirectAgent.port)

    redirectAgent.port = parseInt(redirectAgent.port) + 1

    // Set up container API with the redirect URL
    try {
      await window.electronAPI.setContainerApi(redirectAgent.ip, redirectAgent.port)
      console.log('Container API configured successfully')
      const userData = getSession()
      portInfo = await window.electronAPI.getContainerPorts(userData.username);
    } catch (error) {
      console.error('Failed to configure container API:', error)
      alert('Failed to configure container connection. Please try again.')
      return
    }
  }

  // Fetch available containers
  await fetchContainers()

  refreshContainerState()
}

// Cleanup intervals on window close
window.addEventListener('beforeunload', () => {
  clearInterval(refreshInterval)
})

// Handle service navigation

const launchFMUI = () => {
  if (containerState.exists && containerState.running && redirectAgent.ip && portInfo?.fm_ui_port) {
    window.electronAPI.fmConnect(redirectAgent.ip, portInfo.fm_ui_port)
      .catch(error => console.error('Failed to launch FM UI:', error));

  }
};


// Function to launch remote viewer
const launchRemoteViewer = () => {
  if (containerState.exists && containerState.running && redirectAgent.ip && portInfo?.spice_port) {
    window.electronAPI.rdpConnect(redirectAgent.ip, redirectAgent.port, portInfo.spice_port)
      .catch(error => console.error('Failed to launch remote-viewer:', error));
  }
};

serviceButtons.forEach(button => {
  button.addEventListener('click', () => {
    const service = button.getAttribute('data-service')
    showServiceInfo(service)
  })
})

// Handle system tray container actions
window.electronAPI.on('container-action', (action) => {
  handleContainerAction(action)
})

// Handle system tray service actions
window.electronAPI.on('service-action', (service) => {
  showServiceInfo(service)
})

const handleVSCodeConnect = async () => {
  const host = redirectAgent.ip
  const port = portInfo.code_port
  await window.electronAPI.vscodeConnect(host, port)
}

// Handle SSH connection form submission
const handleSSHConnect = async () => {
  const host = redirectAgent.ip
  const port = portInfo.ssh_port
  const username = 'root'
  await window.electronAPI.sshConnect(username, host, port)
}

const showServiceInfo = (service) => {
  console.log(containerState)
  if (!containerState.exists || !containerState.running) return

  serviceInfoSection.classList.remove('hidden')

  switch (service) {
    case 'vscode':
      serviceTitle.textContent = 'VS Code Access'
      serviceContent.innerHTML = `
        <div class="mb-2">Use the following URL to access VS Code:</div>
        <div class="bg-gray-100 p-2 rounded cursor-pointer hover:bg-gray-200 transition-colors">
          <code id="vscode-url">http://${redirectAgent.ip}:${portInfo.code_port}</code>
        </div>
      `
      // Add click handler to open VS Code URL
      const vscodeUrl = document.getElementById('vscode-url');
      if (vscodeUrl) {
        vscodeUrl.parentElement.addEventListener('click', () => {
          handleVSCodeConnect()
        });
      }
      handleVSCodeConnect()
      break

    case 'ssh':
      serviceTitle.textContent = 'SSH Access'
      serviceContent.innerHTML = `
        <div class="space-y-2">
          <div>
            <div class="mb-2">Use the following command to connect via SSH:</div>
            <div class="bg-gray-100 p-2 rounded">
              <code id="ssh-command">ssh -p ${portInfo.ssh_port} root@${redirectAgent.ip}</code>
            </div>
          </div>
        </div>
      `
      const sshCommand = document.getElementById('ssh-command');
      if (sshCommand) {
        sshCommand.parentElement.addEventListener('click', () => {
          handleSSHConnect()
        });
      }

      handleSSHConnect()
      break

    case 'rdp':
      serviceTitle.textContent = 'RDP Access'
      serviceContent.innerHTML = `
        <div class="mb-2">Use the following command to connect via RDP:</div>
        <div class="bg-gray-100 p-2 rounded cursor-pointer hover:bg-gray-200 transition-colors">
          <code id="rdp-command">remote-viewer spice://${redirectAgent.ip}:${portInfo.spice_port}</code>
        </div>
      `
      // Add click handler for RDP command
      const rdpCommand = document.getElementById('rdp-command');
      if (rdpCommand) {
        rdpCommand.parentElement.addEventListener('click', launchRemoteViewer);
      }
      launchRemoteViewer()
      break

      case 'fm':
      serviceTitle.textContent = 'FM UI Access'
      serviceContent.innerHTML = `
        <div class="mb-2">Use the following URL to access FM UI:</div>
        <div class="bg-gray-100 p-2 rounded">
          <code id="fm-url"> http://${redirectAgent.ip}:${portInfo.fm_ui_port}</code>
        </div>
      `
      const fmUrl = document.getElementById('fm-url');
      if (fmUrl) {
        fmUrl.parentElement.addEventListener('click', () => {
          launchFMUI()
        });
      }
      launchFMUI()
      break

    case 'refresh':
      serviceInfoSection.classList.add('hidden')
      serviceTitle.textContent = ''
      serviceContent.innerHTML = ``
      currentContainerId = null
      containerSelect.textContent = 'No container selected'
      fetchContainers()
      break
  }
}

// Update the refreshContainerState function to include port info
const refreshContainerState = async () => {
  try {
    const userData = getSession()
    const container_name = await getContainerName(userData.username)
    const response = await window.electronAPI.getContainerInfo(container_name)

    if (response && response.container) {
      const containers = Array.isArray(response.container) ? response.container : [response.container]
      containerState.exists = containers.length > 0
      containerState.running = containers.some(c => c.status === 'running')
      updateButtonStates()
    }
  } catch (error) {
    console.error('Error refreshing container state:', error)
  }

}

// Start the app
const init = async () => {
  // Setup login form handler
  loginForm.addEventListener('submit', handleLogin)

  // Check for existing session
  const isValidSession = await validateSession()
  if (isValidSession) {
    loginContainer.classList.add('hidden')
    appContainer.classList.remove('hidden')
    await initApp()
  } else {
    clearSession()
    loginContainer.classList.remove('hidden')
    appContainer.classList.add('hidden')
  }
}

// Add event listeners for port info modal
const portInfoBtn = document.getElementById('port-info-btn');
const portInfoModal = document.getElementById('port-info-modal');
const closePortModal = document.getElementById('close-port-modal');

if (portInfoBtn) {
  portInfoBtn.addEventListener('click', async () => {
    await updatePortInfo(); // Update port info before showing modal
    portInfoModal.classList.remove('hidden');
  });
}

if (closePortModal) {
  closePortModal.addEventListener('click', () => {
    portInfoModal.classList.add('hidden');
  });
}

// Close modal when clicking outside
portInfoModal.addEventListener('click', (e) => {
  if (e.target === portInfoModal) {
    portInfoModal.classList.add('hidden');
  }
});

init()
