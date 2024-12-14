import subprocess
from pathlib import Path


def setup_nginx(
    config_path="/etc/nginx/sites-available/cocktailberry_web_client",
    web_root="/var/www/cocktailberry_web_client",
    server_name="localhost",
):
    """Install and configures Nginx to serve a React app.

    :param config_path: Path to the Nginx configuration file.
    :param web_root: Directory where the React app's build files are located.
    :param server_name: The server name (e.g., localhost or domain).
    """
    try:
        # Install Nginx
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "nginx"], check=True)

        # Create the web root directory if it doesn't exist
        Path(web_root).mkdir(parents=True, exist_ok=True)

        # Create Nginx configuration
        nginx_config = f"""
        server {{
            listen 80;
            server_name {server_name};

            root {web_root};
            index index.html;

            location / {{
                try_files $uri /index.html;
            }}
        }}
        """

        # Write the configuration to the file
        config_path = Path(config_path)
        config_path.write_text(nginx_config)

        # Enable the site
        subprocess.run(
            ["sudo", "ln", "-s", str(config_path), "/etc/nginx/sites-enabled/cocktailberry_web_client"], check=True
        )

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
