import os
import sys

try:
    from . import create_app
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from club_management import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
