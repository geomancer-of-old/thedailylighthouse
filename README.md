# The Daily Lighthouse

A deliberately insecure server-side-rendered newspaper (Flask + Jinja2 + SQLite)
for teaching web vulnerabilities. **Run only on an isolated lab network.**


## Run it

```bash
# Local
pip install -r requirements.txt
python db.py          # seed the database
python app.py         # http://localhost:5000

```

Reset between attempts: `rm -f lighthouse.db* uploads/* && python db.py`

