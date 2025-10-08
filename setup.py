#!/usr/bin/env python3
"""
Moda Crypto Setup Script
Automated setup for the Moda Crypto application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, cwd=None, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None


def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")

    # Check Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("❌ Python 3.9+ is required")
        return False
    print(
        f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")

    # Check Node.js
    node_result = run_command("node --version", check=False)
    if not node_result or node_result.returncode != 0:
        print("❌ Node.js is not installed")
        return False
    print(f"✅ Node.js {node_result.stdout.strip()}")

    # Check npm
    npm_result = run_command("npm --version", check=False)
    if not npm_result or npm_result.returncode != 0:
        print("❌ npm is not installed")
        return False
    print(f"✅ npm {npm_result.stdout.strip()}")

    # Check git
    git_result = run_command("git --version", check=False)
    if not git_result or git_result.returncode != 0:
        print("⚠️  Git not found - version control won't be available")
    else:
        print(f"✅ {git_result.stdout.strip()}")

    return True


def setup_environment():
    """Setup environment files"""
    print("\n📝 Setting up environment files...")

    # Backend .env
    backend_env_example = Path("backend/.env.example")
    backend_env = Path("backend/.env")

    if backend_env_example.exists() and not backend_env.exists():
        shutil.copy(backend_env_example, backend_env)
        print("✅ Created backend/.env from .env.example")
        print("⚠️  Please edit backend/.env with your API keys and Firebase credentials")
    elif backend_env.exists():
        print("✅ backend/.env already exists")
    else:
        print("❌ backend/.env.example not found")

    # Frontend .env.local
    frontend_env_example = Path("frontend/.env.example")
    frontend_env = Path("frontend/.env.local")

    if frontend_env_example.exists() and not frontend_env.exists():
        shutil.copy(frontend_env_example, frontend_env)
        print("✅ Created frontend/.env.local from .env.example")
        print("⚠️  Please edit frontend/.env.local with your Firebase configuration")
    elif frontend_env.exists():
        print("✅ frontend/.env.local already exists")
    else:
        print("❌ frontend/.env.example not found")


def setup_backend():
    """Setup Python backend"""
    print("\n🐍 Setting up Python backend...")

    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False

    # Create virtual environment
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("Creating Python virtual environment...")
        result = run_command("python3 -m venv venv", cwd=backend_dir)
        if not result:
            print("❌ Failed to create virtual environment")
            return False
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = venv_dir / "Scripts" / "activate"
        pip_path = venv_dir / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = venv_dir / "bin" / "activate"
        pip_path = venv_dir / "bin" / "pip"

    # Install requirements
    requirements_file = backend_dir / "requirements.txt"
    if requirements_file.exists():
        print("Installing Python dependencies...")
        result = run_command(
            f"{pip_path} install -r requirements.txt", cwd=backend_dir)
        if not result:
            print("❌ Failed to install Python dependencies")
            return False
        print("✅ Python dependencies installed")
    else:
        print("❌ requirements.txt not found")
        return False

    return True


def setup_frontend():
    """Setup Node.js frontend"""
    print("\n⚛️  Setting up Node.js frontend...")

    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False

    # Install npm dependencies
    package_json = frontend_dir / "package.json"
    if package_json.exists():
        print("Installing Node.js dependencies...")
        result = run_command("npm install", cwd=frontend_dir)
        if not result:
            print("❌ Failed to install Node.js dependencies")
            return False
        print("✅ Node.js dependencies installed")
    else:
        print("❌ package.json not found")
        return False

    return True


def print_next_steps():
    """Print instructions for next steps"""
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Configure your API keys:")
    print("   - Edit backend/.env with your Firebase and external API credentials")
    print("   - Edit frontend/.env.local with your Firebase project configuration")
    print("\n2. Start the development servers:")
    print("   Backend:")
    if os.name == 'nt':  # Windows
        print("     cd backend")
        print("     venv\\Scripts\\activate")
        print("     uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    else:  # Unix/Linux/macOS
        print("     cd backend")
        print("     source venv/bin/activate")
        print("     uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")

    print("\n   Frontend (in a new terminal):")
    print("     cd frontend")
    print("     npm run dev")

    print("\n3. Access the application:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:8000")
    print("   - API Documentation: http://localhost:8000/docs")

    print("\n📚 Additional resources:")
    print("   - README.md for detailed setup instructions")
    print("   - Firebase Console for database management")
    print("   - API documentation for endpoint details")


def main():
    """Main setup function"""
    print("🚀 Moda Crypto Setup Script")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the moda-crypto root directory")
        sys.exit(1)

    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please install the required tools.")
        sys.exit(1)

    # Setup environment files
    setup_environment()

    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)

    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
