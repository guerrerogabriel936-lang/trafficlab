from locust import HttpUser, task, between
import os


class TrafficLabUser(HttpUser):
    """
    Motor de pruebas de carga para TrafficLab.
    Solo debe utilizarse contra sitios propios o autorizados.
    """

    wait_time = between(2, 5)

    @task
    def prueba_sitio(self):
        ruta = os.environ.get("TEST_PATH", "/")

        with self.client.get(
            ruta,
            name="Prueba autorizada",
            catch_response=True
        ) as respuesta:

            if respuesta.status_code >= 400:
                respuesta.failure(
                    f"HTTP {respuesta.status_code}"
                )
            else:
                respuesta.success()
