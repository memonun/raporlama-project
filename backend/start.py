#!/usr/bin/env python3
"""
Enhanced backend startup script with network debugging and diagnostics
"""
import uvicorn
import socket
import sys
import subprocess
import platform
from pathlib import Path

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "Unable to determine"

def check_port_availability(host, port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        return True
    except OSError:
        return False

def check_firewall_status():
    """Check firewall status (platform-specific)"""
    system = platform.system()
    
    if system == "Windows":
        try:
            result = subprocess.run(["netsh", "advfirewall", "show", "currentprofile"], 
                                 capture_output=True, text=True)
            if "State" in result.stdout and "ON" in result.stdout:
                return "Windows Firewall is ON - may need to allow port 8000"
            return "Windows Firewall status: Unknown"
        except:
            return "Could not check Windows Firewall status"
    
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(["sudo", "-n", "pfctl", "-s", "info"], 
                                 capture_output=True, text=True)
            if result.returncode == 0 and "Enabled" in result.stdout:
                return "macOS Firewall is enabled - may need to allow connections"
            return "macOS Firewall appears to be off"
        except:
            return "Could not check macOS Firewall status (requires sudo)"
    
    elif system == "Linux":
        try:
            # Try ufw first (Ubuntu/Debian)
            result = subprocess.run(["sudo", "-n", "ufw", "status"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                if "inactive" in result.stdout:
                    return "UFW Firewall is inactive"
                else:
                    return "UFW Firewall is active - may need to allow port 8000"
            
            # Try iptables
            result = subprocess.run(["sudo", "-n", "iptables", "-L", "-n"], 
                                 capture_output=True, text=True)
            if result.returncode == 0 and len(result.stdout) > 100:
                return "iptables rules detected - may need to allow port 8000"
                
            return "Linux Firewall status: Unknown"
        except:
            return "Could not check Linux Firewall status"
    
    return "Unknown operating system"

def test_external_connectivity(ip, port):
    """Test if the port is accessible from the local network"""
    print(f"\n🧪 Testing connectivity to {ip}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex((ip, port))
            if result == 0:
                print("   ✅ Port is accessible from local network")
                return True
            else:
                print("   ❌ Port is not accessible from local network")
                return False
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False

def generate_env_file(local_ip, port):
    """Generate .env file for frontend"""
    frontend_dir = Path(__file__).parent / "frontend"
    env_file = frontend_dir / ".env.local"
    
    try:
        with open(env_file, 'w') as f:
            f.write(f"VITE_API_URL=http://{local_ip}:{port}\n")
        print(f"\n📝 Created frontend/.env.local with API URL: http://{local_ip}:{port}")
        return True
    except Exception as e:
        print(f"\n⚠️  Could not create frontend/.env.local: {e}")
        return False

def main():
    print("🚀 İsra Holding - Yatırımcı Raporu Backend")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    print(f"📁 Backend directory: {backend_dir}")
    
    # Get network info
    local_ip = get_local_ip()
    print(f"🌐 Local IP address: {local_ip}")
    
    # Check ports
    port = 8000
    localhost_available = check_port_availability("127.0.0.1", port)
    network_available = check_port_availability("0.0.0.0", port)
    
    print(f"🔌 Port {port} on localhost: {'✅ Available' if localhost_available else '❌ In use'}")
    print(f"🔌 Port {port} on all interfaces: {'✅ Available' if network_available else '❌ In use'}")
    
    if not localhost_available:
        print(f"\n❌ Port {port} is already in use!")
        print("   Try stopping other instances or use a different port")
        print("\n   To find what's using the port:")
        if platform.system() == "Windows":
            print("   Run: netstat -ano | findstr :8000")
        else:
            print("   Run: lsof -i :8000")
        sys.exit(1)
    
    # Check firewall
    print(f"\n🔥 Firewall status: {check_firewall_status()}")
    
    # Generate frontend environment file
    generate_env_file(local_ip, port)
    
    print("\n📋 Backend will be accessible at:")
    print(f"   • http://localhost:{port}")
    print(f"   • http://127.0.0.1:{port}")
    print(f"   • http://{local_ip}:{port} (from other devices on network)")
    
    print("\n📱 For your friend to access:")
    print(f"   1. Make sure they're on the same network")
    print(f"   2. Have them open: http://{local_ip}:5173")
    print(f"   3. If it doesn't work, check:")
    print(f"      - Windows Firewall settings")
    print(f"      - Router isolation settings")
    print(f"      - Antivirus software")
    
    print("\n🔧 Environment check:")
    import os
    if os.getenv("OPENAI_API_KEY"):
        print("   ✅ OPENAI_API_KEY is set")
    else:
        print("   ⚠️  OPENAI_API_KEY not set (AI features won't work)")
    
    print(f"\n🚀 Starting FastAPI server...")
    print("   Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        import os
        os.chdir(backend_dir)
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",  # Listen on all interfaces
            port=port,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()