import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# --- Configuración y Estado Global ---
PORT = int(os.environ.get("PORT", 8080))

# --- Rutas de la Aplicación ---
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "success",
        "message": "Servidor activo y ejecutando correctamente."
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# --- Punto de entrada principal ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
