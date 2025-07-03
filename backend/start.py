#!/usr/bin/env python3
"""
Backend startup script with network debugging
"""
import uvicorn
import socket
import sys
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

def main():
    print("🚀 İsra Holding - Yatırımcı Raporu Backend")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
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
        print(f"❌ Port {port} is already in use!")
        print("   Try stopping other instances or use a different port")
        sys.exit(1)
    
    print("\n📋 Backend will be accessible at:")
    print(f"   • http://localhost:{port}")
    print(f"   • http://127.0.0.1:{port}")
    print(f"   • http://{local_ip}:{port} (from other devices on network)")
    
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