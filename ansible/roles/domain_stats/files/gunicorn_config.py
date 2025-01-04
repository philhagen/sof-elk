import gunicorn
import multiprocessing
import os

os.environ["SERVER_SOFTWARE"] = "domain_stats"
bind = "127.0.0.1:5730"
workers = 9
threads = 12
gunicorn.SERVER_SOFTWARE = "domain_stats"
