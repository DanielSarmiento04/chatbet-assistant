# Proxy Configuration for ChatBet Frontend

This directory contains all the NGINX configuration files needed for the Docker container.

## Files Structure

```
proxy/
├── nginx.conf              # Main NGINX configuration
├── conf.d/
│   ├── default.conf        # HTTP server configuration
│   └── https.conf.example  # HTTPS configuration template
└── ssl/
    ├── README.md          # SSL certificate instructions
    └── [certificate files] # Your SSL certificates go here
```

## Configuration Files

### `nginx.conf`
Main NGINX configuration with:
- Basic security headers
- Gzip compression
- Rate limiting
- Worker process optimization

### `conf.d/default.conf`
HTTP server configuration with:
- Angular SPA routing support
- Static file caching
- Security headers
- Health check endpoint

### `conf.d/https.conf.example`
HTTPS configuration template:
- SSL/TLS settings
- HTTP to HTTPS redirect
- Enhanced security headers
- Same configuration as HTTP version

## How to Use

### For Development (HTTP only)
The default configuration is ready to use. Just build and run the Docker container:

```bash
docker build -t chatbet-frontend .
docker run -p 80:80 chatbet-frontend
```

### For Production (HTTPS)
1. Add your SSL certificates to `proxy/ssl/`:
   - `cert.pem` - Your SSL certificate
   - `key.pem` - Your private key
   - `dhparam.pem` - Diffie-Hellman parameters (optional)

2. Copy and modify the HTTPS configuration:
   ```bash
   cp proxy/conf.d/https.conf.example proxy/conf.d/https.conf
   ```

3. Edit `https.conf` and update:
   - `server_name` with your actual domain
   - SSL certificate paths if different

4. Build and run with HTTPS:
   ```bash
   docker build -t chatbet-frontend .
   docker run -p 80:80 -p 443:443 chatbet-frontend
   ```

## Backend Integration

This configuration serves the frontend as a standalone application. The Angular app will need to connect directly to your backend API using the configured API URLs in the environment files.

Update your Angular environment files to point to your backend:

```typescript
// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://your-backend-api.com/api',
  wsUrl: 'wss://your-backend-api.com/ws'
};
```

## Customization

### Adding Backend Proxy (Optional)
If you want to proxy API requests through NGINX, edit `proxy/conf.d/default.conf` and add:

```nginx
# Proxy API requests to backend
location /api/ {
    proxy_pass http://your-backend-host:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Proxy WebSocket connections
location /ws/ {
    proxy_pass http://your-backend-host:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

### Security Headers
Modify the security headers in both `nginx.conf` and the server configurations as needed for your domain and security requirements.

### Rate Limiting
Adjust rate limiting in `nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

## Troubleshooting

### Common Issues
1. **502 Bad Gateway**: Backend service not reachable
   - Check if backend container is running
   - Verify network connectivity between containers

2. **SSL Certificate Errors**: Invalid or missing certificates
   - Ensure certificate files exist in `proxy/ssl/`
   - Check certificate format and validity

3. **WebSocket Connection Failed**: Proxy configuration issue
   - Verify WebSocket proxy settings in server config
   - Check backend WebSocket endpoint

### Logs
Check NGINX logs inside the container:
```bash
docker exec -it <container-name> tail -f /var/log/nginx/access.log
docker exec -it <container-name> tail -f /var/log/nginx/error.log
```