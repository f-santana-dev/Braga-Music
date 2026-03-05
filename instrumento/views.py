# instrumento/views.py
import logging
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Instrumento
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .forms import ClienteCadastroForm, LoginForm 
import re
from django.utils.timezone import now
from .models import Instrumento, Marca, Categoria, Cliente,  ImagemInstrumento,Carrinho,ItemPedido,Pedido
import logging
from django.contrib import messages
from django.db.models import Min, Max # Importe os módulos Min e Max para calcular o preço mínimo e máximo do slider

from .utils import calcular_total_itens_carrinho
import mercadopago # Importa o módulo mercadopago para fazer a conexao com a api
from .api_mercadopago import sdk, criar_pagamento  # Importa a função que faz a conexao com a api
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse  # Importe a função reverse()
from django.db.models import Prefetch
from django.utils import timezone  # Importe timezone para usar timezone.now()
from django.conf import settings  # Importa as configurações do Django
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from datetime import datetime


def filtro_instrumentos(request):
    total_itens = calcular_total_itens_carrinho(request)
    # Obtém categorias, marcas e cores distintas no banco de dados
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    cores = Instrumento.objects.values_list('cor', flat=True).distinct()

    contexto = {
        'categorias': categorias,
        'marcas': marcas,
        'cores': cores,
        'total_itens': total_itens,  # Adicione esta linha
    }

    return render(request, 'loja/filtro.html', contexto)

logger = logging.getLogger(__name__)


def login_view(request):
    logger.info("Acessando a view de login.")
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            logger.info(f"Tentativa de login com email: {email}")
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                logger.info(f"Login bem-sucedido para o usuário: {email}")

                # Verificar se o cliente aceitou a política de privacidade
                if isinstance(user, Cliente) and not user.aceitou_politica:
                    request.session['exibir_modal_politica'] = True  # Define a flag na sessão
                    return redirect('exibir_politica') # Redireciona para exibir modal

                # Atualiza o contador de itens após o login
                request.session['total_itens'] = calcular_total_itens_carrinho(request)

                # Mover itens do carrinho da sessão para o banco de dados
                carrinho = request.session.get('carrinho', {})
                logger.info(f"Carrinho na sessão: {carrinho}")
                try:
                    for instrumento_id, item in carrinho.items():
                        instrumento = Instrumento.objects.get(pk=instrumento_id)
                        carrinho_item, created = Carrinho.objects.get_or_create(cliente=user, instrumento=instrumento)
                        if not created:
                            carrinho_item.quantidade += item['quantidade']
                            carrinho_item.save()
                            logger.info(f"Item {instrumento.nome} atualizado no carrinho do banco de dados.")
                        else:
                            logger.info(f"Item {instrumento.nome} adicionado ao carrinho do banco de dados.")
                    # Limpar o carrinho da sessão apenas se a transferência for bem-sucedida
                    if 'carrinho' in request.session:
                        del request.session['carrinho']
                        logger.info("Carrinho da sessão limpo.")
                except Instrumento.DoesNotExist:
                    logger.error("Um instrumento no carrinho da sessão não foi encontrado no banco de dados.")
                    messages.error(request, "Houve um erro ao transferir o carrinho. Alguns itens podem não ter sido adicionados.")
                except Exception as e:
                    logger.error(f"Erro inesperado ao transferir o carrinho: {e}")
                    messages.error(request, "Houve um erro inesperado ao transferir o carrinho.")

                ##mODIFICADO PARA ADICIONAR O TOTAL DE ITENS NO CARRINHO
                request.session['total_itens'] = calcular_total_itens_carrinho(request)
                request.session.modified = True
                logger.info(f"Total itens no carrinho após login: {request.session['total_itens']}")

                return redirect('homepage')
            else:
                messages.error(request, "Credenciais inválidas.")
                logger.warning(f"Falha no login para o usuário: {email}")
                return redirect('login')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
            logger.warning("Formulário de login inválido.")
            return render(request, 'login.html', {'form': form})  # Retorno para requisições POST com formulário inválido
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})  # Retorno para requisições GET



