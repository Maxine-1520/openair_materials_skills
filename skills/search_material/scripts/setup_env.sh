#!/bin/bash
# Setup environment for MP Material Search

# Install dependencies
pip install -r ../requirements.txt

# Check for MP_API_KEY
if [ -z "$MP_API_KEY" ]; then
    echo "MP_API_KEY not set. Please either:"
    echo "  1. Set environment variable: export MP_API_KEY=your_key"
    echo "  2. Or create a .env file with: MP_API_KEY=your_key"
fi
