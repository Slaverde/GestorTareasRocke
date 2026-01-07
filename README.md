# Gestor de Tareas Comerciales - D&F

Sistema de gestión de tareas comerciales basado en la estructura del Excel "D&F - Tareas Comerciales Pendientes.xlsx". Permite crear, editar, eliminar y delegar tareas de forma 1 a 1, manteniendo un historial completo de todas las delegaciones.

## Características

- ✅ Crear, editar y eliminar tareas
- ✅ Delegación de tareas de 1 a 1 (una persona a otra)
- ✅ Historial completo de delegaciones
- ✅ Filtros por estado, encargado y búsqueda de texto
- ✅ Vista de tarjetas y vista de lista compacta
- ✅ Línea de tiempo tipo roadmap
- ✅ Interfaz moderna y responsive
- ✅ Base de datos SQLite para persistencia

## Instalación Local

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicación:
```bash
python app.py
```

3. Abrir en el navegador:
```
http://localhost:5000
```

## Despliegue

Ver `DEPLOY.md` para instrucciones detalladas de despliegue en Railway, Render u otros servicios.

## Tecnologías

- **Backend:** Flask (Python)
- **Base de Datos:** SQLite con SQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Servidor:** Gunicorn (producción)
