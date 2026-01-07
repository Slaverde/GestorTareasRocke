# Solución para el Error de Railway

## Problema
Railway muestra: "Railpack could not determine how to build the app"

## Solución Rápida

### Opción 1: Configuración Manual en Railway

1. Ve a tu proyecto en Railway
2. Haz clic en **Settings**
3. En la sección **Build & Deploy**, configura manualmente:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Root Directory**: `/` (dejar vacío)

### Opción 2: Usar Dockerfile (Recomendado)

He creado un `Dockerfile` que Railway puede usar automáticamente.

1. En Railway, ve a Settings
2. En Build & Deploy, selecciona **Dockerfile** como builder
3. Railway usará el Dockerfile automáticamente

### Opción 3: Cambiar a Render (Más Simple)

Si Railway sigue dando problemas:

1. Ve a https://render.com
2. "New +" → "Web Service"
3. Conecta tu repositorio
4. Configuración:
   - **Name**: gestor-tareas-df
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
5. Clic en "Create Web Service"

## Archivos Importantes

Asegúrate de que estos archivos estén en la raíz:
- ✅ `app.py` (archivo principal)
- ✅ `requirements.txt`
- ✅ `Procfile`
- ✅ `Dockerfile` (nuevo)
- ✅ `railway.json` (nuevo)

## Verificar en GitHub

Antes de desplegar, asegúrate de que todos los archivos estén en GitHub:

```bash
git add .
git commit -m "Fix Railway deployment"
git push
```

