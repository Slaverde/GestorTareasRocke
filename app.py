import os
import re
import json
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime
import pandas as pd
from io import BytesIO

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL', 'sqlite:///tareas.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'gestor-tareas-rocket-2024')

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_df = db.Column(db.String(50))
    # actividad_predecesora kept only for DB compatibility with existing rows
    actividad_predecesora = db.Column(db.String(50))
    asunto_tema = db.Column(db.String(500))
    tarea = db.Column(db.Text, nullable=False)
    encargado_actual = db.Column(db.String(200), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(50), default='Pendiente')
    dias = db.Column(db.Integer)
    evidencia = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    historial_notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Campos Fase 1
    prioridad = db.Column(db.String(50), default='Normal')
    tipo = db.Column(db.String(50), default='Tarea')
    parent_id = db.Column(db.Integer, db.ForeignKey('tarea.id'), nullable=True)
    depends_on_id = db.Column(
        db.Integer, db.ForeignKey('tarea.id'), nullable=True)
    orden_kanban = db.Column(db.Integer, default=0)

    delegaciones = db.relationship(
        'Delegacion', backref='tarea', lazy=True, cascade='all, delete-orphan')

    subtareas = db.relationship(
        'Tarea',
        foreign_keys=[parent_id],
        backref=db.backref('padre', remote_side=[id]),
        lazy='dynamic'
    )


class Encargado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class Delegacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tarea_id = db.Column(db.Integer, db.ForeignKey('tarea.id'), nullable=False)
    delegado_de = db.Column(db.String(200), nullable=False)
    delegado_a = db.Column(db.String(200), nullable=False)
    fecha_delegacion = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.Text)
    observaciones_delegacion = db.Column(db.Text)


# ---------------------------------------------------------------------------
# Migración segura: agrega columnas nuevas a tablas existentes
# ---------------------------------------------------------------------------

def migrar_base_datos():
    from sqlalchemy import text
    from sqlalchemy import inspect as sa_inspect

    with app.app_context():
        try:
            inspector = sa_inspect(db.engine)
            if 'tarea' not in inspector.get_table_names():
                return

            columnas_existentes = [c['name']
                                   for c in inspector.get_columns('tarea')]
            nuevas_columnas = [
                ('prioridad',        "VARCHAR(50) DEFAULT 'Normal'"),
                ('tipo',             "VARCHAR(50) DEFAULT 'Tarea'"),
                ('parent_id',        'INTEGER'),
                ('depends_on_id',    'INTEGER'),
                ('orden_kanban',     'INTEGER DEFAULT 0'),
                ('historial_notas',  'TEXT'),
            ]

            with db.engine.connect() as conn:
                for nombre, definicion in nuevas_columnas:
                    if nombre not in columnas_existentes:
                        conn.execute(text(
                            f'ALTER TABLE tarea ADD COLUMN {nombre} {definicion}'
                        ))
                conn.commit()
        except Exception as e:
            print(f'[Migración] {e}')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generar_numero_tarea():
    """Genera el siguiente ID de tarea en formato T01, T02, T03..."""
    existentes = db.session.query(Tarea.numero_df).filter(
        Tarea.numero_df.like('T%')
    ).all()
    max_num = 0
    for (num,) in existentes:
        if num:
            m = re.match(r'T(\d+)', num, re.IGNORECASE)
            if m:
                n = int(m.group(1))
                if n > max_num:
                    max_num = n
    return f'T{(max_num + 1):02d}'