logger = logging.getLogger(__name__)
User = get_user_model()

def verificar_email(request):
    email = request.GET.get('email', None)
    logger.info(f"Verificando email: {email}")
    exists = User.objects.filter(email=email).exists()
    logger.info(f"Email existe: {exists}")
    return JsonResponse({'exists': exists})


@login_required
def exibir_politica(request):
    if request.method == 'POST':
        if 'aceitar_politica' in request.POST:
            request.user.aceitou_politica = True
            request.user.save()
            return redirect('homepage')  # Redireciona após aceitar
        else:
            return redirect('homepage')  # Redireciona se recusar
    return render(request, 'politica_privacidade.html')


def logout_view(request):
    logout(request)
    #messages.success(request, "Logout realizado com sucesso.")
    return redirect('homepage')



User = get_user_model()
def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteCadastroForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.aceitou_politica = request.POST.get('consentimento') == 'on'

            # Gera um username único a partir do email
            base_username = cliente.email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            cliente.username = username

            cliente.save()

            messages.success(request, 'Cadastro realizado com sucesso!')
            login(request, cliente)
            return redirect('login')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ClienteCadastroForm()
    return render(request, 'cadastro_cliente.html', {'form': form})


def formatar_preco_real(preco):
    """Formata um valor para a moeda real do Brasil."""
    return "R$ {:,.2f}".format(preco).replace(",", "X").replace(".", ",").replace("X", ".")















def homepage(request):
    #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    total_itens = calcular_total_itens_carrinho(request)
    instrumentos_lista = Instrumento.objects.prefetch_related('imagens').filter(ativo=True)

    # Filtros
    categoria_id = request.GET.get('categoria')
    marcas_ids = request.GET.getlist('marca')
    cores_selecionadas = request.GET.getlist('cor')
    preco_min = request.GET.get('preco_min')
    preco_max = request.GET.get('preco_max')

    # Aplicar filtros de forma conjunta
    if categoria_id:
        instrumentos_lista = instrumentos_lista.filter(categoria_id=categoria_id)

    if marcas_ids:
        instrumentos_lista = instrumentos_lista.filter(marca_id__in=marcas_ids)

    if cores_selecionadas:
        instrumentos_lista = instrumentos_lista.filter(cor__in=cores_selecionadas)

    if preco_min and preco_max:
        instrumentos_lista = instrumentos_lista.filter(preco__range=(preco_min, preco_max))

    # Paginação
    paginator = Paginator(instrumentos_lista, 12)
    page = request.GET.get('page')
    try:
        instrumentos = paginator.page(page)
    except PageNotAnInteger:
        instrumentos = paginator.page(1)
    except EmptyPage:
        instrumentos = paginator.page(paginator.num_pages)

    # Formatação de preço
    for instrumento in instrumentos:
        instrumento.preco_formatado = formatar_preco_real(instrumento.preco)

    # Dados para filtros
    categorias = Categoria.objects.all()

    # Filtrar dados de filtro por categoria
    if categoria_id:
        cores = Instrumento.objects.filter(categoria_id=categoria_id).values_list('cor', flat=True).distinct()
        marcas = Marca.objects.filter(instrumento__categoria_id=categoria_id).distinct()
        preco_minimo_global = Instrumento.objects.filter(categoria_id=categoria_id).aggregate(Min('preco'))['preco__min'] or 0
        preco_maximo_global = Instrumento.objects.filter(categoria_id=categoria_id).aggregate(Max('preco'))['preco__max'] or 5000
    else:
        cores = Instrumento.objects.values_list('cor', flat=True).distinct()
        marcas = Marca.objects.all()
        preco_minimo_global = Instrumento.objects.aggregate(Min('preco'))['preco__min'] or 0
        preco_maximo_global = Instrumento.objects.aggregate(Max('preco'))['preco__max'] or 5000

    cores_unicas = sorted(set(filter(None, [cor.strip() for cor in cores])))
    precos_categorias = Categoria.objects.annotate(preco_minimo=Min('instrumento__preco'))

    request.session['total_itens'] = total_itens
    request.session.modified = True

    context = {
        'instrumentos': instrumentos,
        'categorias': categorias,
        'marcas': marcas,
        'cores': cores_unicas,
        'preco_minimo_global': preco_minimo_global,
        'preco_maximo_global': preco_maximo_global,
        'precos_categorias': precos_categorias,
        'total_itens': total_itens,
        'categoria_id_selecionada': categoria_id,
        'marcas_ids_selecionadas': marcas_ids,
        'cores_selecionadas': cores_selecionadas,
        'preco_min_selecionado': preco_min,
        'preco_max_selecionado': preco_max,
    }

    return render(request, 'homepage.html', context)










































