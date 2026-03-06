import os

from django.core.management import BaseCommand, call_command

from instrumento.models import Instrumento


def env_bool(key, default=False):
    return os.environ.get(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Command(BaseCommand):
    help = "Popula o catalogo demo automaticamente quando o banco estiver vazio."

    def handle(self, *args, **options):
        if not env_bool("AUTO_SEED_DEMO", True):
            self.stdout.write("AUTO_SEED_DEMO desabilitado. Nenhuma carga automatica executada.")
            return

        if Instrumento.objects.exists():
            self.stdout.write("Catalogo ja possui instrumentos. Seed demo ignorado.")
            return

        self.stdout.write("Banco vazio detectado. Executando carga demo automatica...")
        call_command("seed_instrumentos", total=24, **{"imagens_por_item": 2})
        self.stdout.write(self.style.SUCCESS("Carga demo automatica concluida."))
