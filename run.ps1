cls

$pythonVersion = python --version

# Check if Python3 is installed
if (!($pythonVersion -match "Python 3\.\d+\.\d+")) {
    Write-Host "No Python3 version found; exiting..."
    Exit
}

# Check for a Python environment name '.venv'
if (!(Test-Path -Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\activate
    python -m pip install --upgrade pip
    
    # Check for a Python requirements.txt file
    if (!(Test-Path -Path "requirements.txt")) {
        Write-Host "Requirements file not found; exiting..."
        Exit
    }

    python -m pip install -r requirements.txt
}

.venv\Scripts\activate

python main.py $args
