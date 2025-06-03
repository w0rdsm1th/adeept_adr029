#!/usr/bin/python3
# File name   : setup.py
# Author      : Adeept Devin
# Date        : 2022/7/12

import os
import time
import getpass
import signal
import sys

cur_path = os.path.realpath(__file__)
this_path = os.path.dirname(cur_path)

# Get current user dynamically
current_user = getpass.getuser()
user_home = os.path.expanduser("~")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nInstallation interrupted by user (Ctrl+C)")
    print("Cleaning up...")
    # Add any cleanup code here if needed
    sys.exit(1)


# Set up signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)


def run_command_with_interrupt_check(command):
    """Run a command but allow interruption"""
    print(f"Running: {command}")
    try:
        result = os.system(command)
        if result != 0:
            return False
        return True
    except KeyboardInterrupt:
        print(f"\nCommand interrupted: {command}")
        raise


def install_uv():
    """Install uv package manager if not already installed"""
    print("Installing uv package manager...")
    if not run_command_with_interrupt_check("curl -LsSf https://astral.sh/uv/install.sh | sh"):
        print("Error installing uv. Falling back to pip.")
        return False

    # Add uv to PATH for this session
    uv_path = os.path.join(user_home, ".cargo/bin")
    current_path = os.environ.get("PATH", "")
    if uv_path not in current_path:
        os.environ["PATH"] = f"{uv_path}:{current_path}"

    return True


def check_uv_available():
    """Check if uv is available in PATH"""
    return os.system("which uv > /dev/null 2>&1") == 0


# Create systemd service instead of using rc.local
def create_systemd_service(startup_script_path):
    """Create a systemd service for auto-starting the robot server"""
    service_name = "robot-server.service"
    service_path = f"/etc/systemd/system/{service_name}"

    service_content = f"""[Unit]
Description=Robot Server
After=network.target
Wants=network.target

[Service]
Type=simple
User={current_user}
Group={current_user}
WorkingDirectory={this_path}
ExecStart={startup_script_path}
Restart=always
RestartSec=5
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
"""

    try:
        # Write the service file
        with open(service_path, 'w') as f:
            f.write(service_content)

        # Set proper permissions
        os.system(f"sudo chmod 644 {service_path}")

        # Reload systemd and enable the service
        os.system("sudo systemctl daemon-reload")
        os.system(f"sudo systemctl enable {service_name}")

        print(f"Created systemd service: {service_name}")
        return True

    except Exception as e:
        print(f"Error creating systemd service: {e}")
        return False