# def homepage(request):
#     #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
#     total_itens = calcular_total_itens_carrinho(request)
#     instrumentos_lista = Instrumento.objects.prefetch_related('imagens').filter(ativo=True)

#     # Filtros
#     categoria_id = request.GET.get('categoria')
#     marcas_ids = request.GET.getlist('marca')
#     cores_selecionadas = request.GET.getlist('cor')
#     preco_min = request.GET.get('preco_min')
#     preco_max = request.GET.get('preco_max')

#     # Aplicar filtros de forma conjunta
#     if categoria_id:
#         instrumentos_lista = instrumentos_lista.filter(categoria_id=categoria_id)

#     if marcas_ids:
#         instrumentos_lista = instrumentos_lista.filter(marca_id__in=marcas_ids)

#     if cores_selecionadas:
#         instrumentos_lista = instrumentos_lista.filter(cor__in=cores_selecionadas)

#     if preco_min and preco_max:
#         instrumentos_lista = instrumentos_lista.filter(preco__range=(preco_min, preco_max))

#     # Paginação
#     paginator = Paginator(instrumentos_lista, 12)
#     page = request.GET.get('page')
#     try:
#         instrumentos = paginator.page(page)
#     except PageNotAnInteger:
#         instrumentos = paginator.page(1)
#     except EmptyPage:
#         instrumentos = paginator.page(paginator.num_pages)

#     # Formatação de preço
#     for instrumento in instrumentos:
#         instrumento.preco_formatado = locale.currency(instrumento.preco, grouping=True)

#     # Dados para filtros
#     categorias = Categoria.objects.all()

#     # Filtrar dados de filtro por categoria
#     if categoria_id:
#         cores = Instrumento.objects.filter(categoria_id=categoria_id).values_list('cor', flat=True).distinct()
#         marcas = Marca.objects.filter(instrumento__categoria_id=categoria_id).distinct()
#         preco_minimo_global = Instrumento.objects.filter(categoria_id=categoria_id).aggregate(Min('preco'))['preco__min'] or 0
#         preco_maximo_global = Instrumento.objects.filter(categoria_id=categoria_id).aggregate(Max('preco'))['preco__max'] or 5000
#     else:
#         cores = Instrumento.objects.values_list('cor', flat=True).distinct()
#         marcas = Marca.objects.all()
#         preco_minimo_global = Instrumento.objects.aggregate(Min('preco'))['preco__min'] or 0
#         preco_maximo_global = Instrumento.objects.aggregate(Max('preco'))['preco__max'] or 5000

#     cores_unicas = sorted(set(filter(None, [cor.strip() for cor in cores])))
#     precos_categorias = Categoria.objects.annotate(preco_minimo=Min('instrumento__preco'))

#     request.session['total_itens'] = total_itens
#     request.session.modified = True

#     context = {
#         'instrumentos': instrumentos,
#         'categorias': categorias,
#         'marcas': marcas,
#         'cores': cores_unicas,
#         'preco_minimo_global': preco_minimo_global,
#         'preco_maximo_global': preco_maximo_global,
#         'precos_categorias': precos_categorias,
#         'total_itens': total_itens,
#         'categoria_id_selecionada': categoria_id,
#         'marcas_ids_selecionadas': marcas_ids,
#         'cores_selecionadas': cores_selecionadas,
#         'preco_min_selecionado': preco_min,
#         'preco_max_selecionado': preco_max,
#     }

