import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'toycraft_tales')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'ToyCraft2024!DataViz@Analytics$SecureKey789')
    
    # Ngrok configuration
    NGROK_ENABLED = os.getenv('NGROK_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        required_vars = ['DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Warning: Missing configuration for: {', '.join(missing_vars)}")
            return False
        return True
    
    @classmethod
    def display_config(cls):
        """Display current configuration (without sensitive data)"""
        print("🔧 Configuration:")
        print(f"   Database Host: {cls.DB_HOST}")
        print(f"   Database Name: {cls.DB_NAME}")
        print(f"   Database User: {cls.DB_USER}")
        print(f"   Database Port: {cls.DB_PORT}")
        print(f"   Ngrok Enabled: {cls.NGROK_ENABLED}")