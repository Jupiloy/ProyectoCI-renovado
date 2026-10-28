"""Ejecuta una sola operación documental pesada a la vez."""

import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from thesis.services.document_jobs import recover_interrupted_jobs, run_next_document_job


WORKER_LOCK_ID = 7721503201


class Command(BaseCommand):
    help = "Procesa la cola PostgreSQL de GROBID e indexación en un proceso separado"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Procesa a lo sumo un trabajo y termina")
        parser.add_argument("--poll-interval", type=float, default=2.0)

    def handle(self, *args, **options):
        if options["poll_interval"] <= 0:
            raise CommandError("--poll-interval debe ser positivo")
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [WORKER_LOCK_ID])
            acquired = cursor.fetchone()[0]
        if not acquired:
            raise CommandError("Ya existe un trabajador documental activo")
        try:
            recover_interrupted_jobs()
            while True:
                worked = run_next_document_job()
                if options["once"]:
                    break
                if not worked:
                    time.sleep(options["poll_interval"])
        except KeyboardInterrupt:
            self.stdout.write("Trabajador detenido")
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [WORKER_LOCK_ID])
