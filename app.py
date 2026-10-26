import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_segura'
database_url = os.environ.get('DATABASE_URL', 'sqlite:///usuarios.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 300}
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

# Modelo para los comentarios del Foro
class ComentarioForo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey('publicacion_foro.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    autor_nombre = db.Column(db.String(100), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.String(50), nullable=False)

    
# --- MODELO DE MI UNIVERSO (Privado por usuario) ---
class UniversoPersonal(db.Model):
    __tablename__ = 'universo_personal'

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id'),
        unique=True,
        nullable=False
    )

    # Aquí se guardarán las estrellas, metas y reflexiones.
    contenido = db.Column(db.JSON, nullable=False, default=dict)

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

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
        comentarios = ComentarioForo.query.filter_by(publicacion_id=p.id).order_by(ComentarioForo.id.asc()).all()
        resultado.append({
            "id": p.id,
            "autor": p.autor_nombre,
            "texto": p.texto,
            "fecha": p.fecha,
            "insignias": {
                "diario": p.ins_diario,
                "respiracion": p.ins_respiracion,
                "foro": p.ins_foro,
                "reto": p.ins_reto
            },
            "comentarios": [
                {"autor": c.autor_nombre, "texto": c.texto, "fecha": c.fecha}
                for c in comentarios
            ]
        })
    return jsonify(resultado)

# --- RUTA PARA COMENTAR EN EL FORO ---
@app.route('/api/foro/comentar', methods=['POST'])
def comentar_foro():
    if 'usuario_id' not in session:
        return "No autorizado", 401

    data = request.get_json()
    publicacion_id = data.get('publicacion_id')
    texto = data.get('texto')
    fecha = data.get('fecha') or datetime.now().strftime('%d/%m/%Y')

    if not texto or not texto.strip():
        return "Texto vacío", 400

    publicacion = PublicacionForo.query.get(publicacion_id)
    if not publicacion:
        return "Publicación no encontrada", 404

    usuario = Usuario.query.get(session['usuario_id'])

    nuevo_comentario = ComentarioForo(
        publicacion_id=publicacion.id,
        autor_id=usuario.id,
        autor_nombre=usuario.nombre,
        texto=texto.strip(),
        fecha=fecha
    )
    db.session.add(nuevo_comentario)
    db.session.commit()
    return "", 200

# --- RUTA PARA BORRAR UNA PUBLICACIÓN PROPIA ---
@app.route('/api/foro/<int:pub_id>', methods=['DELETE'])
def borrar_publicacion(pub_id):
    if 'usuario_id' not in session:
        return "No autorizado", 401

    publicacion = PublicacionForo.query.get(pub_id)
    if not publicacion:
        return "Publicación no encontrada", 404

    if publicacion.autor_id != session['usuario_id']:
        return "No puedes borrar mensajes de otros usuarios", 403

    ComentarioForo.query.filter_by(publicacion_id=publicacion.id).delete()
    db.session.delete(publicacion)
    db.session.commit()
    return "", 200


# --- API DE MI UNIVERSO ---

@app.route('/api/universo', methods=['GET'])
def obtener_universo():
    if 'usuario_id' not in session:
        return jsonify({"error": "Debes iniciar sesión"}), 401

    universo = UniversoPersonal.query.filter_by(
        usuario_id=session['usuario_id']
    ).first()

    if not universo:
        return jsonify({"contenido": {}}), 200

    return jsonify({
        "contenido": universo.contenido,
        "actualizado_en": (
            universo.actualizado_en.isoformat()
            if universo.actualizado_en else None
        )
    }), 200


@app.route('/api/universo', methods=['PUT'])
def guardar_universo():
    if 'usuario_id' not in session:
        return jsonify({"error": "Debes iniciar sesión"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Datos JSON inválidos"}), 400

    contenido = data.get('contenido')

    if not isinstance(contenido, dict):
        return jsonify({
            "error": "El contenido debe ser un objeto JSON"
        }), 400

    # Límite inicial para evitar guardar cargas excesivas.
    if len(request.get_data()) > 100_000:
        return jsonify({"error": "El contenido es demasiado grande"}), 413

    universo = UniversoPersonal.query.filter_by(
        usuario_id=session['usuario_id']
    ).first()

    if universo is None:
        universo = UniversoPersonal(
            usuario_id=session['usuario_id'],
            contenido=contenido
        )
        db.session.add(universo)
    else:
        universo.contenido = contenido

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Error guardando Mi Universo")
        return jsonify({"error": "No se pudo guardar el universo"}), 500

    return jsonify({
        "mensaje": "Universo guardado correctamente",
        "contenido": universo.contenido
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)