#     return render(request, 'homepage.html', context)


def pre_login(request):
    return render(request, 'pre-login.html')


logger = logging.getLogger(__name__)
def adicionar_ao_carrinho(request, instrumento_id):
    instrumento = get_object_or_404(Instrumento, pk=instrumento_id)
    logger.info(f"Adicionando instrumento {instrumento.nome} ao carrinho.")

    if request.user.is_authenticated:
        logger.info(f"Usuário autenticado, adicionando ao banco de dados.")
        carrinho_item, created = Carrinho.objects.get_or_create(cliente=request.user, instrumento=instrumento, defaults={'quantidade': 0})
        carrinho_item.quantidade += 1
        carrinho_item.save()
        logger.info(f"Item {instrumento.nome} adicionado ao carrinho do banco de dados. Quantidade: {carrinho_item.quantidade}")
    else:
        logger.info(f"Usuário não autenticado, adicionando à sessão.")
        carrinho = request.session.get('carrinho', {})
        instrumento_id_str = str(instrumento_id)
        if instrumento_id_str in carrinho:
            carrinho[instrumento_id_str]['quantidade'] += 1
        else:
            carrinho[instrumento_id_str] = {
                'nome': instrumento.nome,
                'preco': str(instrumento.preco),
                'quantidade': 1,
            }
        request.session['carrinho'] = carrinho
        logger.info(f"Item {instrumento.nome} adicionado ao carrinho da sessão. Quantidade: {carrinho[instrumento_id_str]['quantidade']}")

    request.session['total_itens'] = calcular_total_itens_carrinho(request)
    request.session.modified = True
    logger.info(f"Total itens no carrinho: {request.session['total_itens']}")
    return redirect('carrinho')


logger = logging.getLogger(__name__)
# def carrinho(request):
#     #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
#     total_itens = calcular_total_itens_carrinho(request)
#     itens_carrinho = []
#     total_geral = 0
#     total_itens_quantidade = 0

#     logger.info(f"Acessando a view carrinho. Usuário autenticado: {request.user.is_authenticated}")

#     if request.user.is_authenticated:
#         logger.info(f"Usuário autenticado: {request.user.email}")
#         logger.info(f"Usuario logado: {request.user.is_authenticated}")
#         carrinho_itens_db = Carrinho.objects.filter(cliente=request.user)
#         logger.info(f"Itens do carrinho (banco de dados): {carrinho_itens_db}")

#         for item in carrinho_itens_db:
#             instrumento = item.instrumento
#             preco = instrumento.preco
#             quantidade = item.quantidade
#             total_item = preco * quantidade
#             total_geral += total_item
#             total_itens_quantidade += quantidade

#             #preco_formatado = locale.currency(preco, grouping=True)
            
#             preco_formatado = formatar_preco_real(preco_formatado)
            
#             #total_item_formatado = locale.currency(total_item, grouping=True)

#             total_item_formatado = formatar_preco_real(total_item_formatado)

#             primeira_imagem = ImagemInstrumento.objects.filter(instrumento=instrumento).first()
#             imagem_url = primeira_imagem.imagem.url if primeira_imagem else None

#             itens_carrinho.append({
#                 'id': instrumento.id,
#                 'nome': instrumento.nome,
#                 'preco': preco_formatado,
#                 'quantidade': quantidade,
#                 'total_item': total_item_formatado,
#                 'imagem': imagem_url,
#             })
#     else:
#         logger.info(f"Usuário não autenticado. Sessão: {request.session.get('carrinho')}")
#         carrinho_sessao = request.session.get('carrinho', {})
#         for instrumento_id, item in carrinho_sessao.items():
#             try:
#                 instrumento = Instrumento.objects.get(pk=instrumento_id)
#                 preco = instrumento.preco
#                 quantidade = item['quantidade']
#                 total_item = preco * quantidade
#                 total_geral += total_item
#                 total_itens_quantidade += quantidade

