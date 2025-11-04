#!/bin/bash

# Ensure SSH service is running
if command -v systemctl >/dev/null 2>&1; then
  systemctl enable ssh.service >/dev/null 2>&1 || true
  systemctl restart ssh.service >/dev/null 2>&1 || systemctl restart sshd.service >/dev/null 2>&1 || true
fi

# Create and enable a 4GB swap file
if ! grep -q '/swapfile' /etc/fstab; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Create user and project directory
if ! id "freqtrade" &>/dev/null; then
    useradd -m -s /bin/bash freqtrade
fi
PROJECT_DIR="/home/freqtrade/freqtrade"
mkdir -p "$PROJECT_DIR"
chown -R freqtrade:freqtrade /home/freqtrade

# Clone the repository ONLY if the directory is empty
if [ -z "$(ls -A $PROJECT_DIR)" ]; then
  echo "Cloning repository..."
  sudo -u freqtrade git clone https://github.com/HaoweiChan/FreqTrade.git "$PROJECT_DIR"
fi
