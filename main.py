import os
import threading
import time
from urllib.parse import urlparse

from flask import Flask, jsonify, request, render_template_string

from locust.env import Environment
from locust.stats import stats_history
from locustfile import TrafficLabUser


app = Flask(__name__)

PORT = int(os.environ.get("PORT", 8080))

# ============================================================
# CONFIGURACIÓN
# ============================================================

configuracion = {
    "titulo": "",
    "dominio": "",
    "fuente": "Directo",
    "palabras_clave": [],
    "sesiones_dia": 100,
    "rebote": 20,
    "aumento_automatico": False,
    "aumento_semanal": 10,
    "movil": 60,
    "escritorio": 30,
    "tablet": 10,
    "paises": [],
    "tiempo_pagina": 120,
    "paginas_sesion": 3,
    "urls_entrada": [],
    "recorrido_automatico": True,
    "programacion_inteligente": True,
    "autorizado": False
}

# ============================================================
# ESTADO DEL MOTOR DE PRUEBAS
# ============================================================

motor = {
    "environment": None,
    "runner": None,
    "activo": False,
    "inicio": None,
    "error": None,
    "objetivo": "",
    "usuarios": 0
}

motor_lock = threading.Lock()


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validar_dominio(url):
    """
    Comprueba que exista una URL HTTP/HTTPS válida.
    """

    if not url:
        return None

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return None

        if not parsed.netloc:
            return None

        return url.rstrip("/")

    except Exception:
        return None


def ejecutar_prueba(host, usuarios, velocidad):
    """
    Ejecuta Locust en segundo plano.
    Solo debe utilizarse contra sitios propios o autorizados.
    """

    global motor

    try:

        environment = Environment(
            user_classes=[TrafficLabUser],
            host=host
        )

        runner = environment.create_local_runner()

        with motor_lock:
            motor["environment"] = environment
            motor["runner"] = runner
            motor["activo"] = True
            motor["inicio"] = time.time()
            motor["error"] = None
            motor["objetivo"] = host
            motor["usuarios"] = usuarios

        # Iniciar usuarios
        runner.start(
            user_count=usuarios,
            spawn_rate=velocidad
        )

        # Mantener el motor funcionando
        while True:

            with motor_lock:
                activo = motor["activo"]

            if not activo:
                break

            if runner.state == "stopped":
                break

            time.sleep(1)

    except Exception as error:

        with motor_lock:
            motor["error"] = str(error)

    finally:

        try:
            if runner:
                runner.quit()
        except Exception:
            pass

        with motor_lock:
            motor["activo"] = False
            motor["runner"] = None
            motor["environment"] = None


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>TrafficLab</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #080611;
    color: #ffffff;
    font-family: Arial, Helvetica, sans-serif;
}

.header {
    padding: 20px;
    border-bottom: 1px solid #29213b;
    background: #0d0a18;
}

.logo {
    font-size: 24px;
    font-weight: bold;
}

.logo span {
    color: #914cff;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}

.title {
    margin-bottom: 25px;
}

.title h1 {
    margin: 0;
    font-size: 28px;
}

.title p {
    color: #9992aa;
}

.section {
    background: #151120;
    border: 1px solid #2b2340;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 18px;
}

.section h2 {
    margin-top: 0;
    font-size: 19px;
}

.section-description {
    color: #9992aa;
    font-size: 14px;
    margin-bottom: 20px;
}

.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
}

.field {
    margin-bottom: 15px;
}

.field label {
    display: block;
    color: #bcb5ca;
    font-size: 13px;
    margin-bottom: 7px;
}

input,
select,
textarea {
    width: 100%;
    background: #211a31;
    border: 1px solid #3a304d;
    border-radius: 9px;
    color: white;
    padding: 12px;
    outline: none;
}

input:focus,
select:focus,
textarea:focus {
    border-color: #914cff;
}

textarea {
    min-height: 100px;
    resize: vertical;
}

.range-container {
    background: #211a31;
    padding: 15px;
    border-radius: 10px;
}

input[type="range"] {
    padding: 0;
    accent-color: #914cff;
}

.range-value {
    font-size: 22px;
    font-weight: bold;
    color: #a86aff;
    margin-bottom: 8px;
}

