#!/usr/bin/python3
# File name   : setup.py
# Author      : Adeept Devin
# Date        : 2022/7/12

import os
import getpass
import signal
import sys

cur_path = os.path.realpath(__file__)
this_path = os.path.dirname(cur_path)

# Get current user dynamically
current_user = getpass.getuser()
user_home = os.path.expanduser("~")
venv_path = os.path.join(user_home, ".venv")


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


def check_uv_available():
    """Check if uv is available in PATH"""
    return os.system("which uv > /dev/null 2>&1") == 0


def test_package_installation():
    """Test if critical packages can be imported"""
    print("\n=== Testing Package Installation ===")
    test_packages = [
        "adafruit_motor",
        "flask",
        "RPi.GPIO"
    ]

    all_good = True
    for package in test_packages:
        try:
            if use_uv:
                # Test in virtual environment
                test_cmd = f"source {venv_path}/bin/activate && python3 -c 'import {package}; print(\"✓ {package} imported successfully\")'"
                if run_command_with_interrupt_check(test_cmd):
                    continue
                else:
                    print(f"✗ {package} import failed")
                    all_good = False
            else:
                # Test with current python
                result = os.system(f"python3 -c 'import {package}' > /dev/null 2>&1")
                if result == 0:
                    print(f"✓ {package} imported successfully")
                else:
                    print(f"✗ {package} import failed")
                    all_good = False
        except:
            print(f"✗ {package} test failed")
            all_good = False

    return all_good


def fix_installation_if_needed():
    """Fix common installation issues"""
    print("\n=== Checking and Fixing Installation ===")

    # Check if virtual environment exists when using uv
    if use_uv and not os.path.exists(venv_path):
        print("Virtual environment missing, recreating...")
        if run_command_with_interrupt_check(f"uv venv {venv_path}"):
            print("Virtual environment recreated successfully")
        else:
            print("Failed to recreate virtual environment")
            return False

    # Test package installation
    if not test_package_installation():
        print("\nSome packages failed to import. Attempting to reinstall...")

        # Reinstall critical packages
        critical_packages = [
            "adafruit-circuitpython-motor",
            "adafruit-circuitpython-pca9685",
            "flask",
            "flask_cors",
            "websockets",
            "psutil",
            "RPi.GPIO",
            "rpi_ws281x",
            "mpu6050-raspberrypi",
            "luma.oled"
        ]

        for package in critical_packages:
            if use_uv:
                run_command_with_interrupt_check(f"uv pip install {package}")
            else:
                run_command_with_interrupt_check(f"pip3 install --user {package}")

        # Test again
        if test_package_installation():
            print("✓ Package installation fixed!")
            return True
        else:
            print("✗ Package installation still has issues")
            return False
    else:
        print("✓ All packages imported successfully")
        return True


def create_systemd_service(startup_script_path):
    """
    Create a systemd service for auto-starting the robot server
    """
    service_name = "robot-server.service"
    service_path = f"/etc/systemd/system/{service_name}"

    # Include proper PATH for uv and virtual environment
    env_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    if use_uv:
        env_path = f"{user_home}/.local/bin:{env_path}"

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
Environment=PATH={env_path}

[Install]
WantedBy=multi-user.target
"""

    try:
        # Write to temp file first
        temp_path = f"/tmp/{service_name}"
        with open(temp_path, 'w') as f:
            f.write(service_content)

        # Move with sudo
        os.system(f"sudo mv {temp_path} {service_path}")
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



use_uv = True  # hardcoded - we are using the uv base image, should be there!
# Create virtual environment with uv if available
print("Creating virtual environment with uv...")
if not os.path.exists(venv_path):
    run_command_with_interrupt_check(f"uv venv {venv_path}")

# Set environment variables to use the virtual environment
os.environ["VIRTUAL_ENV"] = venv_path
os.environ["PATH"] = f"{venv_path}/bin:{os.environ['PATH']}"
pip_cmd = "uv pip install"
print(f"Using virtual environment at {venv_path}")

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
    f"{pip_cmd} psutil",
    f"{pip_cmd} smbus",
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
        # Read the file
        with open(file, "r") as f:
            for line in f.readlines():
                if (line.find(initial) == 0):
                    line = (str_num + '\n')
                newline += line

        # Write to temp file first, then move with sudo
        temp_file = f"/tmp/config_temp_{os.getpid()}.txt"
        with open(temp_file, "w") as f:
            f.writelines(newline)

        # Move with sudo
        result = os.system(f"sudo cp {temp_file} {file}")
        os.system(f"rm {temp_file}")  # Clean up temp file

        if result != 0:
            print(f"Error: Failed to update {file} with sudo")
        else:
            print(f"Successfully updated {file}")

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
                if os.path.exists(new_config):
                    replace_num(new_config, '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')
                else:
                    print(f"Warning: {new_config} not found")
            else:
                # Old config is the real one, use it
                print("Using old config location")
                replace_num(old_config, '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')
        else:
            # Old config doesn't exist, must be new system
            print("Old config not found, using new location")
            if os.path.exists(new_config):
                replace_num(new_config, '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')
            else:
                print(f"Warning: {new_config} not found")

        print('Boot config update completed')

    except Exception as e:
        print(f'Error updating boot config: {e}')


try:
    update_boot_config()
except:
    print('Error updating boot config to enable i2c. Please try again.')

# Run installation verification and fix
try:
    if not fix_installation_if_needed():
        print("\n⚠️  Warning: Some packages may not be properly installed")
        print("You may need to manually install missing packages after reboot")
except Exception as e:
    print(f"Error during installation verification: {e}")

# Create startup script
try:
    startup_script_path = os.path.join(user_home, "startup.sh")
    with open(startup_script_path, 'w') as file_to_write:
        if use_uv:
            # Use the virtual environment in the startup script
            file_to_write.write(f"#!/bin/bash\n")
            file_to_write.write(f"export PATH={user_home}/.local/bin:$PATH\n")
            file_to_write.write(f"source {venv_path}/bin/activate\n")
            file_to_write.write(f"python3 {this_path}/server/webServer.py\n")
        else:
            file_to_write.write(f"#!/bin/bash\n")
            file_to_write.write(f"export PATH={user_home}/.local/bin:$PATH\n")
            file_to_write.write(f"python3 {this_path}/server/webServer.py\n")

    # Make startup script executable
    os.system(f'chmod +x {startup_script_path}')

    # Try systemd service first, fallback to cron
    print(f"Startup script created at: {startup_script_path}")
    print(f"Virtual environment: {venv_path if use_uv else 'Not using virtual environment'}")

    if not create_systemd_service(startup_script_path):
        print("Systemd service creation failed, trying crontab...")
        create_cron_alternative(startup_script_path)

except Exception as e:
    print(f"Error creating startup configuration: {e}")

print('\n=== Installation Summary ===')
print(f'Package manager: {"uv with virtual environment" if use_uv else "pip3 with --user"}')
print(f'Startup script: {startup_script_path}')
print(f'Service: robot-server.service')
print('\nThe program in Raspberry Pi has been installed, disconnected and restarted.')
print('You can now power off the Raspberry Pi to install the camera and driver board (Robot HAT).')
print(
    'After turning on again, the Raspberry Pi will automatically run the program to set the servos port signal to turn the servos to the middle position, which is convenient for mechanical assembly.')
print('\nTo check status after reboot: sudo systemctl status robot-server')
print('To view logs: sudo journalctl -u robot-server -f')
print('restarting...')
os.system("sudo reboot")