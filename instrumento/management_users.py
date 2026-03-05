
# instrumento/management_users.py

from django.http import HttpResponse
from instrumento.models import Cliente

def create_superuser(request):
    try:
        # Verifica se já existe um superusuário
        if not Cliente.objects.filter(is_superuser=True).exists():
            # Chama o método create_superuser da sua classe UsuarioManager
            Cliente.objects.create_superuser(
                email='bragasan34@gmail.com',
                password='101219',
                nome_completo='Francisco Santana',  # Corrigido para nome_completo
                cpf='49322893249'
            )
            return HttpResponse("Superusuário criado com sucesso!")
        else:
            return HttpResponse("Já existe um superusuário!")
    except Exception as e:
        return HttpResponse(f"Erro ao criar superusuário: {e}")




# from django.http import HttpResponse
# from django.core.management import call_command
# from instrumento.models import Cliente

# def create_superuser(request):
#     try:
#         # Verifica se já existe um superusuário
#         if not Cliente.objects.filter(is_superuser=True).exists():
#             # Chama o método create_superuser da sua classe UsuarioManager
#             Cliente.objects.create_superuser(
#                 email='bragasan34@gmail.com', 
#                 password='101219', 
#                 nome='Francisco Santana',  # Aqui você pode colocar o nome do superusuário
#                 cpf='49322893249'  # Coloque o CPF do superusuário
#             )
#             return HttpResponse("Superusuário criado com sucesso!")
#         else:
#             return HttpResponse("Já existe um superusuário!")
#     except Exception as e:
#         return HttpResponse(f"Erro ao criar superusuário: {e}")