.devices {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.device {
    background: #211a31;
    border: 1px solid #3a304d;
    padding: 15px;
    border-radius: 10px;
}

.device strong {
    display: block;
    margin-bottom: 8px;
}

.switch-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #211a31;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 10px;
}

.switch {
    position: relative;
    width: 48px;
    height: 26px;
}

.switch input {
    display: none;
}

.slider-switch {
    position: absolute;
    inset: 0;
    background: #393246;
    border-radius: 30px;
    cursor: pointer;
}

.slider-switch:before {
    content: "";
    position: absolute;
    width: 20px;
    height: 20px;
    left: 3px;
    top: 3px;
    background: white;
    border-radius: 50%;
    transition: .2s;
}

.switch input:checked + .slider-switch {
    background: #914cff;
}

.switch input:checked + .slider-switch:before {
    transform: translateX(22px);
}

.info {
    background: #1b1430;
    border: 1px solid #4b327d;
    border-radius: 9px;
    padding: 12px;
    color: #cbb8ec;
    font-size: 13px;
    margin-top: 10px;
}

.button-area {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 20px;
}

button {
    border: none;
    background: #914cff;
    color: white;
    padding: 14px 25px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #7b35df;
}

button.stop {
    background: #a93232;
}

button.stop:hover {
    background: #c83b3b;
}

button:disabled {
    opacity: .5;
    cursor: not-allowed;
}

.result {
    display: none;
    background: #10251b;
    border: 1px solid #28704b;
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
}

.status {
    background: #211a31;
    border: 1px solid #3a304d;
    border-radius: 10px;
    padding: 15px;
    margin-top: 15px;
}

