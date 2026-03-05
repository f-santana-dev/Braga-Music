from django.http import HttpResponse
from django.core.management import call_command

def run_migrations(request):
    try:
        call_command('migrate')
        return HttpResponse("Migrações executadas com sucesso!")
    except Exception as e:
        return HttpResponse(f"Erro ao executar migrações: {str(e)}")