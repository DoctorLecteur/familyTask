from app import app, db
from app.models import Users

@app.shell_context_processors
def make_shell_context():
    return {'db': db, 'Users': Users}