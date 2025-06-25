"""
Setup Script for Testing LangChain NLP Integration
Checks dependencies and guides through setup process
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "requests",
        "python-dotenv",
        "langchain",
        "langchain-openai",
        "langchain-community"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    return missing_packages

def install_missing_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"\n📦 Installing {len(packages)} missing packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    return True

def check_environment_setup():
    """Check environment file setup"""
    env_files = {
        ".env.local": "Local development (highest priority)",
        ".env": "Default configuration",
        "env.example": "Template file"
    }
    
    print("\n🔧 ENVIRONMENT FILES:")
    for file, description in env_files.items():
        if Path(file).exists():
            print(f"✅ {file} - {description}")
        else:
            print(f"❌ {file} - {description}")
    
    # Check for API key
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    load_dotenv(".env")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and not api_key.startswith("your_") and not api_key.startswith("sk-your"):
        print("✅ OpenAI API key configured")
        return True
    else:
        print("❌ OpenAI API key not configured")
        return False

def create_env_local():
    """Create .env.local file with template"""
    if Path(".env.local").exists():
        print("📝 .env.local already exists")
        return
    
    template = """# Local Development Environment Variables
# This file takes highest priority and is gitignored

# OpenAI API Key (required for NLP features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Development settings
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Optional: Other AI providers
# ANTHROPIC_API_KEY=your-anthropic-key
# GOOGLE_API_KEY=your-google-key
"""
    
    try:
        with open(".env.local", "w") as f:
            f.write(template)
        print("✅ Created .env.local template")
        print("📝 Edit .env.local and add your OpenAI API key")
    except Exception as e:
        print(f"❌ Failed to create .env.local: {e}")

def main():
    """Main setup function"""
    print("🚀 AUTONOMICA LANGCHAIN NLP SETUP")
    print("=" * 50)
    
    # Check Python version
    print("\n1. PYTHON VERSION:")
    if not check_python_version():
        return False
    
    # Check dependencies
    print("\n2. DEPENDENCIES:")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  {len(missing)} packages need to be installed")
        response = input("Install missing packages? (y/n): ").lower()
        if response == 'y':
            if not install_missing_packages(missing):
                print("❌ Package installation failed")
                return False
        else:
            print("❌ Cannot proceed without required packages")
            return False
    
    # Check environment setup
    print("\n3. ENVIRONMENT SETUP:")
    has_api_key = check_environment_setup()
    
    if not has_api_key:
        create_env_local()
        print("\n⚠️  Please add your OpenAI API key to .env.local before testing")
    
    # Final instructions
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("=" * 50)
    
    if not has_api_key:
        print("1. Edit .env.local and add your OpenAI API key:")
        print("   OPENAI_API_KEY=sk-your-actual-key-here")
        print()
    
    print("2. Start the API server:")
    print("   python -m uvicorn app.main:app --reload")
    print()
    
    print("3. Run the comprehensive test suite:")
    print("   python test_complete_setup.py")
    print()
    
    print("4. Test specific API endpoints:")
    print("   python test_api_endpoints.py")
    print()
    
    print("5. Test individual components:")
    print("   # Test imports only")
    print("   python -c \"from app.owl.langchain_integration import LangChainNLPEngine; print('✅ Imports work')\"")
    print()
    
    print("🔗 USEFUL COMMANDS:")
    print("• Check server health: curl http://localhost:8000/api/health")
    print("• View NLP capabilities: curl http://localhost:8000/api/nlp/capabilities")
    print("• Check logs: tail -f logs/app.log (if logging to file)")
    
    print("\n📚 DOCUMENTATION:")
    print("• Environment setup: ENV_SETUP_GUIDE.md")
    print("• API documentation: http://localhost:8000/docs (when server is running)")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Setup complete! Ready for testing.")
    else:
        print("\n❌ Setup incomplete. Please resolve issues above.")
    sys.exit(0 if success else 1) 