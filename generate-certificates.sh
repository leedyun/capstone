#!/bin/bash

# Create certificates directory if it doesn't exist
mkdir -p certificates

# Generate SSL certificate
openssl req -x509 -newkey rsa:2048 -keyout certificates/key.pem -out certificates/cert.pem -days 365 -nodes -subj "/CN=localhost"

echo "SSL certificates generated successfully!" 