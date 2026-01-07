let tareas = [];
let tareaEditando = null;
let vistaActual = 'tarjetas'; // 'tarjetas' o 'lista'

// Cargar tareas al iniciar
document.addEventListener('DOMContentLoaded', function () {
    cargarTareas();
});

// Cargar todas las tareas
async function cargarTareas() {
    try {
        const response = await fetch('/api/tareas');
        tareas = await response.json();
        renderizarTareas();
        actualizarFiltros();
    } catch (error) {
        console.error('Error al cargar tareas:', error);
        alert('Error al cargar las tareas');
    }
}

// Cambiar entre vista de tarjetas y lista
function cambiarVista(tipo) {
    vistaActual = tipo;

    // Actualizar botones
    document.getElementById('btnVistaTarjetas').classList.toggle('btn-vista-active', tipo === 'tarjetas');
    document.getElementById('btnVistaLista').classList.toggle('btn-vista-active', tipo === 'lista');

    // Cambiar clase del contenedor
    const container = document.getElementById('tareasContainer');
    container.className = tipo === 'lista' ? 'tareas-container lista-vista' : 'tareas-container';

    // Re-renderizar
    filtrarTareas();
}

// Renderizar tareas en el contenedor
function renderizarTareas() {
    const container = document.getElementById('tareasContainer');
    container.innerHTML = '';

    if (tareas.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">No hay tareas registradas</p>';
        return;
    }

    if (vistaActual === 'lista') {
        renderizarVistaLista();
    } else {
        tareas.forEach(tarea => {
            const card = crearCardTarea(tarea);
            container.appendChild(card);
        });
    }
}

// Crear card de tarea
function crearCardTarea(tarea) {
    const card = document.createElement('div');
    card.className = `tarea-card ${tarea.estado.toLowerCase().replace(' ', '-')}`;

    const fechaInicio = tarea.fecha_inicio ? new Date(tarea.fecha_inicio).toLocaleDateString('es-ES') : 'N/A';
    const fechaFin = tarea.fecha_fin ? new Date(tarea.fecha_fin).toLocaleDateString('es-ES') : 'Pendiente';

    card.innerHTML = `
        <div class="tarea-header">
            <span class="tarea-numero">${tarea.numero_df || 'Sin número'}</span>
            <span class="estado-badge ${tarea.estado.toLowerCase().replace(' ', '-')}">${tarea.estado}</span>
        </div>
        <div class="tarea-titulo" onclick="verDetallesTarea(${tarea.id})" style="cursor: pointer; text-decoration: underline;">${tarea.tarea || 'Sin descripción'}</div>
        <div class="tarea-info">
            <div class="tarea-info-item">
                <strong>Inicio:</strong> ${fechaInicio}
            </div>
            <div class="tarea-info-item">
                <strong>Fin:</strong> ${fechaFin}
            </div>
            ${tarea.dias !== null ? `<div class="tarea-info-item"><strong>Días:</strong> ${tarea.dias}</div>` : ''}
            ${tarea.valor ? `<div class="tarea-info-item"><strong>Valor:</strong> ${tarea.valor}</div>` : ''}
        </div>
        <div class="tarea-encargado">
            👤 Encargado: ${tarea.encargado_actual}
        </div>
        ${tarea.asunto_tema ? `<div style="margin-bottom: 10px; font-size: 0.9em; color: #666;"><strong>Asunto:</strong> ${tarea.asunto_tema}</div>` : ''}
        ${tarea.observaciones ? `<div style="margin-bottom: 10px; font-size: 0.85em; color: #888; font-style: italic;">${tarea.observaciones.substring(0, 100)}${tarea.observaciones.length > 100 ? '...' : ''}</div>` : ''}
        <div class="tarea-acciones">
            <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); verDetallesTarea(${tarea.id})">Ver Detalles</button>
            <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); editarTarea(${tarea.id})">Editar</button>
            <button class="btn btn-success btn-sm" onclick="event.stopPropagation(); abrirModalDelegar(${tarea.id})">Delegar</button>
            ${tarea.delegaciones && tarea.delegaciones.length > 0 ?
            `<button class="btn btn-info btn-sm" onclick="event.stopPropagation(); verHistorial(${tarea.id})">Historial (${tarea.delegaciones.length})</button>` :
            ''}
            <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); eliminarTarea(${tarea.id})">Eliminar</button>
        </div>
    `;

    return card;
}

