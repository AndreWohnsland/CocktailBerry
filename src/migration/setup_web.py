# flake8: noqa: E501

import argparse
import shutil
import socket
import subprocess
from pathlib import Path

COMMON_SERVER_BLOCK = """server_name localhost;

    # Serve the React app
    root /var/www/cocktailberry_web_client;
    index index.html;

    # Handle React app routes
    location / {
        try_files $uri /index.html;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    }

    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Master-Key $http_x_master_key;
        proxy_set_header X-Maker-Key $http_x_maker_key;
    }
"""

NON_SSL_CONFIG = f"""
server {{
    listen 80;
    {COMMON_SERVER_BLOCK}
}}
"""


SSL_CONFIG = f"""
server {{
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    {COMMON_SERVER_BLOCK}

    # SSL settings
    include snippets/self-signed.conf;
    include snippets/ssl-params.conf;
}}
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


def get_ip() -> str:
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


def download_latest_web_client() -> None:
    """Download the latest web client from the GitHub release page."""
    # Create the web root directory if it doesn't exist
    web_root = Path("/var/www/cocktailberry_web_client")
    web_root.mkdir(parents=True, exist_ok=True)
    # Download the tar.gz file to the tmp directory, extract it into the web root directory, remove the tar.gz file
    tmp_path = Path("/tmp/cocktailberry_web_client.tar.gz")
    url = "https://github.com/AndreWohnsland/CocktailBerry/releases/latest/download/cocktailberry_web_client.tar.gz"
    subprocess.run(["sudo", "curl", "-L", "-o", str(tmp_path), url], check=True)
    for file in web_root.glob("*"):
        if file.is_file():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(file)
    subprocess.run(["sudo", "tar", "-xzf", str(tmp_path), "-C", str(web_root)], check=True)
    tmp_path.unlink()


def setup_nginx(use_ssl: bool) -> None:
    """Install and configures Nginx to serve a React app."""
    config_path = Path("/etc/nginx/sites-available/cocktailberry_web_client")
    config_path_enabled = Path("/etc/nginx/sites-enabled/cocktailberry_web_client")
    default_site = Path("/etc/nginx/sites-enabled/default")
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

            config_path.write_text(SSL_CONFIG)
        else:
            config_path.write_text(NON_SSL_CONFIG)

        # Enable the configuration
        if not config_path_enabled.exists():
            config_path_enabled.symlink_to(config_path)

        # remove default site
        if default_site.exists():
            default_site.unlink()

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
    download_latest_web_client()
    setup_nginx(args.ssl)
