# Guía de Despliegue - Gestor de Tareas D&F

Esta guía te ayudará a subir tu aplicación a un servidor para que cualquiera pueda accederla.

## Opciones de Despliegue Recomendadas

### Opción 1: Railway (Recomendado - Más Fácil) 🚀

**Railway** es muy fácil de usar y tiene un plan gratuito generoso.

#### Pasos:

1. **Crear cuenta en Railway**
   - Ve a https://railway.app
   - Regístrate con GitHub (recomendado) o email

2. **Subir tu código a GitHub** (si no lo has hecho)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/tu-repositorio.git
   git push -u origin main
   ```

3. **Desplegar en Railway**
   - En Railway, haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio
   - Railway detectará automáticamente que es una app Python
   - ¡Listo! Railway creará automáticamente la URL pública

4. **Configurar base de datos** (opcional)
   - Railway puede crear una base de datos PostgreSQL automáticamente
   - O puedes usar SQLite (ya incluido)

**Ventajas:**
- ✅ Muy fácil de usar
- ✅ Plan gratuito generoso
- ✅ Despliegue automático desde GitHub
- ✅ URL pública automática

---

### Opción 2: Render 🎨

**Render** también es muy fácil y tiene un plan gratuito.

#### Pasos:

1. **Crear cuenta en Render**
   - Ve a https://render.com
   - Regístrate con GitHub

2. **Subir código a GitHub** (igual que arriba)

3. **Crear nuevo Web Service**
   - En Render, haz clic en "New +" → "Web Service"
   - Conecta tu repositorio de GitHub
   - Configuración:
     - **Name**: gestor-tareas-df (o el nombre que quieras)
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
   - Haz clic en "Create Web Service"

4. **Esperar el despliegue**
   - Render construirá y desplegará tu app
   - Te dará una URL como: `https://gestor-tareas-df.onrender.com`

**Ventajas:**
- ✅ Plan gratuito disponible
- ✅ Fácil de usar
- ✅ Despliegue automático

**Nota:** En el plan gratuito, la app se "duerme" después de 15 minutos de inactividad.

---

### Opción 3: PythonAnywhere 🐍

**PythonAnyhouse** es específico para aplicaciones Python.

#### Pasos:

1. **Crear cuenta en PythonAnywhere**
   - Ve a https://www.pythonanywhere.com
   - Crea una cuenta gratuita

2. **Subir archivos**
   - Ve a la pestaña "Files"
   - Sube todos los archivos de tu proyecto

3. **Configurar aplicación web**
   - Ve a la pestaña "Web"
   - Haz clic en "Add a new web app"
   - Selecciona Flask y Python 3.10
   - Configura el path del archivo WSGI

4. **Instalar dependencias**
   - Ve a la pestaña "Tasks"
   - Crea un bash console
   - Ejecuta: `pip3.10 install --user flask flask-sqlalchemy gunicorn`

**Ventajas:**
- ✅ Específico para Python
- ✅ Plan gratuito disponible

---

## Configuración Necesaria

### Archivos ya creados:
- ✅ `Procfile` - Para Railway/Render
- ✅ `requirements.txt` - Con todas las dependencias
- ✅ `runtime.txt` - Versión de Python
- ✅ `.gitignore` - Archivos a ignorar

### Cambios realizados en `app.py`:
- ✅ Configuración para usar variable de entorno `PORT`
- ✅ Soporte para PostgreSQL (si lo necesitas)
- ✅ Configuración de producción

---

## Pasos Rápidos (Railway - Recomendado)

1. **Instalar Git** (si no lo tienes): https://git-scm.com/downloads

2. **Subir a GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Primera versión"
   git branch -M main
   # Crea un repositorio en GitHub y luego:
   git remote add origin https://github.com/TU_USUARIO/tu-repo.git
   git push -u origin main
   ```

3. **Desplegar en Railway:**
   - Ve a https://railway.app
   - New Project → Deploy from GitHub
   - Selecciona tu repositorio
   - ¡Listo! Tu app estará en línea

---

## Solución de Problemas

### Error: "No module named 'flask'"
- Asegúrate de que `requirements.txt` tenga todas las dependencias
- Verifica que el build se complete correctamente

### Error: "Port already in use"
- En producción, usa la variable de entorno `PORT`
- Ya está configurado en el código

### Base de datos no funciona
- En producción, algunos servicios usan PostgreSQL
- El código ya está preparado para esto

---

## URLs de los Servicios

- **Railway**: https://railway.app
- **Render**: https://render.com
- **PythonAnywhere**: https://www.pythonanywhere.com

---

## ¿Necesitas ayuda?

Si tienes problemas, revisa los logs del servicio que elijas. La mayoría de servicios muestran los logs en tiempo real durante el despliegue.

