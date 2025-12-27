#!/bin/bash

echo "========================================"
echo "PPT Generator Setup Script"
echo "========================================"
echo ""

echo "[1/3] Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    echo "Please make sure Python 3 and pip are installed"
    exit 1
fi
echo "[OK] Dependencies installed"
echo ""

echo "[2/3] Creating config.yaml from template..."
if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo "[OK] config.yaml created"
else
    echo "[INFO] config.yaml already exists, skipping..."
fi
echo ""

echo "[3/3] Setup complete!"
echo ""
echo "========================================"
echo "NEXT STEPS:"
echo "========================================"
echo "1. Edit config.yaml and add your API keys"
echo "2. Run: python3 generate_ppt_from_pdf.py \"your_file.pdf\""
echo ""

read -p "Press Enter to open config.yaml for editing..."
nano config.yaml || vi config.yaml || open config.yaml