#                 #preco_formatado = locale.currency(preco, grouping=True)
#                 preco_formatado = formatar_preco_real(preco_formatado)
                
                
#                 #total_item_formatado = locale.currency(total_item, grouping=True)
#                 total_item_formatado = formatar_preco_real(total_item_formatado)
                

#                 primeira_imagem = ImagemInstrumento.objects.filter(instrumento=instrumento).first()
#                 imagem_url = primeira_imagem.imagem.url if primeira_imagem else None

#                 itens_carrinho.append({
#                     'id': instrumento_id,
#                     'nome': item['nome'],
#                     'preco': preco_formatado,
#                     'quantidade': quantidade,
#                     'total_item': total_item_formatado,
#                     'imagem': imagem_url,
#                 })
#             except Instrumento.DoesNotExist:
#                 logger.error(f"Instrumento com ID {instrumento_id} não encontrado.")

#     total_geral_formatado = locale.currency(total_geral, grouping=True)
#     logger.info(f"Itens no carrinho: {itens_carrinho}")

#     # Atualizar a sessão
#     request.session['total_itens'] = total_itens_quantidade
#     request.session.modified = True

#     return render(request, 'carrinho.html', {
#         'itens_carrinho': itens_carrinho,
#         'total_geral': total_geral_formatado,
#         'total_itens': total_itens_quantidade,
#  })
 
 
 
def carrinho(request):
    #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    total_itens = calcular_total_itens_carrinho(request)
    itens_carrinho = []
    total_geral = 0
    total_itens_quantidade = 0

    logger.info(f"Acessando a view carrinho. Usuário autenticado: {request.user.is_authenticated}")

    if request.user.is_authenticated:
        logger.info(f"Usuário autenticado: {request.user.email}")
        logger.info(f"Usuario logado: {request.user.is_authenticated}")
        carrinho_itens_db = Carrinho.objects.filter(cliente=request.user)
        logger.info(f"Itens do carrinho (banco de dados): {carrinho_itens_db}")

        for item in carrinho_itens_db:
            instrumento = item.instrumento
            preco = instrumento.preco
            quantidade = item.quantidade
            total_item = preco * quantidade
            total_geral += total_item
            total_itens_quantidade += quantidade

            preco_formatado = formatar_preco_real(preco)
            total_item_formatado = formatar_preco_real(total_item)

            primeira_imagem = ImagemInstrumento.objects.filter(instrumento=instrumento).first()
            imagem_url = primeira_imagem.imagem.url if primeira_imagem else None

            itens_carrinho.append({
                'id': instrumento.id,
                'nome': instrumento.nome,
                'preco': preco_formatado,
                'quantidade': quantidade,
                'total_item': total_item_formatado,
                'imagem': imagem_url,
            })
    else:
        logger.info(f"Usuário não autenticado. Sessão: {request.session.get('carrinho')}")
        carrinho_sessao = request.session.get('carrinho', {})
        for instrumento_id, item in carrinho_sessao.items():
            try:
                instrumento = Instrumento.objects.get(pk=instrumento_id)
                preco = instrumento.preco
                quantidade = item['quantidade']
                total_item = preco * quantidade
                total_geral += total_item
                total_itens_quantidade += quantidade

                preco_formatado = formatar_preco_real(preco)
                total_item_formatado = formatar_preco_real(total_item)

                primeira_imagem = ImagemInstrumento.objects.filter(instrumento=instrumento).first()
                imagem_url = primeira_imagem.imagem.url if primeira_imagem else None

                itens_carrinho.append({
                    'id': instrumento_id,
                    'nome': item['nome'],
                    'preco': preco_formatado,
                    'quantidade': quantidade,
                    'total_item': total_item_formatado,
                    'imagem': imagem_url,
                })
            except Instrumento.DoesNotExist:
                logger.error(f"Instrumento com ID {instrumento_id} não encontrado.")

    total_geral_formatado = formatar_preco_real(total_geral)
    logger.info(f"Itens no carrinho: {itens_carrinho}")

    # Atualizar a sessão
    request.session['total_itens'] = total_itens_quantidade
    request.session.modified = True

    return render(request, 'carrinho.html', {
        'itens_carrinho': itens_carrinho,
        'total_geral': total_geral_formatado,
        'total_itens': total_itens_quantidade,
    })
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
       
    

