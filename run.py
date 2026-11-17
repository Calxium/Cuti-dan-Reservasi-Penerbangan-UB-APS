from app import create_app
from app.models import db
import seed_data

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Aplikasi QUIZ 2 APS berjalan pada: http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
