import argparse
import socket
import subprocess
from pathlib import Path

NGINX_CONFIG_FILE = """server {
    listen 80;
    server_name localhost;
    {ssl_redirect}
}

server {
    {ssl_listen}
    server_name localhost;

    {ssl_includes}

    # Serve the React app
    root /var/www/cocktailberry_web_client;
    index index.html;

    # Handle React app routes
    location / {
        try_files $uri /index.html;
        # Add cache control headers
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    }

    # Proxy API requests to FastAPI
    location /api/ {
      # rewrite ^/api/(.*)$ /$1 break;
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Master-Key $http_x_master_key;
      proxy_set_header X-Maker-Key $http_x_maker_key;
    }
}
"""

SELF_SIGNED_CONF = """ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
"""

SSL_PARAMS_CONF = """ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_dhparam /etc/ssl/certs/dhparam.pem;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_ecdh_curve secp384r1;
ssl_session_timeout  10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
"""


def get_ip():
    """Retrieve the actual IP address of the Raspberry Pi on the local network."""
    try:
        # Create a socket connection to identify the correct network interface
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to an external address (doesn't need to be reachable)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error retrieving IP address: {e}")
        return "127.0.0.1"


def setup_nginx(use_ssl):
    """Install and configures Nginx to serve a React app."""
    config_path = Path("/etc/nginx/sites-available/cocktailberry_web_client")
    config_path_enabled = Path("/etc/nginx/sites-enabled/cocktailberry_web_client")
    web_root = Path("/var/www/cocktailberry_web_client")
    try:
        # Install Nginx
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "nginx"], check=True)

        if use_ssl:
            # Generate a self-signed SSL certificate
            subprocess.run(
                [
                    "sudo",
                    "openssl",
                    "req",
                    "-x509",
                    "-nodes",
                    "-days",
                    "825",
                    "-newkey",
                    "rsa:2048",
                    "-keyout",
                    "/etc/ssl/private/nginx-selfsigned.key",
                    "-out",
                    "/etc/ssl/certs/nginx-selfsigned.crt",
                    "-subj",
                    "/C=US/ST=State/L=City/O=CocktailBerry/OU=OrgUnit/CN=cocktailberry",
                ],
                check=True,
            )

            # Download a pre-generated Diffie-Hellman group
            subprocess.run(
                ["sudo", "curl", "-o", "/etc/ssl/certs/dhparam.pem", "https://ssl-config.mozilla.org/ffdhe2048.txt"],
                check=True,
            )

            # Create configuration snippets for SSL
            Path("/etc/nginx/snippets/self-signed.conf").write_text(SELF_SIGNED_CONF)
            Path("/etc/nginx/snippets/ssl-params.conf").write_text(SSL_PARAMS_CONF)

        # Create the web root directory if it doesn't exist, clear it if it does
        web_root.mkdir(parents=True, exist_ok=True)
        for file in web_root.glob("*"):
            file.unlink()

        # Write the Nginx configuration file
        nginx_config = NGINX_CONFIG_FILE.format(
            ssl_redirect="return 301 https://$host$request_uri;" if use_ssl else "",
            ssl_listen="listen 443 ssl;" if use_ssl else "listen 80;",
            ssl_includes="include snippets/self-signed.conf;\n    include snippets/ssl-params.conf;" if use_ssl else "",
        )
        config_path.write_text(nginx_config)

        # Enable the configuration
        if not config_path_enabled.exists():
            config_path_enabled.symlink_to(config_path)

        # Restart Nginx to apply changes
        subprocess.run(["sudo", "systemctl", "restart", "nginx"], check=True)

        # Retrieve hostname and IP
        hostname = socket.gethostname()
        ip_address = get_ip()
        prefix = "https" if use_ssl else "http"
        print(f"HTTPS URL (hostname): {prefix}://{hostname}.local")
        print(f"HTTPS URL (IP): {prefix}://{ip_address}")

        print("Nginx has been successfully installed and configured.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Nginx to serve a React app.")
    parser.add_argument(
        "-s",
        "--ssl",
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Use SSL for the Nginx configuration.",
    )
    args = parser.parse_args()
    setup_nginx(args.use_ssl)