def detalhe_instrumento(request, instrumento_id):
    #locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    instrumento = get_object_or_404(Instrumento, id=instrumento_id)
    imagens_secundarias = instrumento.imagens.all()[1:]
    total_itens = calcular_total_itens_carrinho(request)

    # Formatar o preço do instrumento
    #instrumento.preco_formatado = locale.currency(instrumento.preco, grouping=True)
    instrumento.preco_formatado = formatar_preco_real(instrumento.preco) #locale.currency(instrumento.preco, grouping=True).replace('.', '')

    # Atualizar a sessão
    request.session['total_itens'] = total_itens
    request.session.modified = True

    context = {
        'instrumento': instrumento,
        'imagens_secundarias': imagens_secundarias,
        'total_itens': total_itens,
    }
    return render(request, 'detalhes_produto.html', context)



def calcular_total_itens_carrinho(request):
    total_itens = 0
    if request.user.is_authenticated:
        carrinho_itens_db = Carrinho.objects.filter(cliente=request.user)
        for item in carrinho_itens_db:
            total_itens += item.quantidade
    else:
        carrinho_sessao = request.session.get('carrinho', {})
        for item in carrinho_sessao.values():
            total_itens += item.get('quantidade', 0)
    return total_itens



def remover_do_carrinho(request, instrumento_id):
    instrumento_id = str(instrumento_id) #garantindo que a id seja string
    logger.info(f"Removendo item {instrumento_id} do carrinho.")

    if request.user.is_authenticated:
        try:
            carrinho_item = get_object_or_404(Carrinho, cliente=request.user, instrumento_id=instrumento_id)
            carrinho_item.delete()
            logger.info(f"Item {instrumento_id} removido do carrinho do banco de dados.")
        except Carrinho.DoesNotExist:
            logger.warning(f"Item {instrumento_id} não encontrado no carrinho do banco de dados.")
    else:
        carrinho = request.session.get('carrinho', {})
        if instrumento_id in carrinho:
            del carrinho[instrumento_id]
            request.session['carrinho'] = carrinho
            request.session.modified = True
            logger.info(f"Item {instrumento_id} removido do carrinho da sessão.")
        else:
            logger.warning(f"Item {instrumento_id} não encontrado no carrinho da sessão.")

    request.session['total_itens'] = calcular_total_itens_carrinho(request)
    request.session.modified = True
    logger.info(f"Total de itens no carrinho atualizado: {request.session['total_itens']}")

    return redirect('carrinho')




def user_is_authenticated(user):
    return user.is_authenticated