// Filtrar tareas
function filtrarTareas() {
    const textoBusqueda = document.getElementById('buscarTarea').value.toLowerCase();
    const filtroEstado = document.getElementById('filtroEstado').value;
    const filtroEncargado = document.getElementById('filtroEncargado').value;
    const ordenarFecha = document.getElementById('ordenarFecha').value;

    const tareasFiltradas = tareas.filter(tarea => {
        const coincideTexto = !textoBusqueda ||
            (tarea.tarea && tarea.tarea.toLowerCase().includes(textoBusqueda)) ||
            (tarea.asunto_tema && tarea.asunto_tema.toLowerCase().includes(textoBusqueda)) ||
            (tarea.encargado_actual && tarea.encargado_actual.toLowerCase().includes(textoBusqueda));

        const coincideEstado = !filtroEstado || tarea.estado === filtroEstado;
        const coincideEncargado = !filtroEncargado || tarea.encargado_actual === filtroEncargado;

        return coincideTexto && coincideEstado && coincideEncargado;
    });

    // Ordenar por fecha si se seleccionó una opción
    if (ordenarFecha) {
        tareasFiltradas.sort((a, b) => {
            let fechaA, fechaB;

            switch (ordenarFecha) {
                case 'fecha_inicio_asc':
                    fechaA = a.fecha_inicio ? new Date(a.fecha_inicio) : new Date(0);
                    fechaB = b.fecha_inicio ? new Date(b.fecha_inicio) : new Date(0);
                    return fechaA - fechaB;
                case 'fecha_inicio_desc':
                    fechaA = a.fecha_inicio ? new Date(a.fecha_inicio) : new Date(0);
                    fechaB = b.fecha_inicio ? new Date(b.fecha_inicio) : new Date(0);
                    return fechaB - fechaA;
                case 'fecha_fin_asc':
                    fechaA = a.fecha_fin ? new Date(a.fecha_fin) : new Date('9999-12-31');
                    fechaB = b.fecha_fin ? new Date(b.fecha_fin) : new Date('9999-12-31');
                    return fechaA - fechaB;
                case 'fecha_fin_desc':
                    fechaA = a.fecha_fin ? new Date(a.fecha_fin) : new Date(0);
                    fechaB = b.fecha_fin ? new Date(b.fecha_fin) : new Date(0);
                    return fechaB - fechaA;
                case 'fecha_creacion_asc':
                    fechaA = a.fecha_creacion ? new Date(a.fecha_creacion) : new Date(0);
                    fechaB = b.fecha_creacion ? new Date(b.fecha_creacion) : new Date(0);
                    return fechaA - fechaB;
                case 'fecha_creacion_desc':
                    fechaA = a.fecha_creacion ? new Date(a.fecha_creacion) : new Date(0);
                    fechaB = b.fecha_creacion ? new Date(b.fecha_creacion) : new Date(0);
                    return fechaB - fechaA;
                default:
                    return 0;
            }
        });
    }

    const container = document.getElementById('tareasContainer');
    container.innerHTML = '';

    if (tareasFiltradas.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">No se encontraron tareas</p>';
        return;
    }

    if (vistaActual === 'lista') {
        renderizarVistaListaFiltrada(tareasFiltradas);
    } else {
        tareasFiltradas.forEach(tarea => {
            const card = crearCardTarea(tarea);
            container.appendChild(card);
        });
    }
}