def create_cron_alternative(startup_script_path):
    """Alternative: Add to user's crontab for @reboot"""
    try:
        # Add to user's crontab
        cron_line = f"@reboot {startup_script_path}"
        os.system(f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -')
        print("Added startup script to crontab")
        return True
    except Exception as e:
        print(f"Error adding to crontab: {e}")
        return False


# Install uv first
use_uv = False
try:
    if not check_uv_available():
        use_uv = install_uv()
    else:
        use_uv = True

    # Create virtual environment with uv if available
    if use_uv:
        print("Creating virtual environment with uv...")
        venv_path = os.path.join(user_home, ".venv")
        run_command_with_interrupt_check(f"uv venv {venv_path}")
        # Set environment variables to use the virtual environment
        os.environ["VIRTUAL_ENV"] = venv_path
        os.environ["PATH"] = f"{venv_path}/bin:{os.environ['PATH']}"
        pip_cmd = "uv pip install"
        print(f"Using virtual environment at {venv_path}")
    else:
        pip_cmd = "pip3 install --user"
        print("Using pip with --user flag as fallback")
except KeyboardInterrupt:
    print("\nSetup interrupted during uv installation")
    sys.exit(1)

commands_1 = [
    "sudo apt-get update",
    "sudo apt-get purge -y wolfram-engine",
    "sudo apt-get purge -y libreoffice*",
    "sudo apt-get -y clean",
    "sudo apt-get -y autoremove",
    "sudo apt-get install -y python3-dev python3-pip libfreetype6-dev libjpeg-dev build-essential",
    "sudo apt-get install -y i2c-tools",
    f"{pip_cmd} --upgrade luma.oled",
    f"{pip_cmd} rpi_ws281x",
    "sudo apt-get install -y python3-smbus",
    f"{pip_cmd} mpu6050-raspberrypi",
    f"{pip_cmd} flask",
    f"{pip_cmd} flask_cors",
    f"{pip_cmd} websockets",
    "sudo apt-get install -y libjasper-dev",
    "sudo apt-get install -y libatlas-base-dev",
    "sudo apt-get install -y libgstreamer1.0-0",
    f"{pip_cmd} adafruit-circuitpython-motor",
    f"{pip_cmd} adafruit-circuitpython-pca9685"
]

mark_1 = 0
for x in range(3):
    try:
        for command in commands_1:
            if not run_command_with_interrupt_check(command):
                print("Error running installation step 1")
                mark_1 = 1
                break
        if mark_1 == 0:
            break
    except KeyboardInterrupt:
        print("\nInstallation step 1 interrupted")
        sys.exit(1)

commands_2 = [
    f"{pip_cmd} RPi.GPIO",
    "sudo apt-get -y install libqtgui4 libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqt4-test",
    "sudo git clone https://github.com/oblique/create_ap",
    "cd " + this_path + "/create_ap && sudo make install",
    f"cd {user_home}/create_ap && sudo make install",
    "sudo apt-get install -y util-linux procps hostapd iproute2 iw haveged dnsmasq"
]

mark_2 = 0
for x in range(3):
    try:
        for command in commands_2:
            if not run_command_with_interrupt_check(command):
                print("Error running installation step 2")
                mark_2 = 1
                break
        if mark_2 == 0:
            break
    except KeyboardInterrupt:
        print("\nInstallation step 2 interrupted")
        sys.exit(1)


def replace_num(file, initial, new_num):
    newline = ""
    str_num = str(new_num)
    try:
        with open(file, "r") as f:
            for line in f.readlines():
                if (line.find(initial) == 0):
                    line = (str_num + '\n')
                newline += line
        with open(file, "w") as f:
            f.writelines(newline)
    except FileNotFoundError:
        print(f"Warning: {file} not found, skipping configuration")
    except Exception as e:
        print(f"Error modifying {file}: {e}")


def update_boot_config():
    """Intelligently update boot config in the correct location"""
    old_config = "/boot/config.txt"
    new_config = "/boot/firmware/config.txt"

    try:
        # Check if old config exists and what it contains
        if os.path.exists(old_config):
            with open(old_config, 'r') as f:
                content = f.read()

            # If it contains the redirect warning, use new location
            if "DO NOT EDIT" in content.upper() or "moved to" in content:
                print("Old config is a redirect, using new location")
                replace_num(new_config, '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')
            else:
                # Old config is the real one, use it
                print("Using old config location")
                replace_num(old_config, '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')
        else:
            # Old config doesn't exist, must be new system
            print("Old config not found, using new location")
            replace_num(new_config, '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')

        print('Updated boot config to enable i2c and camera')

    except Exception as e:
        print(f'Error updating boot config: {e}')


try:
    update_boot_config()
except:
    print('Error updating boot config to enable i2c. Please try again.')

try:
    startup_script_path = os.path.join(user_home, "startup.sh")
    os.system(f'touch {startup_script_path}')
    with open(startup_script_path, 'w') as file_to_write:
        # you can choose how to control the robot
        if use_uv:
            # Use the virtual environment in the startup script
            file_to_write.write(
                f"#!/bin/bash\nsource {venv_path}/bin/activate\npython3 " + this_path + "/server/webServer.py\n")
        else:
            file_to_write.write("#!/bin/bash\npython3 " + this_path + "/server/webServer.py\n")
    #       file_to_write.write("#!/bin/bash\npython3 " + thisPath + "/server/server.py\n")

    # Make startup script executable
    os.system(f'chmod +x {startup_script_path}')

    # Try systemd service first, fallback to cron
    if not create_systemd_service(startup_script_path):
        print("Systemd service creation failed, trying crontab...")
        create_cron_alternative(startup_script_path)

except Exception as e:
    print(f"Error creating startup configuration: {e}")
    pass

# try:
#     os.system(f"sudo cp -f {user_home}/adeept_adr029/server/config.txt //etc/config.txt")
# except:
#     os.system("sudo cp -f "+ thisPath  +"/adeept_rasptank/server/config.txt //etc/config.txt")
print(
    'The program in Raspberry Pi has been installed, disconnected and restarted. \nYou can now power off the Raspberry Pi to install the camera and driver board (Robot HAT). \nAfter turning on again, the Raspberry Pi will automatically run the program to set the servos port signal to turn the servos to the middle position, which is convenient for mechanical assembly.')
print('restarting...')
os.system("sudo reboot")