@user_passes_test(user_is_authenticated, login_url='/pre-login/')
def finalizar_pedido(request):
    carrinho_itens_db = Carrinho.objects.filter(cliente=request.user)
    total_geral = 0
    items = []

    # Extrai os dados do usuário logado
    nome_completo = request.user.nome_completo
    nome = nome_completo.split()[0] if nome_completo else ""
    sobrenome = " ".join(nome_completo.split()[1:]) if len(nome_completo.split()) > 1 else ""
    email = request.user.email
    cpf = request.user.cpf
    cep = request.user.cep
    endereco = request.user.endereco
    numero = request.user.numero
    complemento = request.user.complemento

    # Prepara os dados do pagador
    payer_data = {
        "name": nome,
        "surname": sobrenome,
        "email": email,
        "identification": {
            "type": "CPF",
            "number": cpf
        },
        "address": {
            "zip_code": cep,
            "street_name": endereco,
            "street_number": numero,
            "complement": complemento,
        }
    }

    # Prepara os dados de envio
    shipment_data = {
        "receiver_address": {
            "zip_code": cep,
            "street_name": endereco,
            "street_number": numero,
            "complement": complemento,
        }
    }

    pedido = Pedido.objects.create(cliente=request.user, valor_total=0)

    for item in carrinho_itens_db:
        instrumento = item.instrumento
        quantidade = item.quantidade
        preco_unitario = instrumento.preco
        total_item = preco_unitario * quantidade

        total_geral += total_item

        ItemPedido.objects.create(pedido=pedido, instrumento=instrumento, quantidade=quantidade, preco_unitario=preco_unitario)

        items.append({
            "nome": instrumento.nome,
            "quantidade": quantidade,
            "preco": preco_unitario
        })

    pedido.valor_total = total_geral
    pedido.save()

    retorno_url = request.build_absolute_uri(reverse('pagamento_retorno'))

    items_formatados = []
    for item in items:
        preco_str = str(item['preco']).replace('R$', '').replace('.', '').replace(',', '.')
        try:
            preco_float = float(preco_str.strip())
        except ValueError as e:
            print(f"Erro ao converter preço: {e}")
            preco_float = 0.0  # Ou outro valor padrão, dependendo do tratamento de erro desejado

        items_formatados.append({
            "nome": item['nome'],
            "quantidade": item['quantidade'],
            "preco": preco_float
        })

    total_geral_str = str(total_geral).replace('R$', '').replace('.', '').replace(',', '.')
    try:
        total_geral_float = float(total_geral_str.strip())
    except ValueError as e:
        print(f"Erro ao converter total geral: {e}")
        total_geral_float = 0.0  # Ou outro valor padrão, dependendo do tratamento de erro desejado

    payment_link, preference_id = criar_pagamento(items_formatados, retorno_url, total_geral_float, str(pedido.id), payer_data, shipment_data)
    print(preco_unitario)
    print(total_geral)

    if payment_link:
        return redirect(payment_link)
    else:
        return render(request, 'pagamento_erro.html')








































