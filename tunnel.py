"""
1-Click Cloudflare Tunnel for Pan-India Lead Extraction System
Automatically tunnels port 5001 to a public HTTPS URL accessible from any system or mobile device worldwide.
"""
import subprocess
import re
import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def start_tunnel():
    print("=" * 65, flush=True)
    print("  [+] STARTING CLOUDFLARE PUBLIC TUNNEL FOR PORT 5001...", flush=True)
    print("=" * 65, flush=True)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(base_dir, "cloudflared.exe")

    if not os.path.exists(exe_path):
        print(f"Error: cloudflared.exe not found at {exe_path}", flush=True)
        return

    cmd = [exe_path, "tunnel", "--url", "http://localhost:5001"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    tunnel_url = None
    try:
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            m = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
            if m:
                tunnel_url = m.group(1)
                print("\n" + "=" * 65, flush=True)
                print("  [SUCCESS] TUNNEL IS LIVE! SHARE THIS LINK WITH ANY SYSTEM:", flush=True)
                print(f"  >>>  {tunnel_url}  <<<", flush=True)
                print("=" * 65, flush=True)
                print("  (Press Ctrl+C anytime to stop the tunnel)\n", flush=True)
            if "error" in line.lower() and "registered" not in line.lower():
                print(line.strip(), flush=True)
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping tunnel...", flush=True)
        proc.terminate()

if __name__ == "__main__":
    start_tunnel()
