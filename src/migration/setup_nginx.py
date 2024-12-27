import subprocess
from pathlib import Path

NGINX_CONFIG_FILE = """server {
    listen 80;
    server_name localhost;

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
      proxy_pass_request_headers on;
      proxy_set_header X-Master-Key $http_x_master_key;
      proxy_set_header X-Maker-Key $http_x_maker_key;
    }
}
"""


def setup_nginx():
    """Install and configures Nginx to serve a React app."""
    config_path = Path("/etc/nginx/sites-available/cocktailberry_web_client")
    config_path_enabled = Path("/etc/nginx/sites-enabled/cocktailberry_web_client")
    web_root = Path("/var/www/cocktailberry_web_client")
    try:
        # Install Nginx
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "nginx"], check=True)

        # Create the web root directory if it doesn't exist, clear it if it does
        web_root.mkdir(parents=True, exist_ok=True)
        for file in web_root.glob("*"):
            file.unlink()
        tmp_path = Path("/tmp/cocktailberry_web_client.tar.gz")
        url = "https://github.com/AndreWohnsland/CocktailBerry/releases/latest/download/cocktailberry_web_client.tar.gz"

        # Download the tar.gz file to the tmp directory, extract it into the web root directory, remove the tar.gz file
        subprocess.run(["sudo", "curl", "-L", "-o", str(tmp_path), url], check=True)
        subprocess.run(["sudo", "tar", "-xzf", str(tmp_path), "-C", str(web_root)], check=True)
        tmp_path.unlink()
        config_path.write_text(NGINX_CONFIG_FILE)

        # Remove existing symbolic link if it exists
        if config_path_enabled.exists():
            config_path_enabled.unlink()

        # Enable the site
        subprocess.run(["sudo", "ln", "-s", str(config_path), str(config_path_enabled)], check=True)

        # Remove default Nginx site if exists
        default_path = Path("/etc/nginx/sites-enabled/default")
        if default_path.exists():
            default_path.unlink()

        # Restart Nginx to apply changes
        subprocess.run(["sudo", "systemctl", "restart", "nginx"], check=True)

        print("Nginx has been successfully installed and configured.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    setup_nginx()