def pagamento_retorno(request):
    """
    Processa o retorno do pagamento do Mercado Pago, atualizando o pedido no banco de dados.
    """

    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    preference_id = request.GET.get('preference_id')
    payment_id = request.GET.get('payment_id')

    print(f"Status recebido: {status}")
    print(f"External reference recebido: {external_reference}")
    print(f"preference_id recebido: {preference_id}")
    print(f"payment_id recebido: {payment_id}")

    if external_reference:
        try:
            pedido = Pedido.objects.get(id=external_reference)
            itens_pedido = ItemPedido.objects.filter(pedido=pedido)

            if status == 'approved':
                sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
                try:
                    pagamento = sdk.payment().get(payment_id)

                    if pagamento['status'] == 200:
                        payment_data = pagamento['response']
                        meio_pagamento_codigo = payment_data.get('payment_type_id')
                        codigo_transacao = payment_data.get('id')
                        data_pagamento = payment_data.get('date_approved')

                        # Converter código do meio de pagamento para nome
                        if meio_pagamento_codigo == 'credit_card':
                            meio_pagamento = 'Cartão de Crédito'
                        else:
                            meio_pagamento = meio_pagamento_codigo

                        # Preencher dados do pagador e envio com os dados do cliente logado
                        pedido.nome_pagador = pedido.cliente.nome_completo.split()[0] if pedido.cliente.nome_completo else ""
                        pedido.sobrenome_pagador = " ".join(pedido.cliente.nome_completo.split()[1:]) if pedido.cliente.nome_completo and len(pedido.cliente.nome_completo.split()) > 1 else ""
                        pedido.email_pagador = pedido.cliente.email or ''
                        pedido.cpf_pagador = pedido.cliente.cpf or ''
                        pedido.cep_pagador = pedido.cliente.cep or ''
                        pedido.rua_pagador = pedido.cliente.endereco or ''
                        pedido.numero_pagador = pedido.cliente.numero or ''
                        pedido.complemento_pagador = pedido.cliente.complemento or ''
                        pedido.bairro_pagador = pedido.cliente.bairro or ''
                        pedido.cidade_pagador = pedido.cliente.cidade or ''
                        pedido.estado_pagador = pedido.cliente.estado or ''

                        pedido.cep_entrega = pedido.cliente.cep or ''
                        pedido.rua_entrega = pedido.cliente.endereco or ''
                        pedido.numero_entrega = pedido.cliente.numero or ''
                        pedido.complemento_entrega = pedido.cliente.complemento or ''
                        pedido.bairro_entrega = pedido.cliente.bairro or ''
                        pedido.cidade_entrega = pedido.cliente.cidade or ''
                        pedido.estado_entrega = pedido.cliente.estado or ''


                        # Atualizar pedido
                        pedido.status_pagamento = 'aprovado'
                        pedido.meio_pagamento = meio_pagamento
                        pedido.codigo_transacao = codigo_transacao
                        pedido.data_pagamento = data_pagamento
                        pedido.save()

                        Carrinho.objects.filter(cliente=pedido.cliente).delete()
                        return render(request, 'compra_concluida.html', {'status': status, 'pedido': pedido, 'itens_pedido': itens_pedido})
                    else:
                        print(f"Erro ao obter detalhes do pagamento: {pagamento}")
                        return render(request, 'pagamento_erro.html', {'error_message': 'Erro ao obter detalhes do pagamento.'})
                except Exception as e:
                    print(f"Erro ao obter detalhes do pagamento: {e}")
                    return render(request, 'pagamento_erro.html', {'error_message': 'Erro ao obter detalhes do pagamento.'})

            elif status in ['pending', 'rejected']:
                pedido.status_pagamento = 'pendente' if status == 'pending' else 'rejeitado'
                pedido.save()

                if status == 'rejected':
                    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
                    try:
                        pagamento = sdk.payment().get(payment_id)

                        if pagamento['status'] == 200 and 'status_detail' in pagamento['response']:
                            erro_detalhe = pagamento['response']['status_detail']
                            return render(request, 'pagamento_erro.html', {'mensagem': f'Pagamento rejeitado: {erro_detalhe}', 'payment_id': payment_id})
                        else:
                            return render(request, 'pagamento_erro.html', {'mensagem': 'Pagamento rejeitado.', 'payment_id': payment_id})
                    except Exception as e:
                        print(f"Erro ao obter detalhes do pagamento: {e}")
                        return render(request, 'pagamento_erro.html', {'mensagem': 'Pagamento rejeitado. Detalhes adicionais não disponíveis.', 'payment_id': payment_id})
                else:
                    return render(request, 'compra_concluida.html', {'status': status, 'pedido': pedido, 'itens_pedido': itens_pedido})

            else:
                print(f"Status de pagamento desconhecido ou nulo: {status}")
                return redirect('carrinho')
        except Pedido.DoesNotExist:
            print(f"Pedido com external_reference {external_reference} não encontrado.")
            return render(request, 'pagamento_erro.html', {'mensagem': 'Pedido não encontrado.'})
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return render(request, 'pagamento_erro.html', {'mensagem': 'Ocorreu um erro inesperado.'})
    else:
        print("External reference não fornecido.")
        if 'carrinho' in request.session:
            return redirect('carrinho')
        else:
            return redirect('carrinho')



def lista_pedidos(request):
    if request.user.is_authenticated:
        pedidos = Pedido.objects.filter(cliente=request.user)
        return render(request, 'lista_pedidos.html', {'pedidos': pedidos})
    else:
        return render(request, 'lista_pedidos.html')


def filtrar_categoria(request, categoria_id):
    instrumentos = Instrumento.objects.filter(categoria=categoria_id)
    return render(request, 'home.html', {'instrumentos': instrumentos})
