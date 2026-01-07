import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Configuración de base de datos - usa variable de entorno si está disponible (para producción)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///tareas.db')
# Ajustar para PostgreSQL si es necesario (Railway, Render usan PostgreSQL)
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelos de base de datos


class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_df = db.Column(db.String(50))
    actividad_predecesora = db.Column(db.String(50))
    asunto_tema = db.Column(db.String(500))
    tarea = db.Column(db.Text, nullable=False)
    encargado_actual = db.Column(db.String(200), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(50), default='Pendiente')
    dias = db.Column(db.Integer)
    valor = db.Column(db.String(100))
    evidencia = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con delegaciones
    delegaciones = db.relationship(
        'Delegacion', backref='tarea', lazy=True, cascade='all, delete-orphan')


class Delegacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tarea_id = db.Column(db.Integer, db.ForeignKey('tarea.id'), nullable=False)
    delegado_de = db.Column(
        db.String(200), nullable=False)  # Persona que delega
    # Persona que recibe
    delegado_a = db.Column(db.String(200), nullable=False)
    fecha_delegacion = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.Text)
    observaciones_delegacion = db.Column(db.Text)


# Crear tablas
with app.app_context():
    db.create_all()

# Rutas


@app.route('/')
def index():
    return render_template('index.html')

# API - Obtener todas las tareas


@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    tareas = Tarea.query.all()
    return jsonify([{
        'id': t.id,
        'numero_df': t.numero_df,
        'actividad_predecesora': t.actividad_predecesora,
        'asunto_tema': t.asunto_tema,
        'tarea': t.tarea,
        'encargado_actual': t.encargado_actual,
        'fecha_inicio': t.fecha_inicio.strftime('%Y-%m-%d') if t.fecha_inicio else None,
        'fecha_fin': t.fecha_fin.strftime('%Y-%m-%d') if t.fecha_fin else None,
        'estado': t.estado,
        'dias': t.dias,
        'valor': t.valor,
        'evidencia': t.evidencia,
        'observaciones': t.observaciones,
        'fecha_creacion': t.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if t.fecha_creacion else None,
        'delegaciones': [{
            'id': d.id,
            'delegado_de': d.delegado_de,
            'delegado_a': d.delegado_a,
            'fecha_delegacion': d.fecha_delegacion.strftime('%Y-%m-%d %H:%M:%S'),
            'motivo': d.motivo,
            'observaciones_delegacion': d.observaciones_delegacion
        } for d in t.delegaciones]
    } for t in tareas])

# API - Crear nueva tarea


