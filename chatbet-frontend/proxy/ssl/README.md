# SSL Certificate Files

This directory should contain your SSL certificates for HTTPS configuration.

## Required files for HTTPS:

- `cert.pem` - Your SSL certificate
- `key.pem` - Your private key
- `dhparam.pem` - Diffie-Hellman parameters (optional but recommended)

## Generate self-signed certificates for development:

```bash
# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate signing request
openssl req -new -key key.pem -out csr.pem

# Generate self-signed certificate
openssl x509 -req -days 365 -in csr.pem -signkey key.pem -out cert.pem

# Generate Diffie-Hellman parameters
openssl dhparam -out dhparam.pem 2048
```

## For production:

Use certificates from a trusted Certificate Authority like:
- Let's Encrypt (free)
- Cloudflare
- DigiCert
- etc.

## Note:

Never commit real SSL certificates to version control!
Add `*.pem`, `*.key`, `*.crt` to your `.gitignore` file.
