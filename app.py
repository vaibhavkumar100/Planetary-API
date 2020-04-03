from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os
from json import *

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(base_dir, 'planets.db')
app.config["SECRET_KEY"] = "9b71bdfb424c1693851bf269f3357f79"

app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '59ee03740d40fa'
app.config['MAIL_PASSWORD'] = 'e9acefd01f068e'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False



db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


# database functions
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('DB Created!')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('DB Dropped!')

@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                    planet_type='Class D',
                    home_star='Sun',
                    mass=3.258e23,
                    radius=1516,
                    distance=35.98e6)
    
    venus = Planet(planet_name='venus',
                    planet_type='Class K',
                    home_star='Sun',
                    mass=4.8678e24,
                    radius=3760,
                    distance=67.24e6)
    
    earth = Planet(planet_name='earth',
                    planet_type='Class M',
                    home_star='Sun',
                    mass=5.972e24,
                    radius=3959,
                    distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='Vaibhav',
    last_name='Kumar',
    email='vaibhav@vaibhav.com',
    password='vaibhav')

    db.session.add(test_user)
    db.session.commit()
    print('DB Seeded!')



@app.route("/")
@app.route("/home")
def hello_world():
    response = {
        'message': 'Hello World!'
    }
    return dumps(response)

@app.route("/about")
def about_page():
    return 'About Page'

@app.route("/super-simple")
def super_simple():
    return jsonify(message="Hello from the Planetary API.")

@app.route("/not_found")
def not_found():
    return jsonify(message="Resource not found"), 404

@app.route('/query_params')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message=f"Sorry {name}, you are not old enough."), 401 # => unauthorized
    else:
        return jsonify(message=f"Welcome {name}, you are old enough!")

@app.route('/url_params/<string:name>/<int:age>')
def url_parameters(name: str, age: int):
    if age < 18:
        return jsonify(message=f"Sorry {name}, you are not old enough."), 401 # => unauthorized
    else:
        return jsonify(message=f"Welcome {name}, you are old enough!")

@app.route('/planets', methods=['GET'])
def planets():
    planet_list = Planet.query.all()
    result = planets_schema.dump(planet_list)
    return jsonify(result=result)

@app.route('/register', methods=['POST'])
def register():
    email=request.form['email']
    test = User.query.filter_by(email=email).first()

    if test:
        return jsonify(message='Email already exists'), 409
    else:
        f_name = request.form['first_name']
        l_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=f_name, last_name=l_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return jsonify(message='User created successfully'), 201

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login successful", access_token=access_token)
    else:
        return jsonify(message="Incorrect email or password"), 401

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your planetary API password is " + user.password, sender="admin@planetary-api.com", recipients=[email])
        mail.send(msg)
        return jsonify(message='Password sent to ' + email)
    else:
        return jsonify(message="That email doesn't exist"), 401

@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message="That planet doesn't exist"), 404

@app.route('/add_planet', methods=['POST'])
@jwt_required
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message='There already a planet by that name'), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = request.form['mass']
        radius = request.form['radius']
        distance = request.form['distance']

        new_planet = Planet(planet_name = planet_name,
            planet_type=planet_type,
            home_star=home_star,
            mass=mass,
            radius=radius,
            distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="You added a planet"), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="Planet details updated"), 202
    else:
        return jsonify(message="Planet Not Found"), 404

@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required
def remove_planet(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message='Planet deleted'), 202
    else:
        return jsonify(message='No planet by that id!'), 404

# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)

#serializing
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')

class PlanetSchema(ma.Schema):
    class Meta:
        fields = ("planet_id",
        "planet_name",
        "planet_type",
        "home_star",
        "mass",
        "radius",
        "distance")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)



if __name__ == "__main__":
    app.run(debug=True)