.status-title {
    font-weight: bold;
    margin-bottom: 10px;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.stat {
    background: #151120;
    border-radius: 8px;
    padding: 12px;
}

.stat small {
    display: block;
    color: #9992aa;
    margin-bottom: 5px;
}

.stat strong {
    font-size: 20px;
}

.running {
    color: #55df91;
}

.stopped {
    color: #ff8c8c;
}

@media(max-width:700px) {

    .grid {
        grid-template-columns: 1fr;
    }

    .devices {
        grid-template-columns: 1fr;
    }

    .status-grid {
        grid-template-columns: 1fr 1fr;
    }

    .container {
        padding: 12px;
    }

    .section {
        padding: 15px;
    }

    .button-area {
        flex-direction: column;
    }

    .button-area button {
        width: 100%;
    }
}

</style>

</head>

<body>

<div class="header">

    <div class="logo">
        <span>◆</span> TRAFFICLAB
    </div>

</div>

<div class="container">

<div class="title">

    <h1>Crear proyecto</h1>

    <p>
        Configura una prueba de tráfico autorizada para tu sitio web.
    </p>

</div>


<!-- ======================================================
     GENERAL
====================================================== -->

<div class="section">

<h2>1. General</h2>

<div class="section-description">
Configuración básica del proyecto y destino de la prueba.
</div>

<div class="grid">

<div class="field">

<label>Título del proyecto</label>

<input
    id="titulo"
    type="text"
    placeholder="Mi proyecto"
>

</div>


<div class="field">

<label>Dominio autorizado</label>

<input
    id="dominio"
    type="url"
    placeholder="https://misitio.com"
>

</div>

</div>


<div class="field">

<label>Fuente de tráfico de prueba</label>

<select id="fuente">

<option value="Directo">Directo</option>
<option value="Orgánico">Orgánico</option>
<option value="Referido">Referido</option>
<option value="Social">Social</option>

</select>

</div>


<div class="field">

<label>Palabras clave</label>

<textarea
    id="palabras"
    placeholder="Una palabra clave por línea"
></textarea>

</div>


<div class="info">

Estas sesiones son pruebas automatizadas.
No representan visitantes humanos reales ni sirven para fabricar
métricas de plataformas externas.

</div>

</div>


<!-- ======================================================
     AUDIENCIA
====================================================== -->

<div class="section">

<h2>2. Audiencia</h2>

<div class="section-description">
Configura el volumen de usuarios de prueba.
</div>


<div class="grid">

<div class="field">

<label>Usuarios simultáneos</label>

<input
    id="sesiones"
    type="number"
    value="5"
    min="1"
    max="100"
>

</div>


<div class="field">

<label>Tasa de rebote</label>

<div class="range-container">

<div class="range-value">
<span id="reboteValor">20</span>%
</div>

<input
    id="rebote"
    type="range"
    min="0"
    max="100"
    value="20"
    oninput="actualizarRebote()"
>

</div>

</div>

</div>


<div class="switch-row">

<div>

<strong>Aumentar automáticamente el tráfico</strong>

<div class="section-description">
Aumenta gradualmente el volumen de pruebas.
</div>

</div>

<label class="switch">

<input
    id="aumento"
    type="checkbox"
>

<span class="slider-switch"></span>

</label>

</div>


<div class="field">

<label>Aumento semanal</label>

<select id="aumentoSemanal">

<option value="10">10%</option>
<option value="25">25%</option>
<option value="50">50%</option>
<option value="100">100%</option>

</select>

</div>


<h3>Dispositivos</h3>

<div class="devices">

<div class="device">

<strong>📱 Móvil</strong>

<input
    id="movil"
    type="number"
    value="60"
    min="0"
    max="100"
>

</div>


<div class="device">

<strong>💻 Escritorio</strong>

<input
    id="escritorio"
    type="number"
    value="30"
    min="0"
    max="100"
>

</div>


<div class="device">

<strong>📱 Tablet</strong>

<input
    id="tablet"
    type="number"
    value="10"
    min="0"
    max="100"
>

</div>

</div>


<div class="info">

La distribución de dispositivos debe sumar exactamente 100%.

</div>

</div>


<!-- ======================================================
     RECORRIDO
====================================================== -->

<div class="section">

<h2>3. Recorrido del usuario</h2>

<div class="section-description">
Configura las páginas que deben utilizarse durante la prueba.
</div>


<div class="grid">

<div class="field">

<label>Tiempo promedio en página</label>

<select id="tiempo">

<option value="10">10 segundos</option>
<option value="30">30 segundos</option>
<option value="60">60 segundos</option>
<option value="120" selected>120 segundos</option>
<option value="300">300 segundos</option>

</select>

</div>


<div class="field">

<label>Páginas por sesión</label>

<input
    id="paginas"
    type="number"
    value="3"
    min="1"
    max="20"
>

</div>

</div>


<div class="field">

<label>URLs de entrada</label>

<textarea
    id="urls"
    placeholder="Una URL por línea
https://misitio.com/
https://misitio.com/blog
https://misitio.com/productos"
></textarea>

</div>


<div class="switch-row">

<div>

<strong>Recorrido automático</strong>

<div class="section-description">
Permite utilizar las páginas configuradas.
</div>

</div>

<label class="switch">

<input
    id="recorrido"
    type="checkbox"
    checked
>

<span class="slider-switch"></span>

</label>

</div>


<div class="switch-row">

<div>

<strong>Programación inteligente</strong>

<div class="section-description">
Distribuye las pruebas en el tiempo.
</div>

</div>

<label class="switch">

<input
    id="programacion"
    type="checkbox"
    checked
>

<span class="slider-switch"></span>

</label>

</div>


<div class="switch-row">

<div>

<strong>Autorización</strong>

<div class="section-description">
Confirmo que tengo autorización para realizar pruebas sobre este sitio.
</div>

</div>

<label class="switch">

<input
    id="autorizado"
    type="checkbox"
>

<span class="slider-switch"></span>

</label>

</div>


<div class="button-area">

<button onclick="crearProyecto()">
Guardar proyecto
</button>

<button onclick="iniciarPrueba()">
▶ Iniciar prueba
</button>

<button
    id="detener"
    class="stop"
    onclick="detenerPrueba()"
    disabled
>
■ Detener
</button>

</div>


<div
    id="resultado"
    class="result"
></div>


<div class="status">

<div class="status-title">
Estado de TrafficLab
</div>

<div class="status-grid">

<div class="stat">

<small>Estado</small>

<strong id="estado">
Detenido
</strong>

</div>


<div class="stat">

<small>Usuarios</small>

<strong id="usuarios">
0
</strong>

</div>


<div class="stat">

<small>Peticiones</small>

<strong id="peticiones">
0
</strong>

</div>


<div class="stat">

<small>Errores</small>

<strong id="errores">
0
</strong>

</div>

</div>

</div>

</div>

</div>


<script>

function actualizarRebote() {

    const valor =
        document.getElementById("rebote").value;

    document.getElementById("reboteValor").textContent =
        valor;

}


function obtenerDatos() {

    const movil =
        Number(document.getElementById("movil").value);

    const escritorio =
        Number(document.getElementById("escritorio").value);

    const tablet =
        Number(document.getElementById("tablet").value);

    const total =
        movil + escritorio + tablet;


    if (total !== 100) {

        alert(
            "Los porcentajes de dispositivos deben sumar 100%."
        );

        return null;

    }


    const autorizado =
        document.getElementById("autorizado").checked;


    if (!autorizado) {

        alert(
            "Debes confirmar que tienes autorización para realizar la prueba."
        );

        return null;

    }


    return {

        titulo:
            document.getElementById("titulo").value,

        dominio:
            document.getElementById("dominio").value,

        fuente:
            document.getElementById("fuente").value,

        palabras_clave:
            document.getElementById("palabras").value
                .split("\\n")
                .map(x => x.trim())
                .filter(Boolean),

        sesiones_dia:
            Number(
                document.getElementById("sesiones").value
            ),

        rebote:
            Number(
                document.getElementById("rebote").value
            ),

        aumento_automatico:
            document.getElementById("aumento").checked,

        aumento_semanal:
            Number(
                document.getElementById("aumentoSemanal").value
            ),

        movil,
        escritorio,
        tablet,

        tiempo_pagina:
            Number(
                document.getElementById("tiempo").value
            ),

        paginas_sesion:
            Number(
                document.getElementById("paginas").value
            ),

        urls_entrada:
            document.getElementById("urls").value
                .split("\\n")
                .map(x => x.trim())
                .filter(Boolean),

        recorrido_automatico:
            document.getElementById("recorrido").checked,

        programacion_inteligente:
            document.getElementById("programacion").checked,

        autorizado: true

    };

}


async function crearProyecto() {

    const datos = obtenerDatos();

    if (!datos) {
        return;
    }


    try {

        const respuesta =
            await fetch("/api/project", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body:
                    JSON.stringify(datos)

            });


        const resultado =
            await respuesta.json();


        mostrarResultado(
            resultado.status === "success",
            resultado.message
        );

    }

    catch(error) {

        mostrarResultado(
            false,
            "Error de conexión con el servidor."
        );

    }

}


