web: gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --timeout 60 --keep-alive 5 --max-requests 500 --max-requests-jitter 50 --graceful-timeout 30 --worker-class uvicorn.workers.UvicornWorker --worker-tmp-dir /dev/shm