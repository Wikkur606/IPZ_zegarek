import pprint
from flask import Flask, redirect, render_template, request, jsonify, abort, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields
from datetime import datetime, timedelta
import os
from os.path import isfile, join
from os import listdir
import json
from io import StringIO
from werkzeug.wrappers import Response
import itertools
import random
import string

app = Flask(__name__)
app.secret_key = 'development key'

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{username}:{password}@{hostname}/{databasename}".format(
    username="Mechaniczny",
    password="alamakota",
    hostname="Mechaniczny.mysql.pythonanywhere-services.com",
    databasename="Mechaniczny$sza3",
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)



class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096))
    devices = db.relationship('Devices', backref='user', lazy=True)

    def __init__(self, username):
        self.name = username


class Devices(db.Model):
    __tablename__ = "devices"
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(255))
    status = db.Column(db.String(255))
    presence = db.Column(db.Boolean)
    batt_now = db.Column(db.Float)
    positionX = db.Column(db.Integer)
    positionY = db.Column(db.Integer)
    histereza = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mes1_data = db.relationship('Mes1', backref='device', lazy=True)


class Mes1(db.Model):
    __tablename__ = "mes1"
    id = db.Column(db.Integer, primary_key=True)
    foto1 = db.Column(db.Float)
    foto2 = db.Column(db.Float)
    foto3 = db.Column(db.Float)
    foto4 = db.Column(db.Float)
    serwo1 = db.Column(db.Integer)
    serwo2 = db.Column(db.Integer)
    bett_his = db.Column(db.Float)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)



class UsersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Users


class DevicesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Devices
        include_fk = True


class Mes1Schema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mes1
        include_fk = True


user_schema = UsersSchema()
users_schema = UsersSchema(many=True)
device_schema = DevicesSchema()
devices_schema = DevicesSchema(many=True)
mes1_schema = Mes1Schema()
mes1_schemas = Mes1Schema(many=True)



@app.route("/")
def home():
    return "Witaj! Moje API działa poprawnie."


@app.route("/user", methods=["POST"])
def add_user():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({"message": "Brak pola 'name'"}), 400
    new_user = Users(username=data['name'])
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user), 201


@app.route("/users", methods=["GET"])
def get_users():
    wszyscy = Users.query.all()
    return jsonify(users_schema.dump(wszyscy))



@app.route("/device", methods=["POST"])
def add_device():
    """Dodaj nowe urządzenie do użytkownika."""
    data = request.json
    if not data or 'user_id' not in data:
        return jsonify({"message": "Brak pola 'user_id'"}), 400

    user = Users.query.get(data['user_id'])
    if not user:
        return jsonify({"message": "Użytkownik nie istnieje"}), 404

    new_device = Devices(
        model=data.get('model', 'ESP'),
        status=data.get('status', 'active'),
        presence=data.get('presence', False),
        batt_now=data.get('batt_now', 0.0),
        positionX=data.get('positionX', 0),
        positionY=data.get('positionY', 0),
        histereza=data.get('histereza', 0.0),
        user_id=data['user_id']
    )
    db.session.add(new_device)
    db.session.commit()
    return device_schema.jsonify(new_device), 201


@app.route("/devices", methods=["GET"])
def get_devices():
    """Lista wszystkich urządzeń."""
    devices = Devices.query.all()
    return jsonify(devices_schema.dump(devices))


@app.route("/device/<int:id>", methods=["GET"])
def get_device(id):
    """Dane konkretnego urządzenia."""
    device = Devices.query.get_or_404(id)
    return device_schema.jsonify(device)


@app.route("/device/<int:id>", methods=["PATCH"])
def update_device(id):
    """Aktualizuj dane urządzenia (np. status, pozycja)."""
    device = Devices.query.get_or_404(id)
    data = request.json
    if 'status' in data:
        device.status = data['status']
    if 'presence' in data:
        device.presence = data['presence']
    if 'batt_now' in data:
        device.batt_now = data['batt_now']
    if 'positionX' in data:
        device.positionX = data['positionX']
    if 'positionY' in data:
        device.positionY = data['positionY']
    if 'histereza' in data:
        device.histereza = data['histereza']
    db.session.commit()
    return device_schema.jsonify(device)



@app.route("/device/<int:id>/mes1", methods=["POST"])
def add_mes1(id):
    """
    ESP wysyła pomiary dla urządzenia o podanym id.

    Przykładowy JSON z ESP:
    {
        "foto1": 1.23,
        "foto2": 2.34,
        "foto3": 3.45,
        "foto4": 4.56,
        "serwo1": 90,
        "serwo2": 45,
        "bett_his": 3.7
    }
    """
    device = Devices.query.get_or_404(id)
    data = request.json
    if not data:
        return jsonify({"message": "Brak danych"}), 400

    # Aktualizuj też batt_now i presence w tabeli devices
    if 'bett_his' in data:
        device.batt_now = data['bett_his']
    if 'presence' in data:
        device.presence = data['presence']

    new_mes = Mes1(
        foto1=data.get('foto1'),
        foto2=data.get('foto2'),
        foto3=data.get('foto3'),
        foto4=data.get('foto4'),
        serwo1=data.get('serwo1'),
        serwo2=data.get('serwo2'),
        bett_his=data.get('bett_his'),
        device_id=id
    )
    db.session.add(new_mes)
    db.session.commit()
    return mes1_schema.jsonify(new_mes), 201


@app.route("/device/<int:id>/mes1", methods=["GET"])
def get_mes1(id):
    """Pobierz ostatnie 100 pomiarów dla urządzenia."""
    Devices.query.get_or_404(id)
    pomiary = Mes1.query.filter_by(device_id=id).order_by(desc(Mes1.id)).limit(100).all()
    return jsonify(mes1_schemas.dump(pomiary))


@app.route("/device/<int:id>/mes1/last", methods=["GET"])
def get_mes1_last(id):
    """Pobierz ostatni pomiar dla urządzenia."""
    Devices.query.get_or_404(id)
    ostatni = Mes1.query.filter_by(device_id=id).order_by(desc(Mes1.id)).first()
    if not ostatni:
        return jsonify({"message": "Brak pomiarów"}), 404
    return mes1_schema.jsonify(ostatni)