def tarea_a_dict(t):
    depends_numero = None
    if t.depends_on_id:
        dep = Tarea.query.get(t.depends_on_id)
        if dep:
            depends_numero = dep.numero_df or f'#{dep.id}'

    return {
        'id': t.id,
        'numero_df': t.numero_df,
        'asunto_tema': t.asunto_tema,
        'tarea': t.tarea,
        'encargado_actual': t.encargado_actual,
        'fecha_inicio': t.fecha_inicio.strftime('%Y-%m-%d') if t.fecha_inicio else None,
        'fecha_fin': t.fecha_fin.strftime('%Y-%m-%d') if t.fecha_fin else None,
        'estado': t.estado,
        'dias': t.dias,
        'evidencia': t.evidencia,
        'observaciones': t.observaciones,
        'fecha_creacion': t.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if t.fecha_creacion else None,
        'prioridad': t.prioridad or 'Normal',
        'tipo': t.tipo or 'Tarea',
        'parent_id': t.parent_id,
        'depends_on_id': t.depends_on_id,
        'depends_on_numero': depends_numero,
        'orden_kanban': t.orden_kanban or 0,
        'historial_notas': json.loads(t.historial_notas) if t.historial_notas else [],
        'subtareas_count': t.subtareas.count(),
        'delegaciones': [{
            'id': d.id,
            'delegado_de': d.delegado_de,
            'delegado_a': d.delegado_a,
            'fecha_delegacion': d.fecha_delegacion.strftime('%Y-%m-%d %H:%M:%S'),
            'motivo': d.motivo,
            'observaciones_delegacion': d.observaciones_delegacion
        } for d in t.delegaciones]
    }


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()
    migrar_base_datos()


# ---------------------------------------------------------------------------
# Rutas de páginas
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/informes')
def informes():
    return render_template('informes.html')


# ---------------------------------------------------------------------------
# API – Encargados
# ---------------------------------------------------------------------------

@app.route('/api/encargados', methods=['GET'])
def get_encargados():
    encargados = Encargado.query.filter_by(
        activo=True).order_by(Encargado.nombre).all()
    return jsonify([{
        'id': e.id, 'nombre': e.nombre, 'email': e.email
    } for e in encargados])


@app.route('/api/encargados', methods=['POST'])
def crear_encargado():
    data = request.json
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({'error': 'El nombre es obligatorio'}), 400

    existe = Encargado.query.filter_by(nombre=nombre).first()
    if existe:
        if not existe.activo:
            existe.activo = True
            existe.email = data.get('email', '')
            db.session.commit()
            return jsonify({'id': existe.id, 'mensaje': 'Encargado reactivado'}), 200
        return jsonify({'error': 'Ya existe un encargado con ese nombre'}), 400

    encargado = Encargado(nombre=nombre, email=data.get('email', ''))
    db.session.add(encargado)
    db.session.commit()
    return jsonify({'id': encargado.id, 'mensaje': 'Encargado creado exitosamente'}), 201


@app.route('/api/encargados/<int:encargado_id>', methods=['PUT'])
def actualizar_encargado(encargado_id):
    encargado = Encargado.query.get_or_404(encargado_id)
    data = request.json
    if 'nombre' in data:
        nuevo_nombre = data['nombre'].strip()
        if nuevo_nombre != encargado.nombre:
            existe = Encargado.query.filter_by(nombre=nuevo_nombre).first()
            if existe and existe.id != encargado_id:
                return jsonify({'error': 'Ya existe un encargado con ese nombre'}), 400
            encargado.nombre = nuevo_nombre
    if 'email' in data:
        encargado.email = data['email']
    db.session.commit()
    return jsonify({'mensaje': 'Encargado actualizado exitosamente'})


@app.route('/api/encargados/<int:encargado_id>', methods=['DELETE'])
def eliminar_encargado(encargado_id):
    encargado = Encargado.query.get_or_404(encargado_id)
    encargado.activo = False
    db.session.commit()
    return jsonify({'mensaje': 'Encargado eliminado exitosamente'})


# ---------------------------------------------------------------------------
# API – Tareas
# ---------------------------------------------------------------------------

@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    tareas = Tarea.query.order_by(
        Tarea.orden_kanban, Tarea.fecha_creacion).all()
    return jsonify([tarea_a_dict(t) for t in tareas])


