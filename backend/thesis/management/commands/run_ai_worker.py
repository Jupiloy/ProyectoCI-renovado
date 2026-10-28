"""Trabajador acotado para procesar concurrentemente la cola de generación IA."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections, connection

from thesis.services.ai_jobs import fail_interrupted_ai_jobs, run_next_ai_job


AI_WORKER_LOCK_ID = 7721503202


class Command(BaseCommand):
    help = "Procesa generación IA y síntesis de lotes con concurrencia limitada y reclamos atómicos"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Procesa a lo sumo un trabajo y termina")
        parser.add_argument("--poll-interval", type=float, default=2.0)
        parser.add_argument(
            "--concurrency",
            type=int,
            default=1,
            help="Máximo de llamadas IA simultáneas en este worker (predeterminado: 1)",
        )

    def handle(self, *args, **options):
        poll_interval = options["poll_interval"]
        concurrency = options["concurrency"]
        maximum = getattr(settings, "TESISMCP_AI_WORKER_MAX_CONCURRENCY", 4)
        if poll_interval <= 0:
            raise CommandError("--poll-interval debe ser positivo")
        if maximum < 1:
            raise CommandError("TESISMCP_AI_WORKER_MAX_CONCURRENCY debe ser al menos 1")
        if concurrency < 1 or concurrency > maximum:
            raise CommandError(f"--concurrency debe estar entre 1 y {maximum}")
        if options["once"] and concurrency != 1:
            raise CommandError("--once admite solo --concurrency 1 para conservar el límite de un job")

        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [AI_WORKER_LOCK_ID])
            acquired = cursor.fetchone()[0]
        if not acquired:
            raise CommandError("Ya existe un trabajador de IA activo")

        try:
            # El advisory lock garantiza que ningún proceso worker anterior siga activo.
            # Un job RUNNING que quedó en BD es ambiguo y se falla, nunca se reintenta solo.
            interrupted_count = fail_interrupted_ai_jobs()
            if interrupted_count:
                self.stdout.write(f"Jobs interrumpidos marcados FAILED: {interrupted_count}")

            if options["once"]:
                run_next_ai_job()
                return

            self.stdout.write(f"Trabajador IA iniciado con concurrencia máxima {concurrency}")
            stop_event = threading.Event()

            def consume_queue():
                close_old_connections()
                try:
                    while not stop_event.is_set():
                        close_old_connections()
                        try:
                            worked = run_next_ai_job()
                        finally:
                            close_old_connections()
                        if not worked:
                            stop_event.wait(poll_interval)
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="tesismcp-ai") as pool:
                futures = [pool.submit(consume_queue) for _ in range(concurrency)]
                try:
                    while not stop_event.is_set():
                        time.sleep(0.25)
                        for future in futures:
                            if future.done():
                                stop_event.set()
                                error = future.exception()
                                if error:
                                    raise error
                                raise RuntimeError("Un consumidor de la cola IA terminó inesperadamente")
                except KeyboardInterrupt:
                    self.stdout.write("Deteniendo trabajadores IA; se espera a que terminen los jobs en curso")
                finally:
                    stop_event.set()
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [AI_WORKER_LOCK_ID])
            close_old_connections()
