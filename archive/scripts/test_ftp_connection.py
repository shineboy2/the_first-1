#!/usr/bin/env python3
"""
Test FTP connection with detailed logging
"""
import ftplib
import sys

def test_ftp(host, port, user, password, path="/"):
    """Test FTP connection with detailed output"""
    print(f"=" * 80)
    print(f"Testing FTP Connection")
    print(f"=" * 80)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)}")
    print(f"Path: {path}")
    print(f"=" * 80)
    print()
    
    try:
        print(f"Step 1: Creating FTP object...")
        ftp = ftplib.FTP()
        ftp.set_debuglevel(2)  # Enable debug output
        
        print(f"\nStep 2: Connecting to {host}:{port}...")
        ftp.connect(host, port, timeout=10)
        print(f"✓ Connected successfully")
        
        print(f"\nStep 3: Logging in as '{user}'...")
        ftp.login(user, password)
        print(f"✓ Login successful")
        
        print(f"\nStep 4: Getting welcome message...")
        print(f"Welcome: {ftp.getwelcome()}")
        
        print(f"\nStep 5: Changing to directory '{path}'...")
        ftp.cwd(path)
        print(f"✓ Changed to {path}")
        
        print(f"\nStep 6: Listing files...")
        files = ftp.nlst()
        print(f"✓ Found {len(files)} files:")
        for f in files[:10]:  # Show first 10
            print(f"  - {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
        
        print(f"\nStep 7: Closing connection...")
        ftp.quit()
        print(f"✓ Connection closed")
        
        print(f"\n{'=' * 80}")
        print(f"✅ SUCCESS: FTP connection test passed!")
        print(f"{'=' * 80}")
        return True
        
    except ftplib.error_perm as e:
        print(f"\n{'=' * 80}")
        print(f"❌ PERMISSION ERROR: {e}")
        print(f"{'=' * 80}")
        return False
    except ConnectionRefusedError as e:
        print(f"\n{'=' * 80}")
        print(f"❌ CONNECTION REFUSED: {e}")
        print(f"Possible reasons:")
        print(f"  - FTP server is not running")
        print(f"  - Firewall blocking connection")
        print(f"  - Wrong port number")
        print(f"  - Server not accessible from this network")
        print(f"{'=' * 80}")
        return False
    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"❌ ERROR ({type(e).__name__}): {e}")
        print(f"{'=' * 80}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 test_ftp_connection.py <host> <port> <user> <password> [path]")
        print("Example: python3 test_ftp_connection.py 10.250.240.1 8090 ftpUser01 MyComplex /results")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    user = sys.argv[3]
    password = sys.argv[4]
    path = sys.argv[5] if len(sys.argv) > 5 else "/"
    
    success = test_ftp(host, port, user, password, path)
    sys.exit(0 if success else 1)
