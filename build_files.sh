#!/bin/bash
echo "Building project assets for Vercel deployment..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
python3 manage.py migrate --noinput
python3 manage.py seed_data
echo "Build complete."

