web: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --graceful-timeout 30 --worker-class uvicorn.workers.UvicornWorker --worker-tmp-dir /dev/shm --preload