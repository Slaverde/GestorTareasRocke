# Solución al Error del Puerto

## Problema
Error: `'$PORT' is not a valid port number`

## Solución Aplicada

He actualizado los archivos para manejar correctamente la variable de entorno PORT:

1. **Procfile**: Usa `${PORT:-5000}` (valor por defecto si no existe)
2. **start.sh**: Lee la variable PORT correctamente
3. **railway.json**: Actualizado con el formato correcto
4. **Dockerfile**: Usa la variable PORT dinámicamente

## Pasos para Aplicar la Corrección

1. **Sube los cambios a GitHub:**
   ```bash
   git add .
   git commit -m "Fix PORT variable"
   git push
   ```

2. **En Railway/Render:**
   - El servicio debería redeployarse automáticamente
   - O puedes hacer un "Redeploy" manual

## Si el Error Persiste

### Opción 1: Configuración Manual en Railway
1. Ve a Settings → Deploy
2. En "Start Command", usa:
   ```
   gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
   ```

### Opción 2: Usar Variable de Entorno
1. Ve a Settings → Variables
2. Asegúrate de que existe la variable `PORT`
3. Si no existe, Railway la asigna automáticamente

### Opción 3: Script Alternativo
Si nada funciona, crea un archivo `run.sh`:
```bash
#!/bin/bash
export PORT=${PORT:-5000}
gunicorn --bind 0.0.0.0:$PORT app:app
```

Y en el Procfile:
```
web: bash run.sh
```

