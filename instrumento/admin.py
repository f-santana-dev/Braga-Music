
#-------------- Admin.py------------- #                   


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Cliente, Categoria, Marca, Instrumento, ImagemInstrumento, Pedido, ItemPedido
from .forms import ClienteCadastroForm

# Configuração do Cliente no Django Admin
class ClienteAdmin(UserAdmin):
    form = ClienteCadastroForm  # Usa o ClienteCadastroForm corrigido
    list_display = ('nome_completo', 'id', 'email', 'cpf', 'telefone', 'cidade', 'estado','aceitou_politica',  'is_staff', 'is_superuser')  
    search_fields = ('email', 'cpf', 'telefone')  
    list_filter = ('estado', 'is_staff', 'is_superuser')  
    ordering = ('id',)

    fieldsets = (
        ("Informações Pessoais", {'fields': ('email', 'password', 'cpf', 'telefone')}),  
        ("Endereço", {'fields': ('cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado')}),  
        ("Permissões", {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),  
        ("Datas Importantes", {'fields': ('last_login', 'date_joined')}),  
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username','nome_completo','email', 'cpf', 'telefone', 'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado', 'is_staff', 'is_superuser', 'password1', 'password2')  
        }),
    )  


# Configuração de Categoria
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)
    ordering = ('nome',)

# Configuração de Marca
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)
    ordering = ('nome',)

# Configuração de Instrumento
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'marca', 'categoria', 'preco', 'estoque', 'ativo')
    search_fields = ('nome', 'marca__nome', 'categoria__nome')
    list_filter = ('marca', 'categoria', 'ativo')
    ordering = ('nome',)
    prepopulated_fields = {"slug": ("nome",)}

# # Configuração de Imagem do Instrumento
# class ImagemInstrumentoAdmin(admin.ModelAdmin):
#     list_display = ('id', 'instrumento', 'imagem')
#     search_fields = ('instrumento__nome',)

# Configuração de Imagem do Instrumento
class ImagemInstrumentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrumento', 'imagem')  # Alterado para 'imagem_url'
    search_fields = ('instrumento__nome',)

# Configuração de Pedido
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data_pedido', 'valor_total', 'status')
    search_fields = ('cliente__username', 'cliente__email', 'status')
    list_filter = ('status', 'data_pedido')
    ordering = ('-data_pedido',)

# Configuração de Item do Pedido
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'instrumento', 'quantidade', 'preco_unitario')
    search_fields = ('pedido__id', 'instrumento__nome')
    ordering = ('pedido',)

# Registro dos modelos no Django Admin
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Instrumento, InstrumentoAdmin)
admin.site.register(ImagemInstrumento, ImagemInstrumentoAdmin)
admin.site.register(Pedido, PedidoAdmin)
admin.site.register(ItemPedido, ItemPedidoAdmin)


# Configuração do título do Django Admin
admin.site.site_header = "Administração da Loja de Instrumentos"
admin.site.site_title = "Painel Administrativo"
admin.site.index_title = "Bem-vindo ao Painel Administrativo"