@app.route('/api/tareas', methods=['POST'])
def crear_tarea():
    data = request.json

    fecha_inicio = (
        datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        if data.get('fecha_inicio') else datetime.now().date()
    )
    fecha_fin = (
        datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
        if data.get('fecha_fin') else None
    )
    dias = (fecha_fin - fecha_inicio).days if fecha_fin else None

    obs_inicial = data.get('observaciones') or ''
    historial_inicial = []
    if obs_inicial.strip():
        historial_inicial.append({
            'texto': obs_inicial.strip(),
            'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })

    tarea = Tarea(
        numero_df=generar_numero_tarea(),
        asunto_tema=data.get('asunto_tema'),
        tarea=data.get('tarea', ''),
        encargado_actual=data.get('encargado_actual', ''),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=data.get('estado', 'Pendiente'),
        dias=dias,
        evidencia=data.get('evidencia'),
        observaciones=obs_inicial,
        historial_notas=json.dumps(
            historial_inicial, ensure_ascii=False) if historial_inicial else None,
        prioridad=data.get('prioridad', 'Normal'),
        tipo=data.get('tipo', 'Tarea'),
        parent_id=data.get('parent_id') or None,
        depends_on_id=data.get('depends_on_id') or None,
        orden_kanban=data.get('orden_kanban', 0),
    )

    db.session.add(tarea)
    db.session.commit()

    tarea_dict = tarea_a_dict(tarea)
    socketio.emit('tarea_actualizada', tarea_dict)
    return jsonify({
        'id': tarea.id,
        'numero_df': tarea.numero_df,
        'mensaje': 'Tarea creada exitosamente'
    }), 201


@app.route('/api/tareas/<int:tarea_id>', methods=['PUT'])
def actualizar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    data = request.json

    for campo in ['asunto_tema', 'tarea', 'encargado_actual', 'estado',
                  'evidencia', 'prioridad', 'tipo']:
        if campo in data:
            setattr(tarea, campo, data[campo])

    if 'observaciones' in data:
        nueva_obs = (data['observaciones'] or '').strip()
        obs_anterior = (tarea.observaciones or '').strip()
        if nueva_obs and nueva_obs != obs_anterior:
            historial = json.loads(
                tarea.historial_notas) if tarea.historial_notas else []
            historial.append({
                'texto': nueva_obs,
                'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            })
            tarea.historial_notas = json.dumps(historial, ensure_ascii=False)
        tarea.observaciones = data['observaciones']

    if 'fecha_inicio' in data:
        tarea.fecha_inicio = datetime.strptime(
            data['fecha_inicio'], '%Y-%m-%d').date()
    if 'fecha_fin' in data:
        tarea.fecha_fin = (
            datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
            if data['fecha_fin'] else None
        )
    if 'parent_id' in data:
        tarea.parent_id = data['parent_id'] or None
    if 'depends_on_id' in data:
        tarea.depends_on_id = data['depends_on_id'] or None
    if 'orden_kanban' in data:
        tarea.orden_kanban = data['orden_kanban']

    if tarea.fecha_inicio and tarea.fecha_fin:
        tarea.dias = (tarea.fecha_fin - tarea.fecha_inicio).days
    elif tarea.fecha_inicio:
        tarea.dias = (datetime.now().date() - tarea.fecha_inicio).days

    db.session.commit()

    tarea_dict = tarea_a_dict(tarea)
    socketio.emit('tarea_actualizada', tarea_dict)
    return jsonify({'mensaje': 'Tarea actualizada exitosamente'})


@app.route('/api/tareas/<int:tarea_id>', methods=['DELETE'])
def eliminar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    db.session.delete(tarea)
    db.session.commit()
    socketio.emit('tarea_eliminada', {'id': tarea_id})
    return jsonify({'mensaje': 'Tarea eliminada exitosamente'})


@app.route('/api/tareas/<int:tarea_id>/delegar', methods=['POST'])
def delegar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    data = request.json

    tarea.encargado_actual = data['delegado_a']
    delegacion = Delegacion(
        tarea_id=tarea_id,
        delegado_de=data['delegado_de'],
        delegado_a=data['delegado_a'],
        motivo=data.get('motivo', ''),
        observaciones_delegacion=data.get('observaciones_delegacion', '')
    )
    db.session.add(delegacion)
    db.session.commit()

    socketio.emit('tarea_actualizada', tarea_a_dict(tarea))
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


@app.route('/api/tareas/<int:tarea_id>/notas', methods=['POST'])
def agregar_nota(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    data = request.json
    texto = (data.get('texto') or '').strip()
    if not texto:
        return jsonify({'error': 'El texto de la nota no puede estar vacío'}), 400

    historial = json.loads(
        tarea.historial_notas) if tarea.historial_notas else []
    historial.append({
        'texto': texto,
        'fecha': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    })
    tarea.historial_notas = json.dumps(historial, ensure_ascii=False)
    tarea.observaciones = texto
    db.session.commit()

    socketio.emit('tarea_actualizada', tarea_a_dict(tarea))
    return jsonify({'mensaje': 'Nota agregada', 'historial_notas': historial}), 201


@app.route('/api/tareas/<int:tarea_id>/notas/<int:nota_idx>', methods=['DELETE'])
def eliminar_nota(tarea_id, nota_idx):
    tarea = Tarea.query.get_or_404(tarea_id)
    historial = json.loads(
        tarea.historial_notas) if tarea.historial_notas else []

    if nota_idx < 0 or nota_idx >= len(historial):
        return jsonify({'error': 'Índice de nota no válido'}), 400

    historial.pop(nota_idx)
    tarea.historial_notas = json.dumps(
        historial, ensure_ascii=False) if historial else None
    tarea.observaciones = historial[-1]['texto'] if historial else None
    db.session.commit()

    socketio.emit('tarea_actualizada', tarea_a_dict(tarea))
    return jsonify({'mensaje': 'Nota eliminada', 'historial_notas': historial})


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


@app.route('/api/tareas/<int:tarea_id>/subtareas', methods=['GET'])
def get_subtareas(tarea_id):
    subtareas = Tarea.query.filter_by(parent_id=tarea_id).order_by(
        Tarea.orden_kanban, Tarea.fecha_creacion).all()
    return jsonify([tarea_a_dict(t) for t in subtareas])


# ---------------------------------------------------------------------------
# API – Exportar / Importar Excel
# ---------------------------------------------------------------------------

@app.route('/api/tareas/exportar', methods=['GET'])
def exportar_tareas():
    tareas = Tarea.query.all()
    datos = []
    for t in tareas:
        datos.append({
            'Número de Tarea': t.numero_df or '',
            'ASUNTO, TEMA': t.asunto_tema or '',
            'TAREA': t.tarea or '',
            'ENCARGADO(A)': t.encargado_actual or '',
            'FECHA INICIO': t.fecha_inicio.strftime('%Y-%m-%d') if t.fecha_inicio else '',
            'FECHA FIN': t.fecha_fin.strftime('%Y-%m-%d') if t.fecha_fin else '',
            'ESTADO': t.estado or '',
            'PRIORIDAD': t.prioridad or 'Normal',
            'TIPO': t.tipo or 'Tarea',
            'DÍAS': t.dias if t.dias is not None else '',
            'EVIDENCIA, CONCLUSIÓN, RESULTADO, SOPORTE.': t.evidencia or '',
            'OBSERVACIONES': t.observaciones or ''
        })

    df = pd.DataFrame(datos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tareas')
    output.seek(0)

    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'Tareas_Comerciales_{fecha}.xlsx'
    )


@app.route('/api/tareas/importar', methods=['POST'])
def importar_tareas():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400

    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    try:
        df = pd.read_excel(archivo)
        columnas_mapeo = {
            'Número de Tarea': 'numero_df',
            '# D&F': 'numero_df',
            'ASUNTO, TEMA': 'asunto_tema',
            'TAREA': 'tarea',
            'ENCARGADO(A)': 'encargado_actual',
            'FECHA INICIO': 'fecha_inicio',
            'FECHA FIN': 'fecha_fin',
            'ESTADO': 'estado',
            'PRIORIDAD': 'prioridad',
            'TIPO': 'tipo',
            'DÍAS': 'dias',
            'EVIDENCIA, CONCLUSIÓN, RESULTADO, SOPORTE.': 'evidencia',
            'OBSERVACIONES': 'observaciones'
        }

        tareas_importadas = 0
        tareas_actualizadas = 0
        errores = []
        encargados_creados = set()

        for index, row in df.iterrows():
            try:
                numero_df = (
                    str(row.get('Número de Tarea', '')).strip()
                    if pd.notna(row.get('Número de Tarea', '')) else None
                )
                if not numero_df:
                    numero_df = (
                        str(row.get('# D&F', '')).strip()
                        if pd.notna(row.get('# D&F', '')) else None
                    )

                tarea_existente = (
                    Tarea.query.filter_by(numero_df=numero_df).first()
                    if numero_df else None
                )

                datos_tarea = {}
                for col_excel, campo_db in columnas_mapeo.items():
                    if col_excel in df.columns:
                        valor = row[col_excel]
                        if pd.notna(valor):
                            if campo_db in ['fecha_inicio', 'fecha_fin']:
                                try:
                                    datos_tarea[campo_db] = (
                                        datetime.strptime(
                                            str(valor), '%Y-%m-%d').date()
                                        if isinstance(valor, str)
                                        else (valor.date() if hasattr(valor, 'date') else None)
                                    )
                                except Exception:
                                    datos_tarea[campo_db] = None
                            elif campo_db == 'dias':
                                try:
                                    datos_tarea[campo_db] = int(valor)
                                except Exception:
                                    datos_tarea[campo_db] = None
                            else:
                                datos_tarea[campo_db] = str(valor).strip()

                if not datos_tarea.get('tarea') or not datos_tarea.get('encargado_actual'):
                    errores.append(
                        f'Fila {index + 2}: Faltan campos obligatorios (TAREA o ENCARGADO)')
                    continue

                nombre_encargado = datos_tarea.get(
                    'encargado_actual', '').strip()
                if nombre_encargado:
                    enc = Encargado.query.filter_by(
                        nombre=nombre_encargado).first()
                    if not enc:
                        db.session.add(
                            Encargado(nombre=nombre_encargado, email='', activo=True))
                        encargados_creados.add(nombre_encargado)

                if datos_tarea.get('fecha_inicio') and datos_tarea.get('fecha_fin'):
                    datos_tarea['dias'] = (
                        datos_tarea['fecha_fin'] - datos_tarea['fecha_inicio']).days
                if not datos_tarea.get('fecha_inicio'):
                    datos_tarea['fecha_inicio'] = datetime.now().date()
                if not datos_tarea.get('estado'):
                    datos_tarea['estado'] = 'Pendiente'
                if not datos_tarea.get('prioridad'):
                    datos_tarea['prioridad'] = 'Normal'
                if not datos_tarea.get('tipo'):
                    datos_tarea['tipo'] = 'Tarea'

                if tarea_existente:
                    for campo, valor in datos_tarea.items():
                        setattr(tarea_existente, campo, valor)
                    tareas_actualizadas += 1
                else:
                    if not datos_tarea.get('numero_df'):
                        datos_tarea['numero_df'] = generar_numero_tarea()
                    db.session.add(Tarea(**datos_tarea))
                    tareas_importadas += 1

            except Exception as e:
                errores.append(f'Fila {index + 2}: {str(e)}')
                continue

        db.session.commit()

        mensaje = f'Importación completada: {tareas_importadas} nuevas, {tareas_actualizadas} actualizadas'
        if encargados_creados:
            mensaje += f', {len(encargados_creados)} encargados creados automáticamente'
        if errores:
            mensaje += f'. {len(errores)} errores encontrados.'

        return jsonify({
            'mensaje': mensaje,
            'tareas_importadas': tareas_importadas,
            'tareas_actualizadas': tareas_actualizadas,
            'encargados_creados': len(encargados_creados),
            'errores': errores[:10]
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500


# ---------------------------------------------------------------------------
# API – Estadísticas
# ---------------------------------------------------------------------------

@app.route('/api/estadisticas', methods=['GET'])
def get_estadisticas():
    try:
        from datetime import date
        from collections import defaultdict

        todas = Tarea.query.all()
        hoy = date.today()

        total = len(todas)
        finalizadas = len([t for t in todas if t.estado == 'Finalizado'])
        en_proceso = len([t for t in todas if t.estado == 'En Proceso'])
        pendientes = len([t for t in todas if t.estado == 'Pendiente'])
        canceladas = len([t for t in todas if t.estado == 'Cancelado'])
        atrasadas = [
            t for t in todas
            if t.fecha_fin and t.fecha_fin < hoy and t.estado != 'Finalizado'
        ]

        stats = defaultdict(lambda: {
            'total': 0, 'finalizadas': 0, 'en_proceso': 0,
            'pendientes': 0, 'atrasadas': 0, 'canceladas': 0
        })
        for t in todas:
            e = t.encargado_actual
            stats[e]['total'] += 1
            if t.estado == 'Finalizado':
                stats[e]['finalizadas'] += 1
            elif t.estado == 'En Proceso':
                stats[e]['en_proceso'] += 1
            elif t.estado == 'Pendiente':
                stats[e]['pendientes'] += 1
            elif t.estado == 'Cancelado':
                stats[e]['canceladas'] += 1
            if t.fecha_fin and t.fecha_fin < hoy and t.estado != 'Finalizado':
                stats[e]['atrasadas'] += 1

        encargados_stats = [{
            'nombre': e,
            'total': s['total'],
            'finalizadas': s['finalizadas'],
            'en_proceso': s['en_proceso'],
            'pendientes': s['pendientes'],
            'atrasadas': s['atrasadas'],
            'canceladas': s['canceladas'],
            'porcentaje_completado': round(
                s['finalizadas'] / s['total'] * 100, 1) if s['total'] > 0 else 0
        } for e, s in stats.items()]

        inicio_mes = hoy.replace(day=1)
        inicio_ano = hoy.replace(month=1, day=1)

        return jsonify({
            'resumen': {
                'total_tareas': total,
                'finalizadas': finalizadas,
                'en_proceso': en_proceso,
                'pendientes': pendientes,
                'canceladas': canceladas,
                'atrasadas': len(atrasadas),
                'completadas_mes': len([
                    t for t in todas
                    if t.estado == 'Finalizado' and t.fecha_creacion
                    and t.fecha_creacion.date() >= inicio_mes
                ]),
                'completadas_ano': len([
                    t for t in todas
                    if t.estado == 'Finalizado' and t.fecha_creacion
                    and t.fecha_creacion.date() >= inicio_ano
                ])
            },
            'distribucion_estado': {
                'Finalizado': finalizadas,
                'En Proceso': en_proceso,
                'Pendiente': pendientes,
                'Cancelado': canceladas
            },
            'encargados': {
                'mas_tareas': sorted(
                    encargados_stats, key=lambda x: x['total'], reverse=True)[:5],
                'mas_finalizadas': sorted(
                    encargados_stats, key=lambda x: x['finalizadas'], reverse=True)[:5],
                'mas_atrasadas': sorted(
                    encargados_stats, key=lambda x: x['atrasadas'], reverse=True)[:5],
                'mas_actuales': sorted(
                    encargados_stats,
                    key=lambda x: x['en_proceso'] + x['pendientes'], reverse=True)[:5],
                'todos': encargados_stats
            },
            'tareas_atrasadas': sorted([{
                'id': t.id,
                'numero_df': t.numero_df,
                'tarea': t.tarea,
                'encargado_actual': t.encargado_actual,
                'fecha_fin': t.fecha_fin.strftime('%Y-%m-%d') if t.fecha_fin else None,
                'estado': t.estado,
                'dias_atraso': (hoy - t.fecha_fin).days if t.fecha_fin else 0
            } for t in atrasadas], key=lambda x: x['dias_atraso'], reverse=True)[:20]
        })

    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error al generar estadísticas: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
