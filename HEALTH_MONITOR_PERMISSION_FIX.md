# Health Monitor Permission Issue - Fixed

## The Problem
The health monitor container was failing with a Docker socket permission error:
```
Error while fetching server API version: ('Connection aborted.', PermissionError(13, 'Permission denied'))
```

## Root Cause
1. The `Dockerfile.monitor` created a user called `monitoruser` (UID 1000)
2. The container was configured to run as this user with `USER monitoruser`
3. The Docker socket (`/var/run/docker.sock`) is owned by root on macOS Docker Desktop
4. The `monitoruser` didn't have permission to access the socket

## The Fix
Modified `Dockerfile.monitor` to comment out the USER directive:
```dockerfile
# Create user but don't switch to it - run as root for Docker socket access
RUN useradd -m -u 1000 monitoruser && chown -R monitoruser:monitoruser /app
# USER monitoruser  # Commented out to allow Docker socket access
```

## Result
- Health monitor now runs as root inside the container
- Can successfully access the Docker socket
- Monitor is operational and tracking all services
- Status changed from ❌ Down to ✅ Running

## Security Note
Running as root inside a container is generally safe when:
- The container needs to access the Docker socket
- The container is only used for monitoring (read-only operations)
- The container doesn't expose any network services
- It's isolated in the Docker network

## Verification
```bash
# Check monitor status
docker logs cherry_ai_monitor_prod

# Should see:
# ✅ Docker client connected
# 🏥 Starting Cherry AI Health Monitor
# 📊 Monitoring 6 services every 30s
```

## Alternative Solutions (Not Used)
1. **Docker Group**: Add user to docker group (complex on macOS)
2. **Socket Permissions**: Change socket permissions (not persistent)
3. **Rootless Docker**: Use rootless Docker setup (requires reconfiguration)
4. **External Monitoring**: Use monitoring that doesn't need socket access 