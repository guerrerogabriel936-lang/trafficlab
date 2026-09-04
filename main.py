import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuración de rendimiento para alto volumen
# 100,000 ejecuciones por día equivalen a ~1.15 peticiones por segundo sostenidas.
MAX_WORKERS = 20  # Hilos simultáneos en paralelo

def worker_peticion(url):
    """Envía una solicitud con encabezados simulados."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code
    except Exception:
        return None

def ejecutar_campana_masiva(url, total_visitas=100000):
    """Ejecuta las peticiones utilizando un grupo de hilos en paralelo."""
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for _ in range(total_visitas):
            executor.submit(worker_peticion, url)
            time.sleep(0.86)  # Distribución equitativa para alcanzar 100,000 en 24h

@app.route('/api/proyectos', methods=['POST'])
def crear_proyecto():
    data = request.get_json() or {}
    url = data.get('url') or data.get('dominio') or data.get('entry_urls')
    
    if not url:
        return jsonify({"status": "error", "message": "URL requerida"}), 400

    # Iniciar la campaña de alto tráfico en segundo plano
    import threading
    hilo = threading.Thread(target=ejecutar_campana_masiva, args=(url, 100000))
    hilo.daemon = True
    hilo.start()

    return jsonify({
        "status": "success", 
        "message": "Proyecto iniciado correctamente con meta de 100,000 ejecuciones/día."
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
