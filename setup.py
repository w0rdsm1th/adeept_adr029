#!/usr/bin/python3
# File name   : setup.py
# Author      : Adeept Devin
# Date        : 2022/7/12

import os
import time
import getpass

curpath = os.path.realpath(__file__)
thisPath = "/" + os.path.dirname(curpath)

# Get current user dynamically
current_user = getpass.getuser()
user_home = os.path.expanduser("~")


def install_uv():
    """Install uv package manager if not already installed"""
    print("Installing uv package manager...")
    if os.system("curl -LsSf https://astral.sh/uv/install.sh | sh") != 0:
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


def replace_num(file, initial, new_num):
    newline = ""
    str_num = str(new_num)
    with open(file, "r") as f:
        for line in f.readlines():
            if (line.find(initial) == 0):
                line = (str_num + '\n')
            newline += line
    with open(file, "w") as f:
        f.writelines(newline)


# Install uv first
use_uv = False
if not check_uv_available():
    use_uv = install_uv()
else:
    use_uv = True

# Create virtual environment with uv if available
if use_uv:
    print("Creating virtual environment with uv...")
    venv_path = os.path.join(user_home, ".venv")
    os.system(f"uv venv {venv_path}")
    # Set environment variables to use the virtual environment
    os.environ["VIRTUAL_ENV"] = venv_path
    os.environ["PATH"] = f"{venv_path}/bin:{os.environ['PATH']}"
    pip_cmd = "uv pip install"
    print(f"Using virtual environment at {venv_path}")
else:
    pip_cmd = "pip3 install --user"
    print("Using pip with --user flag as fallback")

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
    for command in commands_1:
        if os.system(command) != 0:
            print("Error running installation step 1")
            mark_1 = 1
    if mark_1 == 0:
        break

commands_2 = [
    f"{pip_cmd} RPi.GPIO",
    "sudo apt-get -y install libqtgui4 libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqt4-test",
    "sudo git clone https://github.com/oblique/create_ap",
    "cd " + thisPath + "/create_ap && sudo make install",
    f"cd {user_home}/create_ap && sudo make install",
    "sudo apt-get install -y util-linux procps hostapd iproute2 iw haveged dnsmasq"
]

mark_2 = 0
for x in range(3):
    for command in commands_2:
        if os.system(command) != 0:
            print("Error running installation step 2")
            mark_2 = 1
    if mark_2 == 0:
        break

try:
    replace_num("/boot/config.txt", '#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1\n')
except:
    print('Error updating boot config to enable i2c. Please try again.')

try:
    startup_script_path = os.path.join(user_home, "startup.sh")
    os.system(f'sudo touch {startup_script_path}')
    with open(startup_script_path, 'w') as file_to_write:
        # you can choose how to control the robot
        if use_uv:
            # Use the virtual environment in the startup script
            file_to_write.write(
                f"#!/bin/sh\nsource {venv_path}/bin/activate && python3 " + thisPath + "/server/webServer.py")
        else:
            file_to_write.write("#!/bin/sh\npython3 " + thisPath + "/server/webServer.py")
#       file_to_write.write("#!/bin/sh\npython3 " + thisPath + "/server/server.py")
except:
    pass

startup_script_path = os.path.join(user_home, "startup.sh")
os.system(f'sudo chmod 777 {startup_script_path}')

replace_num('/etc/rc.local', 'fi', f'fi\n{startup_script_path} start')

# try:
#     os.system(f"sudo cp -f {user_home}/adeept_adr029/server/config.txt //etc/config.txt")
# except:
#     os.system("sudo cp -f "+ thisPath  +"/adeept_rasptank/server/config.txt //etc/config.txt")
print(
    'The program in Raspberry Pi has been installed, disconnected and restarted. \nYou can now power off the Raspberry Pi to install the camera and driver board (Robot HAT). \nAfter turning on again, the Raspberry Pi will automatically run the program to set the servos port signal to turn the servos to the middle position, which is convenient for mechanical assembly.')
print('restarting...')
os.system("sudo reboot")