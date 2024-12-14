import os
from dotenv import load_dotenv

from flask import Flask, request, abort, jsonify, g
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_migrate import Migrate
from sqlalchemy import create_engine

from app.extansions import db
from app.models import Donations
from app.utils import insert_donate, get_sum

admin_ext = Admin(template_mode='bootstrap3')
migrate_ext = Migrate()
load_dotenv()


def get_engine():
    return create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

def get_db():
    if 'db' not in g:
        g.db = db._make_scoped_session(options={'bind': get_engine()})
    return g.db

def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.remove()


def create_app(testing=False):
    new_app = Flask(__name__)
    if testing:
        new_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        new_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatabase.db"
    new_app.config["SECRET_KEY"] = os.getenv('SECRET_KEY', 'TypeMeIn')
    db.init_app(new_app)
    new_app.teardown_appcontext(close_db)
    migrate_ext.init_app(new_app, db)
    admin_ext.init_app(new_app)

    @new_app.route("/donate", methods=["POST"])
    def payment_page():
        data = request.json
        if not data:
            return abort(400)
        try:
            db = get_db()
            insert_donate(data, db)
        except Exception as e:
            return abort(500)
        return jsonify({"message": "Success"})

    @new_app.route("/balance")
    def get_balance():
        db = get_db()
        total = get_sum(db)
        return jsonify({"Total": total})

    return new_app


app = create_app()


class MyModelView(ModelView):
    column_display_all_relations = True
    column_hide_backrefs = False


admin_ext.add_view(MyModelView(Donations, db.session))


