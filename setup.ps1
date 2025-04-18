# Validate Python 3.11 availability
try {
    $pythonCommand = Get-Command "py" -ErrorAction Stop
    $pythonVersion = & py -3.11 --version 2>&1
    if ($pythonVersion -notlike "*Python 3.11*") {
        Write-Error "Python 3.11 is required but not found. Please install Python 3.11 and ensure 'py -3.11' works."
        exit 1
    }
    Write-Host "Python 3.11 found: $pythonVersion"
} catch {
    Write-Error "Python Launcher (py) not found. Please install Python 3.11 and ensure 'py' is in PATH."
    exit 1
}

# Create virtual environment if it doesn't exist
$venvPath = ".\venv"
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..."
    try {
        & py -3.11 -m venv $venvPath
        if (-not (Test-Path $activateScript)) {
            Write-Error "Failed to create virtual environment. Ensure you have write permissions and 'venv' module is available."
            exit 1
        }
        Write-Host "Virtual environment created successfully."
    } catch {
        Write-Error "Error creating virtual environment: $_"
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists, skipping creation."
}

# Check execution policy
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq "Restricted" -or $policy -eq "AllSigned") {
    Write-Warning "Current execution policy ($policy) may prevent running Activate.ps1. Consider running: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned"
}

# Activate virtual environment
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..."
    try {
        & $activateScript
        Write-Host "Virtual environment activated."
    } catch {
        Write-Error "Failed to activate virtual environment: $_"
        Write-Warning "Proceeding with installation using venv's pip directly."
        $useVenvPip = $true
    }
} else {
    Write-Error "Activation script not found: $activateScript"
    Write-Warning "Proceeding with installation using venv's pip directly."
    $useVenvPip = $true
}

# Upgrade pip in the virtual environment
Write-Host "Upgrading pip..."
try {
    & py -3.11 -m pip install --upgrade pip
    Write-Host "Pip upgraded successfully."
} catch {
    Write-Error "Failed to upgrade pip: $_"
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..."
try {
    if ($useVenvPip) {
        & "$venvPath\Scripts\pip.exe" install -r requirements.txt
    } else {
        & pip install -r requirements.txt
    }
    Write-Host "Dependencies installed successfully."
} catch {
    Write-Error "Failed to install dependencies: $_"
    exit 1
}

Write-Host "Setup complete. To use Vertex:"
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate.ps1"
Write-Host "2. Run the application: py -3.11 .\src\main.py"