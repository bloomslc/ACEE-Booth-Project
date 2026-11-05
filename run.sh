lxterminal --command="cd backend && python3 -m gunicorn app:app --host 0.0.0.0 --port 8080" &
lxterminal --command="cd frontend && python3 main.py" &