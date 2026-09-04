```python
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

MAX_OPERACIONES = 100_000
MAX_CONCURRENCIA = 20

estado = {
    "ejecutando": False,
    "total": 0,
    "completadas": 0,
    "exitosas": 0,
    "fallidas": 0,
    "inicio": None,
    "fin": None,
    "duracion": 0,
}

lock = threading.Lock()


# ============================================================
# PÁGINA WEB
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>TRAFFICLAB</title>

    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
        }

        .contenedor {
            max-width: 700px;
            margin: auto;
        }

        h1 {
            text-align: center;
            font-size: 36px;
        }

        .tarjeta {
            background: #1d1d1d;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 0 20px rgba(0,0,0,.25);
        }

        input {
            width: 100%;
            box-sizing: border-box;
            padding: 14px;
            margin-top: 8px;
            margin-bottom: 15px;
            border-radius: 10px;
            border: 1px solid #555;
            background: #222;
            color: white;
            font-size: 16px;
        }

        button {
            width: 100%;
            padding: 15px;
            border: 0;
            border-radius: 10px;
            background: #fff;
            color: #111;
            font-size: 17px;
            font-weight: bold;
            cursor: pointer;
        }

        button:disabled {
            opacity: .5;
        }

        .barra {
            width: 100%;
            height: 25px;
            background: #333;
            border-radius: 20px;
            overflow: hidden;
            margin-top: 15px;
        }

        .progreso {
            height: 100%;
            width: 0%;
            background: #fff;
            transition: width .2s;
        }

        .numero {
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            margin-top: 15px;
        }

        .resultado {
            line-height: 1.8;
            font-size: 17px;
        }

        .estado {
            text-align: center;
            margin-top: 15px;
            font-weight: bold;
        }
    </style>
</head>

<body>

<div class="contenedor">

    <h1>TRAFFICLAB</h1>

    <div class="tarjeta">

        <h2>Prueba de carga</h2>

        <label>
            Número de operaciones
        </label>

        <input
            id="cantidad"
            type="number"
            min="1"
            max="100000"
            value="100000"
        >

        <label>
            Concurrencia máxima
        </label>

        <input
            id="concurrencia"
            type="number"
            min="1"
            max="20"
            value="20"
        >

        <button id="boton" onclick="iniciar()">
            INICIAR PRUEBA
        </button>

        <div class="estado" id="estado">
            Esperando prueba...
        </div>

        <div class="barra">
            <div class="progreso" id="progreso"></div>
        </div>

        <div class="numero" id="porcentaje">
            0%
        </div>

    </div>


    <div class="tarjeta">

        <h2>Resultados</h2>

        <div class="resultado">

            Total:
            <strong id="total">0</strong>
            <br>

            Completadas:
            <strong id="completadas">0</strong>
            <br>

            Exitosas:
            <strong id="exitosas">0</strong>
            <br>

            Fallidas:
            <strong id="fallidas">0</strong>
            <br>

            Duración:
            <strong id="duracion">0</strong> segundos
            <br>

            Operaciones/segundo:
            <strong id="ops">0</strong>

        </div>

    </div>

</div>


<script>

let timer = null;

async function iniciar() {

    const cantidad =
        parseInt(document.getElementById("cantidad").value);

    const concurrencia =
        parseInt(document.getElementById("concurrencia").value);

    if (!cantidad || cantidad < 1 || cantidad > 100000) {
        alert("La cantidad debe estar entre 1 y 100000.");
        return;
    }

    if (!concurrencia || concurrencia < 1 || concurrencia > 20) {
        alert("La concurrencia debe estar entre 1 y 20.");
        return;
    }

    const boton = document.getElementById("boton");

    boton.disabled = true;

    document.getElementById("estado").innerText =
        "Ejecutando prueba...";

    try {

        const respuesta = await fetch("/api/iniciar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                cantidad: cantidad,
                concurrencia: concurrencia
            })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            alert(datos.error || "No se pudo iniciar.");
            boton.disabled = false;
            return;
        }

        actualizar();

    } catch (error) {

        alert("Error de conexión.");

        boton.disabled = false;
    }
}


async function actualizar() {

    try {

        const respuesta =
            await fetch("/api/estado");

        const datos =
            await respuesta.json();

        document.getElementById("total").innerText =
            datos.total;

        document.getElementById("completadas").innerText =
            datos.completadas;

        document.getElementById("exitosas").innerText =
            datos.exitosas;

        document.getElementById("fallidas").innerText =
            datos.fallidas;

        document.getElementById("duracion").innerText =
            datos.duracion;

        document.getElementById("ops").innerText =
            datos.ops;

        let porcentaje = 0;

        if (datos.total > 0) {
            porcentaje =
                Math.floor(
                    (datos.completadas / datos.total) * 100
                );
        }

        document.getElementById("progreso").style.width =
            porcentaje + "%";

        document.getElementById("porcentaje").innerText =
            porcentaje + "%";

        if (datos.ejecutando) {

            document.getElementById("estado").innerText =
                "Prueba en ejecución...";

            timer = setTimeout(actualizar, 500);

        } else {

            document.getElementById("estado").innerText =
                "Prueba terminada.";

            document.getElementById("boton").disabled =
                false;
        }

    } catch (error) {

        timer = setTimeout(actualizar, 1000);
    }
}

</script>

</body>
</html>
"""


# ============================================================
# OPERACIÓN DE PRUEBA
# ============================================================

def realizar_operacion(numero):
    """
    Operación interna de prueba.

    No genera vistas, no visita YouTube
    y no envía tráfico a servicios externos.
    """

    try:

        # Simulación muy pequeña de trabajo.
        resultado = (numero * 7) % 97

        if resultado >= 0:
            return True

        return False

    except Exception:
        return False


# ============================================================
# EJECUTOR DE PRUEBA
# ============================================================

def ejecutar_prueba(cantidad, concurrencia):

    global estado

    inicio = time.time()

    with lock:

        estado["ejecutando"] = True
        estado["total"] = cantidad
        estado["completadas"] = 0
        estado["exitosas"] = 0
        estado["fallidas"] = 0
        estado["inicio"] = inicio
        estado["fin"] = None
        estado["duracion"] = 0

    try:

        with ThreadPoolExecutor(
            max_workers=concurrencia
        ) as executor:

            trabajos = [
                executor.submit(
                    realizar_operacion,
                    numero
                )
                for numero in range(cantidad)
            ]

            for futuro in as_completed(trabajos):

                try:

                    resultado = futuro.result()

                    with lock:

                        estado["completadas"] += 1

                        if resultado:
                            estado["exitosas"] += 1
                        else:
                            estado["fallidas"] += 1

                except Exception:

                    with lock:
                        estado["completadas"] += 1
                        estado["fallidas"] += 1

    finally:

        fin = time.time()

        with lock:

            estado["ejecutando"] = False
            estado["fin"] = fin
            estado["duracion"] = round(
                fin - inicio,
                2
            )


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@app.route("/")
def inicio():

    return render_template_string(HTML)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "servicio": "TRAFFICLAB"
    })


# ============================================================
# INICIAR PRUEBA
# ============================================================

@app.route("/api/iniciar", methods=["POST"])
def iniciar_prueba():

    with lock:

        if estado["ejecutando"]:

            return jsonify({
                "error": "Ya existe una prueba ejecutándose."
            }), 409

    datos = request.get_json(silent=True) or {}

    try:

        cantidad = int(
            datos.get(
                "cantidad",
                MAX_OPERACIONES
            )
        )

        concurrencia = int(
            datos.get(
                "concurrencia",
                MAX_CONCURRENCIA
            )
        )

    except (ValueError, TypeError):

        return jsonify({
            "error": "Valores inválidos."
        }), 400

    if cantidad < 1 or cantidad > MAX_OPERACIONES:

        return jsonify({
            "error":
            f"La cantidad máxima es {MAX_OPERACIONES}."
        }), 400

    if concurrencia < 1 or concurrencia > MAX_CONCURRENCIA:

        return jsonify({
            "error":
            f"La concurrencia máxima es {MAX_CONCURRENCIA}."
        }), 400

    hilo = threading.Thread(
        target=ejecutar_prueba,
        args=(cantidad, concurrencia),
        daemon=True
    )

    hilo.start()

    return jsonify({
        "ok": True,
        "mensaje": "Prueba iniciada.",
        "cantidad": cantidad,
        "concurrencia": concurrencia
    })


# ============================================================
# ESTADO
# ============================================================

@app.route("/api/estado")
def obtener_estado():

    with lock:

        datos = dict(estado)

    duracion = datos["duracion"]

    if datos["ejecutando"] and datos["inicio"]:

        duracion = time.time() - datos["inicio"]

    duracion = round(duracion, 2)

    if duracion > 0:

        ops = round(
            datos["completadas"] / duracion,
            2
        )

    else:

        ops = 0

    datos["duracion"] = duracion
    datos["ops"] = ops

    return jsonify(datos)


# ============================================================
# INFORMACIÓN
# ============================================================

@app.route("/api/info")
def info():

    return jsonify({
        "nombre": "TRAFFICLAB",
        "version": "1.0",
        "tipo": "Prueba de carga interna",
        "max_operaciones": MAX_OPERACIONES,
        "max_concurrencia": MAX_CONCURRENCIA,
        "estado": estado["ejecutando"]
    })


# ============================================================
# ARRANQUE
# ============================================================

if __name__ == "__main__":

    puerto = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=puerto,
        threaded=True
    )
```