async function iniciarPrueba() {

    const datos = obtenerDatos();

    if (!datos) {
        return;
    }


    try {

        const guardar =
            await fetch("/api/project", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body:
                    JSON.stringify(datos)

            });


        const resultadoGuardar =
            await guardar.json();


        if (resultadoGuardar.status !== "success") {

            mostrarResultado(
                false,
                resultadoGuardar.message
            );

            return;

        }


        const respuesta =
            await fetch("/api/test/start", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    usuarios:
                        Number(
                            document.getElementById("sesiones").value
                        ),

                    velocidad: 1

                })

            });


        const resultado =
            await respuesta.json();


        mostrarResultado(
            resultado.status === "success",
            resultado.message
        );


        actualizarEstado();

    }

    catch(error) {

        mostrarResultado(
            false,
            "No se pudo iniciar la prueba."
        );

    }

}


async function detenerPrueba() {

    try {

        const respuesta =
            await fetch("/api/test/stop", {

                method: "POST"

            });


        const resultado =
            await respuesta.json();


        mostrarResultado(
            resultado.status === "success",
            resultado.message
        );


        actualizarEstado();

    }

    catch(error) {

        mostrarResultado(
            false,
            "No se pudo detener la prueba."
        );

    }

}


async function actualizarEstado() {

    try {

        const respuesta =
            await fetch("/api/test/status");


        const datos =
            await respuesta.json();


        const estado =
            document.getElementById("estado");

        const usuarios =
            document.getElementById("usuarios");

        const peticiones =
            document.getElementById("peticiones");

        const errores =
            document.getElementById("errores");

        const detener =
            document.getElementById("detener");


        if (datos.activo) {

            estado.textContent = "Ejecutando";

            estado.className = "running";

            detener.disabled = false;

        } else {

            estado.textContent = "Detenido";

            estado.className = "stopped";

            detener.disabled = true;

        }


        usuarios.textContent =
            datos.usuarios || 0;


        peticiones.textContent =
            datos.peticiones || 0;


        errores.textContent =
            datos.errores || 0;

    }

    catch(error) {

        console.log(error);

    }

}


