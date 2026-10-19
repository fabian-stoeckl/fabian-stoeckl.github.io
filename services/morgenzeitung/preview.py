"""Create an isolated preview DB. Never point this at production storage."""
import json
import sys
from pathlib import Path
from core import Store, now
path=Path(sys.argv[1])
if path.exists():
    raise SystemExit('Vorschaupfad existiert bereits; anderen Pfad wählen')
store=Store(path)
e=json.loads(Path(__file__).with_name('preview.json').read_text())
e['researched_at']=now()
store.publish(e)
print('Vorschau erstellt')
