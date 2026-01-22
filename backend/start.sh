#!/bin/sh
set -e

# 1. Start Tailscale (IPv4 mode)
/usr/local/bin/tailscaled \
    --tun=userspace-networking \
    --socks5-server=127.0.0.1:1055 \
    --state=mem: &

# 2. Authenticate
echo "⏳ Connecting to Tailscale..."
until /usr/local/bin/tailscale up --authkey=${TS_AUTHKEY} --hostname=kako-api-${K_REVISION:-default}; do
    echo "zzz... waiting for tailscaled"
    sleep 1
done

# 3. Configure HTTP Proxies (For standard web requests)
export ALL_PROXY=socks5h://127.0.0.1:1055
export HTTP_PROXY=socks5h://127.0.0.1:1055
export HTTPS_PROXY=socks5h://127.0.0.1:1055
export NO_PROXY=metadata.google.internal,169.254.169.254,localhost,127.0.0.1,.googleapis.com

# ----------------------------------------------------------------
# 4. 🌉 THE BRIDGE: SSH Tunnel via socat
# ----------------------------------------------------------------
# Logic: Listen on Local:2222 -> Pipe to SOCKS Proxy -> Pipe to Real SSH_HOST
echo "bridge: Creating SSH tunnel 127.0.0.1:2222 -> ${SSH_HOST}:${SSH_PORT}"
# Note: We keep the ORIGINAL SSH_HOST/PORT here for socat to use
socat TCP4-LISTEN:2222,fork,bind=127.0.0.1 SOCKS5:127.0.0.1:${SSH_HOST}:${SSH_PORT},socksport=1055 &

# 5. OVERRIDE Variables for Python
# Now we tell Python: "Connect to localhost:2222" (The Bridge)
export SSH_HOST=127.0.0.1
export SSH_PORT=2222
# ----------------------------------------------------------------

echo "✅ Network ready. Starting App..."

# 6. Start App
exec uvicorn backend.src.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --proxy-headers \
    --forwarded-allow-ips '*'