function mostrarResultado(exito, mensaje) {

    const caja =
        document.getElementById("resultado");


    caja.style.display = "block";


    if (exito) {

        caja.innerHTML =
            "✅ " + (mensaje || "Operación realizada correctamente.");

    } else {

        caja.innerHTML =
            "❌ " + (mensaje || "Ocurrió un error.");

    }

}


setInterval(
    actualizarEstado,
    2000
);


actualizarEstado();

</script>

</body>

</html>
"""


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return render_template_string(HTML)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health_check():

    return jsonify({
        "status": "healthy"
    })


# ============================================================
# CREAR / GUARDAR PROYECTO
# ============================================================

@app.route("/api/project", methods=["POST"])
def create_project():

    global configuracion

    data = request.get_json() or {}

    dominio = validar_dominio(
        data.get("dominio", "")
    )

    if not dominio:

        return jsonify({
            "status": "error",
            "message": "El dominio no es válido."
        }), 400


    if not data.get("autorizado"):

        return jsonify({
            "status": "error",
            "message": "Debes confirmar la autorización."
        }), 400


    data["dominio"] = dominio

    configuracion.update(data)


    return jsonify({

        "status": "success",

        "message":
            "Proyecto guardado correctamente.",

        "project":
            configuracion

    }), 200


# ============================================================
# OBTENER PROYECTO
# ============================================================

@app.route("/api/project", methods=["GET"])
def get_project():

    return jsonify({

        "status": "success",

        "project":
            configuracion

    }), 200


# ============================================================
# INICIAR LOCUST
# ============================================================

@app.route("/api/test/start", methods=["POST"])
def start_test():

    global motor

    data = request.get_json() or {}

    with motor_lock:

        if motor["activo"]:

            return jsonify({

                "status": "error",

                "message":
                    "Ya existe una prueba ejecutándose."

            }), 400


    if not configuracion.get("autorizado"):

        return jsonify({

            "status": "error",

            "message":
                "Debes confirmar la autorización."

        }), 403


    host = validar_dominio(
        configuracion.get("dominio", "")
    )


    if not host:

        return jsonify({

            "status": "error",

            "message":
                "Configura primero un dominio válido."

        }), 400


    usuarios = int(
        data.get(
            "usuarios",
            configuracion.get("sesiones_dia", 5)
        )
    )


    velocidad = int(
        data.get(
            "velocidad",
            1
        )
    )


    # Límite prudente para esta versión gratuita.
    usuarios = max(1, min(usuarios, 100))

    velocidad = max(1, min(velocidad, usuarios))


    hilo = threading.Thread(

        target=ejecutar_prueba,

        args=(
            host,
            usuarios,
            velocidad
        ),

        daemon=True

    )

    hilo.start()


    return jsonify({

        "status": "success",

        "message":
            "Prueba iniciada correctamente.",

        "objetivo":
            host,

        "usuarios":
            usuarios

    }), 200


# ============================================================
# DETENER PRUEBA
# ============================================================

@app.route("/api/test/stop", methods=["POST"])
def stop_test():

    with motor_lock:

        runner = motor.get("runner")

        activo = motor.get("activo")


    if not activo or runner is None:

        return jsonify({

            "status": "error",

            "message":
                "No hay ninguna prueba ejecutándose."

        }), 400


    try:

        runner.quit()

    except Exception:
        pass


    with motor_lock:

        motor["activo"] = False


    return jsonify({

        "status": "success",

        "message":
            "Prueba detenida."

    }), 200


# ============================================================
# ESTADO DE LA PRUEBA
# ============================================================

@app.route("/api/test/status", methods=["GET"])
def test_status():

    with motor_lock:

        environment = motor.get("environment")

        activo = motor.get("activo")

        objetivo = motor.get("objetivo")

        inicio = motor.get("inicio")

        error = motor.get("error")


    peticiones = 0
    errores = 0
    usuarios = 0


    if environment is not None:

        try:

            total = environment.stats.total

            peticiones = total.num_requests

            errores = total.num_failures

            usuarios = (
                environment.runner.user_count
                if environment.runner
                else 0
            )

        except Exception:
            pass


    return jsonify({

        "status": "success",

        "activo": activo,

        "objetivo": objetivo,

        "inicio": inicio,

        "usuarios": usuarios,

        "peticiones": peticiones,

        "errores": errores,

        "error": error

    }), 200


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=PORT

    )
