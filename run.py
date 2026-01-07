#!/usr/bin/env python3
import os
import subprocess
import sys

# Obtener el puerto de la variable de entorno, usar 5000 por defecto
port = os.environ.get('PORT', '5000')

# Ejecutar gunicorn
cmd = ['gunicorn', '--bind', f'0.0.0.0:{port}', 'app:app']
sys.exit(subprocess.call(cmd))

