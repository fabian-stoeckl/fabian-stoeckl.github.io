"""Single-service supervisor: API plus optional research process, shared private disk."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
children=[]
def stop(*args):
    for child in children:
        child.terminate()
    for child in children:
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill()
    sys.exit(0)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
children.append(subprocess.Popen([sys.executable,'server.py']))
if os.environ.get('PAPER_AUTOMATION')=='1':
    children.append(subprocess.Popen([sys.executable,'research.py']))
while all(child.poll() is None for child in children):
    time.sleep(1)
stop()
