import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as c:
    print(c.execute(text('SELECT * FROM hepatwin_compounds LIMIT 0')).keys())
