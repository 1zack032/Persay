web: gunicorn --workers 1 --threads 2 --timeout 60 --preload --max-requests 100 --max-requests-jitter 20 --bind 0.0.0.0:$PORT app:app

