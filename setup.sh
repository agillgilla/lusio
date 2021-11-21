#!/bin/sh

# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Setup autostart on boot
mkdir /home/pi/.config/autostart
echo '[Desktop Entry]
Name=Lusio
Type=Application
Exec=sudo /usr/bin/python3 /home/pi/lusio/lusio.py
' >> /home/pi/.config/autostart/lusio.desktop

# Disable screen blanking
sudo mkdir -p /etc/X11/xorg.conf.d/
sudo cp /usr/share/raspi-config/10-blanking.conf /etc/X11/xorg.conf.d/
sudo sh -c "printf '\\033[9;0]' >> /etc/issue"

# Install VLC
sudo apt update
sudo apt upgrade
sudo apt install -y vlc

# Install python packages
cd /home/pi/lusio
sudo pip3 install -r requirements.txt

# Disable HDMI-CEC
sudo sh -c "echo '
hdmi_ignore_cec_init=1
hdmi_ignore_cec=1' >> /boot/config.txt"
