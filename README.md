# Gestor de Tareas - Rocket

Sistema web para gestión de tareas comerciales. Permite crear, editar, eliminar y delegar tareas, con historial de delegaciones, vistas Kanban/lista/roadmap e informes.

## Stack

- **Backend:** Flask + Flask-SQLAlchemy + Flask-SocketIO
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Base de datos:** PostgreSQL en producción (Neon), SQLite en local
- **Hosting:** Vercel (serverless WSGI)

## Variables de entorno requeridas

Copia `.env.example` como `.env` y completa los valores:

```
DATABASE_URL=postgresql://usuario:contraseña@host:5432/nombre_bd
SECRET_KEY=clave-secreta-larga-y-aleatoria
```

En Vercel, agrega estas variables desde **Project → Settings → Environment Variables**.

## Desarrollo local

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
# Abre http://localhost:5000
```

Sin `DATABASE_URL`, la app usa SQLite automáticamente (`instance/tareas.db`).

## Despliegue en Vercel

```bash
npx vercel deploy
```

El proyecto ya está vinculado al proyecto `gestor-tareas-rocke` en Vercel.
URL de producción: https://gestor-tareas-rocke.vercel.app

## Base de datos en producción

Ver sección **Recomendaciones de base de datos** más abajo, o conecta directamente
desde el panel de Vercel → Integrations → Neon.
