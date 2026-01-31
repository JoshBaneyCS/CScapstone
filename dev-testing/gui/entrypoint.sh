#!/bin/bash
set -e

echo "Starting Dev Testing Environment - GUI Container"
echo "=================================================="
echo "Display: :99 (1920x1080)"
echo "VNC Port: 5900"
echo "noVNC Port: 6080"
echo "VNC Password: casino123"
echo ""

export DISPLAY=:99

echo "Starting supervisor to manage all processes..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
