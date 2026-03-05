#-----------instrumento.models.py ------------- #

from django.db import models
from django.utils.text import slugify

import re
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission



# Definição dos estados brasileiros como choices
ESTADOS_CHOICES = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
]

# Gerenciador de Usuário para Cliente
class ClienteManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O campo Email é obrigatório")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário deve ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário deve ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class Cliente(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="E-mail")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")  # Adicionado campo
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    telefone = models.CharField(max_length=15, verbose_name="Telefone")
    cep = models.CharField(max_length=9, verbose_name="CEP")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    numero = models.CharField(max_length=10, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=2, choices=ESTADOS_CHOICES, verbose_name="Estado")
    aceitou_politica = models.BooleanField(default=False, verbose_name="Aceitou Política de Privacidade")  # Novo campo

    is_staff = models.BooleanField(default=False, verbose_name="Membro da equipe")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "cpf", "telefone", "cep", "endereco", "numero", "bairro", "cidade", "estado"]

    objects = ClienteManager()  # Usa o gerenciador personalizado

    def primeiro_nome(self):
        return self.nome_completo.split()[0] if self.nome_completo else ""

    def __str__(self):
        return self.nome_completo

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição da Categoria")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Marca")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição da Marca")
    logo = models.ImageField(upload_to='marcas/', blank=True, null=True, verbose_name="Logo da Marca")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nome']



class Instrumento(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Instrumento")
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modelo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name="Categoria", default=1)
    material = models.CharField(max_length=100, blank=True, null=True, verbose_name="Material")
    cor = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cor")
    estoque = models.PositiveIntegerField(default=0, verbose_name="Quantidade em Estoque")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Instrumento"
        verbose_name_plural = "Instrumentos"
        ordering = ['nome']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class ImagemInstrumento(models.Model):
    instrumento = models.ForeignKey(                          
        'Instrumento', 
        on_delete=models.CASCADE, 
        related_name='imagens',  # Permite acessar as imagens com `instrumento.imagens.all()`
        verbose_name="Instrumento"
    )
    imagem = models.ImageField(
    upload_to='',
    verbose_name="Imagem do Instrumento"
    ) 
    
    descricao = models.CharField(
        max_length=300, 
        blank=True, 
        null=True, 
        verbose_name="Descrição da Imagem"
    )

    def __str__(self):
        return f"Imagem de {self.instrumento.nome}"

    class Meta:
        verbose_name = "Imagem do Instrumento"
        verbose_name_plural = "Imagens dos Instrumentos"
        ordering = ['id']


class Pedido(models.Model):
    nome_pagador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome do Pagador")
    sobrenome_pagador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sobrenome do Pagador")
    email_pagador = models.EmailField(blank=True, null=True, verbose_name="Email do Pagador")
    cpf_pagador = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF do Pagador")
    cep_pagador = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP do Pagador")
    rua_pagador = models.CharField(max_length=200, blank=True, null=True, verbose_name="Rua do Pagador")
    numero_pagador = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número do Pagador")
    complemento_pagador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento do Pagador")
    bairro_pagador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro do Pagador")
    cidade_pagador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade do Pagador")
    estado_pagador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado do Pagador")

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    data_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Data do Pedido")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    status = models.CharField(max_length=50, choices=[
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ], default='pendente', verbose_name="Status do Pedido")

    # Campos de pagamento
    status_pagamento = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ], default='pendente', verbose_name="Status do Pagamento")
    meio_pagamento = models.CharField(max_length=50, blank=True, null=True, verbose_name="Meio de Pagamento")
    codigo_transacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Transação")
    data_pagamento = models.DateTimeField(blank=True, null=True, verbose_name="Data do Pagamento")

    # Dados de envio
    cep_entrega = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP de Entrega")
    rua_entrega = models.CharField(max_length=200, blank=True, null=True, verbose_name="Rua de Entrega")
    numero_entrega = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número de Entrega")
    complemento_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento de Entrega")
    bairro_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro de Entrega")
    cidade_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade de Entrega")
    estado_entrega = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado de Entrega")

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente.nome_completo}"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-data_pedido']







class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, verbose_name="Pedido")
    instrumento = models.ForeignKey(Instrumento, on_delete=models.CASCADE, verbose_name="Instrumento")
    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")

    def __str__(self):
        return f"{self.quantidade} x {self.instrumento.nome} no Pedido #{self.pedido.pk}"

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"




class Carrinho(models.Model):#carrinho.py
    """
    criar a tabela carrinho do cliente com os produtos que o cliente adicionar para quando o cliente finalizar a compra o carrinho seja limpo
    e quahdo o cliente fizer o logout o carrinho seja salvo no banco de dados e quando ele logar novamente os produtos sejam adicionados novamente no carrinho
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")# criar o carrinho com chave estrangeira da tabela cliente
    instrumento = models.ForeignKey(Instrumento, on_delete=models.CASCADE, verbose_name="Instrumento") # criar o carrinho com chave estrangeira da tabela instrumento
    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade")# criar o carrinho com chave estrangeira da tabela instrumento