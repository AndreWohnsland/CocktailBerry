import subprocess
from pathlib import Path

from src.filepath import NGINX_CONFIG_FILE


def setup_nginx():
    """Install and configures Nginx to serve a React app."""
    config_path = Path("/etc/nginx/sites-available/cocktailberry_web_client")
    config_path_enabled = Path("/etc/nginx/sites-enabled/cocktailberry_web_client")
    web_root = Path("/var/www/cocktailberry_web_client")
    try:
        # Install Nginx
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "nginx"], check=True)

        # Create the web root directory if it doesn't exist
        web_root.mkdir(parents=True, exist_ok=True)
        config_path.write_text(NGINX_CONFIG_FILE.read_text())

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
