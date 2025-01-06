import subprocess
from pathlib import Path

service_content = """[Unit]
Description=Squeekboard Virtual Keyboard
After=display-manager.service
Wants=graphical.target

[Service]
ExecStart=/usr/bin/squeekboard
Restart=always
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000

[Install]
WantedBy=graphical.target
"""

service_name = "squeekboard.service"


def create_and_start_squeekboard_service():
    service_path = Path("/etc/systemd/system") / service_name
    # Write the service content to the file using sudo
    with subprocess.Popen(["sudo", "tee", str(service_path)], stdin=subprocess.PIPE) as process:
        process.communicate(input=service_content.encode())

    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
    subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
    print("Squeekboard service created, enabled, and started successfully.")


def stop_and_disable_squeekboard_service():
    subprocess.run(["sudo", "systemctl", "stop", service_name], check=True)
    subprocess.run(["sudo", "systemctl", "disable", service_name], check=True)
    print("Squeekboard service stopped and disabled successfully.")
