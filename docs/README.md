# Moda Crypto Documentation

This directory contains all documentation, setup scripts, and guides for the Moda Crypto project.

## 📂 Directory Structure

### `/setup` - Setup Scripts
Contains automated setup scripts for various platforms and services:

- **`setup.py`** - Main Python setup script (cross-platform)
- **`setup.ps1`** - PowerShell setup script for Windows
- **`setup-existing-gcp.sh`** - GCP setup for existing projects
- **`setup-apis.sh`** - API keys and services setup
- **`setup-secrets.sh`** - Environment secrets configuration
- **`api-keys-guide.sh`** - Interactive guide for getting API keys
- **`quick-api-setup.sh`** - Quick setup for essential APIs

### `/guides` - Documentation & Guides
Contains detailed guides and documentation:

- **`DEVELOPMENT.md`** - Development setup and workflow
- **`FIREBASE_PRODUCTION_GUIDE.md`** - Firebase deployment guide
- **`SECRETS_REQUIRED.md`** - Required environment variables and secrets
- **`REFACTORING_SUMMARY.md`** - Project refactoring history

## 🚀 Quick Start

1. **For new users**: Start with [`setup/setup.py`](setup/setup.py) or [`setup/setup.ps1`](setup/setup.ps1)
2. **For API setup**: Run [`setup/api-keys-guide.sh`](setup/api-keys-guide.sh) for interactive setup
3. **For development**: Read [`guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md)
4. **For deployment**: Follow [`guides/FIREBASE_PRODUCTION_GUIDE.md`](guides/FIREBASE_PRODUCTION_GUIDE.md)

## 📋 Setup Order

For a complete setup from scratch:

1. Run the main setup script for your platform
2. Configure API keys using the API setup scripts
3. Set up GCP and Firebase using the deployment guides
4. Follow the development guide for local development

## 🔧 Platform-Specific Setup

- **Windows**: Use `setup/setup.ps1`
- **macOS/Linux**: Use `setup/setup.py` or bash scripts
- **Existing GCP Project**: Use `setup/setup-existing-gcp.sh`

## 📚 Additional Resources

- Main project README: [`../README.md`](../README.md)
- Environment template: [`../.env.example`](../.env.example)
- Firebase configuration: [`../firebase.json`](../firebase.json)