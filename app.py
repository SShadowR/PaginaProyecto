from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    ins_diario = db.Column(db.Boolean, default=False)
    ins_respiracion = db.Column(db.Boolean, default=False)
    ins_foro = db.Column(db.Boolean, default=False)
    ins_reto = db.Column(db.Boolean, default=False)

# Modelo para el Diario (Privado por usuario)
class EntradaDiario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.String(50), nullable=False)
    texto = db.Column(db.Text, nullable=False)

# Modelo para el Foro (Público / Comunitario)
class PublicacionForo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    autor_nombre = db.Column(db.String(100), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.String(50), nullable=False)
    ins_diario = db.Column(db.Boolean, default=False)
    ins_respiracion = db.Column(db.Boolean, default=False)
    ins_foro = db.Column(db.Boolean, default=False)
    ins_reto = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['POST'])
def registro():
    nombre = request.form['usuario']
    password = request.form['password']
    
    if Usuario.query.filter_by(nombre=nombre).first():
        return "El usuario ya existe", 400
        
    hashed_password = generate_password_hash(password)
    nuevo_usuario = Usuario(nombre=nombre, password=hashed_password)
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    session['usuario_id'] = nuevo_usuario.id
    session['usuario_nombre'] = nuevo_usuario.nombre
    return "", 200

@app.route('/login', methods=['POST'])
def login():
    nombre = request.form['usuario']
    password = request.form['password']
    
    usuario = Usuario.query.filter_by(nombre=nombre).first()
    if usuario and check_password_hash(usuario.password, password):
        session['usuario_id'] = usuario.id
        session['usuario_nombre'] = usuario.nombre
        return "", 200
    
    return "Credenciales incorrectas", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/check-session')
def check_session():
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        return jsonify({
            "autenticado": True,
            "nombre": usuario.nombre,
            "insignias": {
                "diario": usuario.ins_diario,
                "respiracion": usuario.ins_respiracion,
                "foro": usuario.ins_foro,
                "reto": usuario.ins_reto
            }
        })
    return jsonify({"autenticado": False})

@app.route('/desbloquear-insignia', methods=['POST'])
def desbloquear_insignia():
    if 'usuario_id' not in session:
        return "No autorizado", 401
    
    data = request.get_json()
    tipo = data.get('tipo')
    usuario = Usuario.query.get(session['usuario_id'])
    
    if tipo == 'diario': usuario.ins_diario = True
    elif tipo == 'respiracion': usuario.ins_respiracion = True
    elif tipo == 'foro': usuario.ins_foro = True
    elif tipo == 'reto': usuario.ins_reto = True
    
    db.session.commit()
    return "", 200

# --- RUTAS DE DIARIO (Privadas) ---
@app.route('/api/diario', methods=['GET', 'POST'])
def gestionar_diario():
    if 'usuario_id' not in session:
        return jsonify([]), 401
    
    usuario_id = session['usuario_id']
    
    if request.method == 'POST':
        data = request.get_json()
        texto = data.get('texto')
        fecha = data.get('fecha')
        
        if texto:
            nueva_entrada = EntradaDiario(usuario_id=usuario_id, texto=texto, fecha=fecha)
            db.session.add(nueva_entrada)
            
            usuario = Usuario.query.get(usuario_id)
            usuario.ins_diario = True
            
            db.session.commit()
            return "", 200
        return "Texto vacío", 400

    entradas = EntradaDiario.query.filter_by(usuario_id=usuario_id).order_by(EntradaDiario.id.desc()).all()
    return jsonify([{"fecha": e.fecha, "texto": e.texto} for e in entradas])

# --- RUTAS DE FORO (Comunitarias) ---
@app.route('/api/foro', methods=['GET', 'POST'])
def gestionar_foro():
    if request.method == 'POST':
        if 'usuario_id' not in session:
            return "No autorizado", 401
            
        data = request.get_json()
        texto = data.get('texto')
        usuario = Usuario.query.get(session['usuario_id'])
        
        if texto:
            fecha_actual = datetime.now().strftime('%d/%m/%Y')
            
            nueva_pub = PublicacionForo(
                autor_id=usuario.id,
                autor_nombre=usuario.nombre,
                texto=texto,
                fecha=fecha_actual,
                ins_diario=usuario.ins_diario,
                ins_respiracion=usuario.ins_respiracion,
                ins_foro=True,
                ins_reto=usuario.ins_reto
            )
            db.session.add(nueva_pub)
            usuario.ins_foro = True
            db.session.commit()
            return "", 200
        return "Texto vacío", 400

    pubs = PublicacionForo.query.order_by(PublicacionForo.id.desc()).all()
    resultado = []
    for p in pubs:
        resultado.append({
            "autor": p.autor_nombre,
            "texto": p.texto,
            "fecha": p.fecha,
            "insignias": {
                "diario": p.ins_diario,
                "respiracion": p.ins_respiracion,
                "foro": p.ins_foro,
                "reto": p.ins_reto
            }
        })
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True)