// Renderizar vista de lista compacta
function renderizarVistaLista() {
    renderizarVistaListaFiltrada(tareas);
}

// Renderizar vista de lista con tareas filtradas
function renderizarVistaListaFiltrada(tareasFiltradas) {
    const container = document.getElementById('tareasContainer');

    if (tareasFiltradas.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">No se encontraron tareas</p>';
        return;
    }

    // Crear tabla
    let html = '<table class="tabla-tareas">';
    html += '<thead><tr>';
    html += '<th>#</th>';
    html += '<th>Tarea</th>';
    html += '<th>Encargado</th>';
    html += '<th>Estado</th>';
    html += '<th>Fecha Inicio</th>';
    html += '<th>Fecha Fin</th>';
    html += '<th>Días</th>';
    html += '<th>Acciones</th>';
    html += '</tr></thead>';
    html += '<tbody>';

    tareasFiltradas.forEach(tarea => {
        const fechaInicio = tarea.fecha_inicio ? new Date(tarea.fecha_inicio).toLocaleDateString('es-ES') : 'N/A';
        const fechaFin = tarea.fecha_fin ? new Date(tarea.fecha_fin).toLocaleDateString('es-ES') : 'Pendiente';
        const estadoClass = tarea.estado.toLowerCase().replace(' ', '-');

        html += `<tr class="fila-tarea ${estadoClass}" onclick="verDetallesTarea(${tarea.id})">`;
        html += `<td class="col-numero">${tarea.numero_df || '-'}</td>`;
        html += `<td class="col-tarea"><strong>${tarea.tarea || 'Sin descripción'}</strong></td>`;
        html += `<td class="col-encargado">${tarea.encargado_actual}</td>`;
        html += `<td class="col-estado"><span class="estado-badge ${estadoClass}">${tarea.estado}</span></td>`;
        html += `<td class="col-fecha">${fechaInicio}</td>`;
        html += `<td class="col-fecha">${fechaFin}</td>`;
        html += `<td class="col-dias">${tarea.dias !== null ? tarea.dias : '-'}</td>`;
        html += `<td class="col-acciones" onclick="event.stopPropagation();">`;
        html += `<button class="btn btn-primary btn-xs" onclick="verDetallesTarea(${tarea.id})" title="Ver detalles">👁️</button> `;
        html += `<button class="btn btn-primary btn-xs" onclick="editarTarea(${tarea.id})" title="Editar">✏️</button> `;
        html += `<button class="btn btn-success btn-xs" onclick="abrirModalDelegar(${tarea.id})" title="Delegar">👤</button> `;
        if (tarea.delegaciones && tarea.delegaciones.length > 0) {
            html += `<button class="btn btn-info btn-xs" onclick="verHistorial(${tarea.id})" title="Historial">📋</button> `;
        }
        html += `<button class="btn btn-danger btn-xs" onclick="eliminarTarea(${tarea.id})" title="Eliminar">🗑️</button>`;
        html += `</td>`;
        html += `</tr>`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// Actualizar filtros de encargados
function actualizarFiltros() {
    const select = document.getElementById('filtroEncargado');
    const encargados = [...new Set(tareas.map(t => t.encargado_actual).filter(Boolean))];

    // Mantener el valor seleccionado
    const valorActual = select.value;

    // Limpiar opciones excepto "Todos"
    select.innerHTML = '<option value="">Todos los encargados</option>';

    encargados.forEach(encargado => {
        const option = document.createElement('option');
        option.value = encargado;
        option.textContent = encargado;
        select.appendChild(option);
    });

    // Restaurar valor seleccionado
    select.value = valorActual;
}

// Abrir modal para crear tarea
function abrirModalCrear() {
    tareaEditando = null;
    document.getElementById('modalTitulo').textContent = 'Nueva Tarea';
    document.getElementById('formTarea').reset();
    document.getElementById('fecha_inicio').value = new Date().toISOString().split('T')[0];
    document.getElementById('modalTarea').style.display = 'block';
}

// Cerrar modal
function cerrarModal() {
    document.getElementById('modalTarea').style.display = 'none';
    tareaEditando = null;
}

// Guardar tarea (crear o actualizar)
async function guardarTarea(event) {
    event.preventDefault();

    const formData = {
        numero_df: document.getElementById('numero_df').value,
        actividad_predecesora: document.getElementById('actividad_predecesora').value,
        asunto_tema: document.getElementById('asunto_tema').value,
        tarea: document.getElementById('tarea').value,
        encargado_actual: document.getElementById('encargado_actual').value,
        fecha_inicio: document.getElementById('fecha_inicio').value,
        fecha_fin: document.getElementById('fecha_fin').value || null,
        estado: document.getElementById('estado').value,
        valor: document.getElementById('valor').value,
        evidencia: document.getElementById('evidencia').value,
        observaciones: document.getElementById('observaciones').value
    };

    try {
        if (tareaEditando) {
            // Actualizar
            const response = await fetch(`/api/tareas/${tareaEditando}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                alert('Tarea actualizada exitosamente');
                cerrarModal();
                cargarTareas();
            } else {
                throw new Error('Error al actualizar');
            }
        } else {
            // Crear
            const response = await fetch('/api/tareas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                alert('Tarea creada exitosamente');
                cerrarModal();
                cargarTareas();
            } else {
                throw new Error('Error al crear');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar la tarea');
    }
}

// Editar tarea
function editarTarea(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

    tareaEditando = id;
    document.getElementById('modalTitulo').textContent = 'Editar Tarea';

    document.getElementById('numero_df').value = tarea.numero_df || '';
    document.getElementById('actividad_predecesora').value = tarea.actividad_predecesora || '';
    document.getElementById('asunto_tema').value = tarea.asunto_tema || '';
    document.getElementById('tarea').value = tarea.tarea || '';
    document.getElementById('encargado_actual').value = tarea.encargado_actual || '';
    document.getElementById('fecha_inicio').value = tarea.fecha_inicio || '';
    document.getElementById('fecha_fin').value = tarea.fecha_fin || '';
    document.getElementById('estado').value = tarea.estado || 'Pendiente';
    document.getElementById('valor').value = tarea.valor || '';
    document.getElementById('evidencia').value = tarea.evidencia || '';
    document.getElementById('observaciones').value = tarea.observaciones || '';

    document.getElementById('modalTarea').style.display = 'block';
}

// Eliminar tarea
async function eliminarTarea(id) {
    if (!confirm('¿Está seguro de eliminar esta tarea?')) return;

    try {
        const response = await fetch(`/api/tareas/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Tarea eliminada exitosamente');
            cargarTareas();
        } else {
            throw new Error('Error al eliminar');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar la tarea');
    }
}

// Abrir modal para delegar
async function abrirModalDelegar(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

    document.getElementById('tarea_id_delegar').value = id;
    document.getElementById('delegado_de').value = tarea.encargado_actual;
    document.getElementById('delegado_a').value = '';
    document.getElementById('motivo').value = '';
    document.getElementById('observaciones_delegacion').value = '';

    document.getElementById('modalDelegar').style.display = 'block';
}

// Cerrar modal de delegar
function cerrarModalDelegar() {
    document.getElementById('modalDelegar').style.display = 'none';
}

// Guardar delegación
async function guardarDelegacion(event) {
    event.preventDefault();

    const tareaId = document.getElementById('tarea_id_delegar').value;
    const delegadoDe = document.getElementById('delegado_de').value;
    const delegadoA = document.getElementById('delegado_a').value;

    if (delegadoDe === delegadoA) {
        alert('No puede delegar la tarea a la misma persona');
        return;
    }

    const formData = {
        delegado_de: delegadoDe,
        delegado_a: delegadoA,
        motivo: document.getElementById('motivo').value,
        observaciones_delegacion: document.getElementById('observaciones_delegacion').value
    };

    try {
        const response = await fetch(`/api/tareas/${tareaId}/delegar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('Tarea delegada exitosamente');
            cerrarModalDelegar();
            cargarTareas();
        } else {
            throw new Error('Error al delegar');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al delegar la tarea');
    }
}

// Ver historial de delegaciones
async function verHistorial(id) {
    try {
        const response = await fetch(`/api/tareas/${id}/delegaciones`);
        const delegaciones = await response.json();

        const content = document.getElementById('historialContent');

        if (delegaciones.length === 0) {
            content.innerHTML = '<div class="sin-delegaciones">No hay historial de delegaciones para esta tarea</div>';
        } else {
            content.innerHTML = delegaciones.map(d => `
                <div class="historial-item">
                    <div class="historial-item-header">
                        <span>Delegación #${d.id}</span>
                        <span>${new Date(d.fecha_delegacion).toLocaleString('es-ES')}</span>
                    </div>
                    <div class="historial-item-info">
                        <strong>De:</strong> ${d.delegado_de}
                    </div>
                    <div class="historial-item-info">
                        <strong>A:</strong> ${d.delegado_a}
                    </div>
                    ${d.motivo ? `<div class="historial-item-info"><strong>Motivo:</strong> ${d.motivo}</div>` : ''}
                    ${d.observaciones_delegacion ? `<div class="historial-item-info"><strong>Observaciones:</strong> ${d.observaciones_delegacion}</div>` : ''}
                </div>
            `).join('');
        }

        document.getElementById('modalHistorial').style.display = 'block';
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar el historial');
    }
}

// Cerrar modal de historial
function cerrarModalHistorial() {
    document.getElementById('modalHistorial').style.display = 'none';
}

// Ver detalles completos de la tarea
function verDetallesTarea(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

    const fechaInicio = tarea.fecha_inicio ? new Date(tarea.fecha_inicio).toLocaleDateString('es-ES') : 'No especificada';
    const fechaFin = tarea.fecha_fin ? new Date(tarea.fecha_fin).toLocaleDateString('es-ES') : 'Pendiente';
    const fechaCreacion = tarea.fecha_creacion ? new Date(tarea.fecha_creacion).toLocaleString('es-ES') : 'N/A';

    const content = document.getElementById('detallesContent');
    content.innerHTML = `
        <div class="detalle-seccion">
            <h3>Información General</h3>
            <div class="detalle-item">
                <strong># D&F:</strong> ${tarea.numero_df || 'Sin número'}
            </div>
            <div class="detalle-item">
                <strong>Estado:</strong> <span class="estado-badge ${tarea.estado.toLowerCase().replace(' ', '-')}">${tarea.estado}</span>
            </div>
            ${tarea.actividad_predecesora ? `
            <div class="detalle-item">
                <strong>Actividad Predecesora:</strong> ${tarea.actividad_predecesora}
            </div>
            ` : ''}
            ${tarea.asunto_tema ? `
            <div class="detalle-item">
                <strong>Asunto, Tema:</strong> ${tarea.asunto_tema}
            </div>
            ` : ''}
        </div>
        
        <div class="detalle-seccion">
            <h3>Descripción de la Tarea</h3>
            <div class="detalle-item detalle-texto">
                ${tarea.tarea || 'Sin descripción'}
            </div>
        </div>
        
        <div class="detalle-seccion">
            <h3>Responsable y Fechas</h3>
            <div class="detalle-item">
                <strong>Encargado(a):</strong> ${tarea.encargado_actual}
            </div>
            <div class="detalle-item">
                <strong>Fecha de Inicio:</strong> ${fechaInicio}
            </div>
            <div class="detalle-item">
                <strong>Fecha de Fin:</strong> ${fechaFin}
            </div>
            ${tarea.dias !== null ? `
            <div class="detalle-item">
                <strong>Días:</strong> ${tarea.dias} día(s)
            </div>
            ` : ''}
            <div class="detalle-item">
                <strong>Fecha de Creación:</strong> ${fechaCreacion}
            </div>
        </div>
        
        ${tarea.valor ? `
        <div class="detalle-seccion">
            <h3>Valor</h3>
            <div class="detalle-item">
                ${tarea.valor}
            </div>
        </div>
        ` : ''}
        
        ${tarea.evidencia ? `
        <div class="detalle-seccion">
            <h3>Evidencia, Conclusión, Resultado, Soporte</h3>
            <div class="detalle-item detalle-texto">
                ${tarea.evidencia}
            </div>
        </div>
        ` : ''}
        
        ${tarea.observaciones ? `
        <div class="detalle-seccion">
            <h3>Observaciones</h3>
            <div class="detalle-item detalle-texto">
                ${tarea.observaciones}
            </div>
        </div>
        ` : ''}
        
        ${tarea.delegaciones && tarea.delegaciones.length > 0 ? `
        <div class="detalle-seccion">
            <h3>Historial de Delegaciones (${tarea.delegaciones.length})</h3>
            ${tarea.delegaciones.map((d, index) => `
                <div class="delegacion-item">
                    <div class="delegacion-header">
                        <strong>Delegación #${index + 1}</strong>
                        <span>${new Date(d.fecha_delegacion).toLocaleString('es-ES')}</span>
                    </div>
                    <div class="delegacion-info">
                        <strong>De:</strong> ${d.delegado_de} → <strong>A:</strong> ${d.delegado_a}
                    </div>
                    ${d.motivo ? `<div class="delegacion-info"><strong>Motivo:</strong> ${d.motivo}</div>` : ''}
                    ${d.observaciones_delegacion ? `<div class="delegacion-info"><strong>Observaciones:</strong> ${d.observaciones_delegacion}</div>` : ''}
                </div>
            `).join('')}
        </div>
        ` : ''}
        
        <div class="detalle-acciones">
            <button class="btn btn-primary" onclick="editarTarea(${tarea.id}); cerrarModalDetalles();">Editar Tarea</button>
            <button class="btn btn-success" onclick="abrirModalDelegar(${tarea.id}); cerrarModalDetalles();">Delegar Tarea</button>
            ${tarea.delegaciones && tarea.delegaciones.length > 0 ?
            `<button class="btn btn-info" onclick="verHistorial(${tarea.id}); cerrarModalDetalles();">Ver Historial Completo</button>` :
            ''}
        </div>
    `;

    document.getElementById('modalDetalles').style.display = 'block';
}

// Cerrar modal de detalles
function cerrarModalDetalles() {
    document.getElementById('modalDetalles').style.display = 'none';
}

// Cerrar modales al hacer clic fuera
window.onclick = function (event) {
    const modalTarea = document.getElementById('modalTarea');
    const modalDelegar = document.getElementById('modalDelegar');
    const modalHistorial = document.getElementById('modalHistorial');
    const modalDetalles = document.getElementById('modalDetalles');

    if (event.target === modalTarea) {
        cerrarModal();
    }
    if (event.target === modalDelegar) {
        cerrarModalDelegar();
    }
    if (event.target === modalHistorial) {
        cerrarModalHistorial();
    }
    if (event.target === modalDetalles) {
        cerrarModalDetalles();
    }
    if (event.target === modalLineaTiempo) {
        cerrarLineaTiempo();
    }
}

// Abrir línea de tiempo
function abrirLineaTiempo() {
    actualizarLineaTiempo();
    document.getElementById('modalLineaTiempo').style.display = 'block';
}

// Cerrar línea de tiempo
function cerrarLineaTiempo() {
    document.getElementById('modalLineaTiempo').style.display = 'none';
}

// Actualizar línea de tiempo
function actualizarLineaTiempo() {
    const tipoFecha = document.getElementById('filtroLineaTiempo').value;
    const filtroEstado = document.getElementById('filtroEstadoLinea').value;

    // Filtrar tareas
    let tareasFiltradas = tareas.filter(tarea => {
        if (filtroEstado && tarea.estado !== filtroEstado) {
            return false;
        }
        return true;
    });

    // Ordenar por fecha seleccionada
    tareasFiltradas.sort((a, b) => {
        let fechaA, fechaB;

        switch (tipoFecha) {
            case 'fecha_creacion':
                fechaA = a.fecha_creacion ? new Date(a.fecha_creacion) : new Date(0);
                fechaB = b.fecha_creacion ? new Date(b.fecha_creacion) : new Date(0);
                break;
            case 'fecha_inicio':
                fechaA = a.fecha_inicio ? new Date(a.fecha_inicio) : new Date(0);
                fechaB = b.fecha_inicio ? new Date(b.fecha_inicio) : new Date(0);
                break;
            case 'fecha_fin':
                fechaA = a.fecha_fin ? new Date(a.fecha_fin) : new Date('9999-12-31');
                fechaB = b.fecha_fin ? new Date(b.fecha_fin) : new Date('9999-12-31');
                break;
            default:
                return 0;
        }

        return fechaA - fechaB; // Orden ascendente (más antigua primero)
    });

    // Renderizar línea de tiempo
    const content = document.getElementById('lineaTiempoContent');

    if (tareasFiltradas.length === 0) {
        content.innerHTML = '<div class="sin-tareas-timeline">No hay tareas para mostrar</div>';
        return;
    }

    // Obtener rango de fechas
    let fechas = [];
    tareasFiltradas.forEach(tarea => {
        let fecha;
        switch (tipoFecha) {
            case 'fecha_creacion':
                fecha = tarea.fecha_creacion ? new Date(tarea.fecha_creacion) : null;
                break;
            case 'fecha_inicio':
                fecha = tarea.fecha_inicio ? new Date(tarea.fecha_inicio) : null;
                break;
            case 'fecha_fin':
                fecha = tarea.fecha_fin ? new Date(tarea.fecha_fin) : null;
                break;
        }
        if (fecha) fechas.push(fecha);
    });

    if (fechas.length === 0) {
        content.innerHTML = '<div class="sin-tareas-timeline">No hay tareas con fechas para mostrar</div>';
        return;
    }

    // Renderizar roadmap horizontal

    const fechaMin = new Date(Math.min(...fechas));
    const fechaMax = new Date(Math.max(...fechas));

    // Extender el rango un poco para mejor visualización
    fechaMin.setMonth(fechaMin.getMonth() - 1);
    fechaMax.setMonth(fechaMax.getMonth() + 1);

    // Crear puntos de tiempo (meses)
    const puntosTiempo = [];
    const fechaActual = new Date(fechaMin);

    while (fechaActual <= fechaMax) {
        const mes = fechaActual.toLocaleDateString('es-ES', { month: 'short', year: 'numeric' });
        const mesCompleto = fechaActual.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
        puntosTiempo.push({
            fecha: new Date(fechaActual),
            label: mes,
            labelCompleto: mesCompleto
        });
        fechaActual.setMonth(fechaActual.getMonth() + 1);
    }

    // Asignar tareas a puntos de tiempo
    const tareasPorPunto = {};
    puntosTiempo.forEach(punto => {
        tareasPorPunto[punto.label] = [];
    });

    tareasFiltradas.forEach(tarea => {
        let fecha;
        switch (tipoFecha) {
            case 'fecha_creacion':
                fecha = tarea.fecha_creacion ? new Date(tarea.fecha_creacion) : null;
                break;
            case 'fecha_inicio':
                fecha = tarea.fecha_inicio ? new Date(tarea.fecha_inicio) : null;
                break;
            case 'fecha_fin':
                fecha = tarea.fecha_fin ? new Date(tarea.fecha_fin) : null;
                break;
        }

        if (fecha) {
            const mesLabel = fecha.toLocaleDateString('es-ES', { month: 'short', year: 'numeric' });
            if (tareasPorPunto[mesLabel]) {
                tareasPorPunto[mesLabel].push(tarea);
            } else {
                // Buscar el punto más cercano
                let puntoMasCercano = puntosTiempo[0];
                let diferenciaMin = Math.abs(fecha - puntosTiempo[0].fecha);
                puntosTiempo.forEach(punto => {
                    const diferencia = Math.abs(fecha - punto.fecha);
                    if (diferencia < diferenciaMin) {
                        diferenciaMin = diferencia;
                        puntoMasCercano = punto;
                    }
                });
                if (!tareasPorPunto[puntoMasCercano.label]) {
                    tareasPorPunto[puntoMasCercano.label] = [];
                }
                tareasPorPunto[puntoMasCercano.label].push(tarea);
            }
        }
    });

    let html = '<div class="roadmap-container">';

    // Área de tareas (arriba)
    html += '<div class="roadmap-tasks-area">';

    puntosTiempo.forEach((punto, index) => {
        const tareasDelMes = tareasPorPunto[punto.label] || [];
        const tieneTareas = tareasDelMes.length > 0;

        if (tieneTareas) {
            tareasDelMes.forEach((tarea, tareaIndex) => {
                const estadoClass = tarea.estado.toLowerCase().replace(' ', '-');
                const leftPosition = (index / puntosTiempo.length) * 100;
                const topOffset = tareaIndex * 120; // Espaciado vertical entre tareas

                html += `
                    <div class="roadmap-task-box ${estadoClass}" 
                         style="left: ${leftPosition}%; top: ${topOffset}px;"
                         onclick="verDetallesTarea(${tarea.id}); cerrarLineaTiempo();">
                        <div class="roadmap-task-connector"></div>
                        <div class="roadmap-task-content">
                            <div class="roadmap-task-header">
                                <span class="roadmap-task-numero">${tarea.numero_df || 'Sin #'}</span>
                                <span class="estado-badge ${estadoClass}">${tarea.estado}</span>
                            </div>
                            <div class="roadmap-task-title">${(tarea.tarea || 'Sin descripción').substring(0, 50)}${(tarea.tarea || '').length > 50 ? '...' : ''}</div>
                            <div class="roadmap-task-info">
                                <span>👤 ${tarea.encargado_actual}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
    });

    html += '</div>';

    // Línea de tiempo (abajo)
    html += '<div class="roadmap-timeline-area">';
    html += '<div class="roadmap-timeline-line"></div>';

    puntosTiempo.forEach((punto, index) => {
        const tareasDelMes = tareasPorPunto[punto.label] || [];
        const leftPosition = (index / puntosTiempo.length) * 100;

        // Determinar trimestre
        const mes = punto.fecha.getMonth();
        let trimestre = '';
        if (mes >= 0 && mes < 3) trimestre = 'Q1';
        else if (mes >= 3 && mes < 6) trimestre = 'Q2';
        else if (mes >= 6 && mes < 9) trimestre = 'Q3';
        else trimestre = 'Q4';

        html += `
            <div class="roadmap-timeline-marker" style="left: ${leftPosition}%">
                <div class="roadmap-timeline-number">${String(index).padStart(2, '0')}</div>
                <div class="roadmap-timeline-month">${punto.label}</div>
                ${index % 3 === 0 ? `<div class="roadmap-timeline-quarter">${trimestre}</div>` : ''}
                ${index === 0 ? '<div class="roadmap-timeline-quarter">Inicio</div>' : ''}
            </div>
        `;
    });

    html += '</div>';
    html += '</div>';

    content.innerHTML = html;
}