@app.route('/api/tareas', methods=['POST'])
def crear_tarea():
    data = request.json

    # Calcular días si hay fechas
    dias = None
    if data.get('fecha_inicio') and data.get('fecha_fin'):
        fecha_inicio = datetime.strptime(
            data['fecha_inicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
        dias = (fecha_fin - fecha_inicio).days
    elif data.get('fecha_inicio'):
        fecha_inicio = datetime.strptime(
            data['fecha_inicio'], '%Y-%m-%d').date()
    else:
        fecha_inicio = datetime.now().date()

    fecha_fin = None
    if data.get('fecha_fin'):
        fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()

    tarea = Tarea(
        numero_df=data.get('numero_df'),
        actividad_predecesora=data.get('actividad_predecesora'),
        asunto_tema=data.get('asunto_tema'),
        tarea=data.get('tarea', ''),
        encargado_actual=data.get('encargado_actual', ''),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=data.get('estado', 'Pendiente'),
        dias=dias,
        valor=data.get('valor'),
        evidencia=data.get('evidencia'),
        observaciones=data.get('observaciones')
    )

    db.session.add(tarea)
    db.session.commit()

    return jsonify({'id': tarea.id, 'mensaje': 'Tarea creada exitosamente'}), 201

# API - Actualizar tarea


@app.route('/api/tareas/<int:tarea_id>', methods=['PUT'])
def actualizar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    data = request.json

    if 'numero_df' in data:
        tarea.numero_df = data['numero_df']
    if 'actividad_predecesora' in data:
        tarea.actividad_predecesora = data['actividad_predecesora']
    if 'asunto_tema' in data:
        tarea.asunto_tema = data['asunto_tema']
    if 'tarea' in data:
        tarea.tarea = data['tarea']
    if 'encargado_actual' in data:
        tarea.encargado_actual = data['encargado_actual']
    if 'fecha_inicio' in data:
        tarea.fecha_inicio = datetime.strptime(
            data['fecha_inicio'], '%Y-%m-%d').date()
    if 'fecha_fin' in data:
        tarea.fecha_fin = datetime.strptime(
            data['fecha_fin'], '%Y-%m-%d').date() if data['fecha_fin'] else None
    if 'estado' in data:
        tarea.estado = data['estado']
    if 'valor' in data:
        tarea.valor = data['valor']
    if 'evidencia' in data:
        tarea.evidencia = data['evidencia']
    if 'observaciones' in data:
        tarea.observaciones = data['observaciones']

    # Recalcular días
    if tarea.fecha_inicio and tarea.fecha_fin:
        tarea.dias = (tarea.fecha_fin - tarea.fecha_inicio).days
    elif tarea.fecha_inicio:
        tarea.dias = (datetime.now().date() - tarea.fecha_inicio).days

    db.session.commit()
    return jsonify({'mensaje': 'Tarea actualizada exitosamente'})

# API - Eliminar tarea


@app.route('/api/tareas/<int:tarea_id>', methods=['DELETE'])
def eliminar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    db.session.delete(tarea)
    db.session.commit()
    return jsonify({'mensaje': 'Tarea eliminada exitosamente'})

# API - Delegar tarea (1 a 1)


@app.route('/api/tareas/<int:tarea_id>/delegar', methods=['POST'])
def delegar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    data = request.json

    # Validar que solo hay una delegación activa (1 a 1)
    # Una tarea solo puede tener una delegación a la vez
    delegacion_activa = Delegacion.query.filter_by(
        tarea_id=tarea_id).order_by(Delegacion.fecha_delegacion.desc()).first()

    if delegacion_activa:
        # Si ya existe una delegación, actualizamos el encargado actual
        # pero mantenemos el historial
        tarea.encargado_actual = data['delegado_a']
    else:
        # Primera delegación
        tarea.encargado_actual = data['delegado_a']

    # Crear registro de delegación
    delegacion = Delegacion(
        tarea_id=tarea_id,
        delegado_de=data['delegado_de'],
        delegado_a=data['delegado_a'],
        motivo=data.get('motivo', ''),
        observaciones_delegacion=data.get('observaciones_delegacion', '')
    )

    db.session.add(delegacion)
    db.session.commit()

    return jsonify({
        'mensaje': 'Tarea delegada exitosamente',
        'delegacion': {
            'id': delegacion.id,
            'delegado_de': delegacion.delegado_de,
            'delegado_a': delegacion.delegado_a,
            'fecha_delegacion': delegacion.fecha_delegacion.strftime('%Y-%m-%d %H:%M:%S'),
            'motivo': delegacion.motivo
        }
    }), 201

# API - Obtener historial de delegaciones de una tarea


@app.route('/api/tareas/<int:tarea_id>/delegaciones', methods=['GET'])
def get_delegaciones(tarea_id):
    delegaciones = Delegacion.query.filter_by(tarea_id=tarea_id).order_by(
        Delegacion.fecha_delegacion.desc()).all()
    return jsonify([{
        'id': d.id,
        'delegado_de': d.delegado_de,
        'delegado_a': d.delegado_a,
        'fecha_delegacion': d.fecha_delegacion.strftime('%Y-%m-%d %H:%M:%S'),
        'motivo': d.motivo,
        'observaciones_delegacion': d.observaciones_delegacion
    } for d in delegaciones])


if __name__ == '__main__':
    # En producción, usar el puerto de la variable de entorno
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
