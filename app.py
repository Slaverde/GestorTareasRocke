import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
from io import BytesIO

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
    evidencia = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con delegaciones
    delegaciones = db.relationship(
        'Delegacion', backref='tarea', lazy=True, cascade='all, delete-orphan')


class Encargado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


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

# API - Encargados
@app.route('/api/encargados', methods=['GET'])
def get_encargados():
    encargados = Encargado.query.filter_by(activo=True).order_by(Encargado.nombre).all()
    return jsonify([{
        'id': e.id,
        'nombre': e.nombre,
        'email': e.email
    } for e in encargados])

@app.route('/api/encargados', methods=['POST'])
def crear_encargado():
    data = request.json
    nombre = data.get('nombre', '').strip()
    
    if not nombre:
        return jsonify({'error': 'El nombre es obligatorio'}), 400
    
    # Verificar si ya existe
    existe = Encargado.query.filter_by(nombre=nombre).first()
    if existe:
        if not existe.activo:
            # Reactivar encargado inactivo
            existe.activo = True
            existe.email = data.get('email', '')
            db.session.commit()
            return jsonify({'id': existe.id, 'mensaje': 'Encargado reactivado exitosamente'}), 200
        return jsonify({'error': 'Ya existe un encargado con ese nombre'}), 400
    
    encargado = Encargado(
        nombre=nombre,
        email=data.get('email', '')
    )
    
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
            # Verificar si el nuevo nombre ya existe
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
    # No eliminar físicamente, solo desactivar
    encargado.activo = False
    db.session.commit()
    return jsonify({'mensaje': 'Encargado eliminado exitosamente'})

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


# API - Exportar tareas a Excel
@app.route('/api/tareas/exportar', methods=['GET'])
def exportar_tareas():
    tareas = Tarea.query.all()
    
    # Crear DataFrame con todas las tareas
    datos = []
    for tarea in tareas:
        datos.append({
            'Número de Tarea': tarea.numero_df or '',
            'ACTIVIDAD PREDECESORA': tarea.actividad_predecesora or '',
            'ASUNTO, TEMA': tarea.asunto_tema or '',
            'TAREA': tarea.tarea or '',
            'ENCARGADO(A)': tarea.encargado_actual or '',
            'FECHA INICIO': tarea.fecha_inicio.strftime('%Y-%m-%d') if tarea.fecha_inicio else '',
            'FECHA FIN': tarea.fecha_fin.strftime('%Y-%m-%d') if tarea.fecha_fin else '',
            'ESTADO': tarea.estado or '',
            'DÍAS': tarea.dias if tarea.dias is not None else '',
            'EVIDENCIA, CONCLUSIÓN, RESULTADO, SOPORTE.': tarea.evidencia or '',
            'OBSERVACIONES': tarea.observaciones or ''
        })
    
    df = pd.DataFrame(datos)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tareas')
    
    output.seek(0)
    
    # Generar nombre de archivo con fecha
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'Tareas_Comerciales_{fecha}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# API - Importar tareas desde Excel
@app.route('/api/tareas/importar', methods=['POST'])
def importar_tareas():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400
    
    archivo = request.files['archivo']
    
    if archivo.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    try:
        # Leer el archivo Excel
        df = pd.read_excel(archivo)
        
        # Mapear columnas (flexible con diferentes nombres)
        columnas_mapeo = {
            'Número de Tarea': 'numero_df',
            '# D&F': 'numero_df',  # Compatibilidad con formato antiguo
            'ACTIVIDAD PREDECESORA': 'actividad_predecesora',
            'ASUNTO, TEMA': 'asunto_tema',
            'TAREA': 'tarea',
            'ENCARGADO(A)': 'encargado_actual',
            'FECHA INICIO': 'fecha_inicio',
            'FECHA FIN': 'fecha_fin',
            'ESTADO': 'estado',
            'DÍAS': 'dias',
            'EVIDENCIA, CONCLUSIÓN, RESULTADO, SOPORTE.': 'evidencia',
            'OBSERVACIONES': 'observaciones'
        }
        
        tareas_importadas = 0
        tareas_actualizadas = 0
        errores = []
        
        for index, row in df.iterrows():
            try:
                # Buscar tarea existente por número de tarea o crear nueva
                numero_df = str(row.get('Número de Tarea', '')).strip() if pd.notna(row.get('Número de Tarea', '')) else None
                # También aceptar el formato antiguo '# D&F' para compatibilidad
                if not numero_df:
                    numero_df = str(row.get('# D&F', '')).strip() if pd.notna(row.get('# D&F', '')) else None
                tarea_existente = None
                
                if numero_df:
                    tarea_existente = Tarea.query.filter_by(numero_df=numero_df).first()
                
                # Preparar datos
                datos_tarea = {}
                for col_excel, campo_db in columnas_mapeo.items():
                    if col_excel in df.columns:
                        valor = row[col_excel]
                        if pd.notna(valor):
                            if campo_db in ['fecha_inicio', 'fecha_fin']:
                                try:
                                    if isinstance(valor, str):
                                        datos_tarea[campo_db] = datetime.strptime(valor, '%Y-%m-%d').date()
                                    else:
                                        datos_tarea[campo_db] = valor.date() if hasattr(valor, 'date') else None
                                except:
                                    datos_tarea[campo_db] = None
                            elif campo_db == 'dias':
                                try:
                                    datos_tarea[campo_db] = int(valor) if pd.notna(valor) else None
                                except:
                                    datos_tarea[campo_db] = None
                            else:
                                datos_tarea[campo_db] = str(valor).strip()
                
                # Validar campos obligatorios
                if not datos_tarea.get('tarea') or not datos_tarea.get('encargado_actual'):
                    errores.append(f'Fila {index + 2}: Faltan campos obligatorios (TAREA o ENCARGADO)')
                    continue
                
                # Calcular días si hay fechas
                if datos_tarea.get('fecha_inicio') and datos_tarea.get('fecha_fin'):
                    dias = (datos_tarea['fecha_fin'] - datos_tarea['fecha_inicio']).days
                    datos_tarea['dias'] = dias
                elif datos_tarea.get('fecha_inicio') and not datos_tarea.get('dias'):
                    datos_tarea['dias'] = (datetime.now().date() - datos_tarea['fecha_inicio']).days
                
                # Establecer fecha de inicio por defecto si no existe
                if not datos_tarea.get('fecha_inicio'):
                    datos_tarea['fecha_inicio'] = datetime.now().date()
                
                # Establecer estado por defecto
                if not datos_tarea.get('estado'):
                    datos_tarea['estado'] = 'Pendiente'
                
                if tarea_existente:
                    # Actualizar tarea existente
                    for campo, valor in datos_tarea.items():
                        setattr(tarea_existente, campo, valor)
                    tareas_actualizadas += 1
                else:
                    # Crear nueva tarea
                    nueva_tarea = Tarea(**datos_tarea)
                    db.session.add(nueva_tarea)
                    tareas_importadas += 1
                    
            except Exception as e:
                errores.append(f'Fila {index + 2}: {str(e)}')
                continue
        
        db.session.commit()
        
        mensaje = f'Importación completada: {tareas_importadas} tareas nuevas, {tareas_actualizadas} actualizadas'
        if errores:
            mensaje += f'. {len(errores)} errores encontrados.'
        
        return jsonify({
            'mensaje': mensaje,
            'tareas_importadas': tareas_importadas,
            'tareas_actualizadas': tareas_actualizadas,
            'errores': errores[:10]  # Limitar a 10 errores
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500


if __name__ == '__main__':
    # En producción, usar el puerto de la variable de entorno
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
