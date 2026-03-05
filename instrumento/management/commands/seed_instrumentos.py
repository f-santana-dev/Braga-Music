import io
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from PIL import Image, ImageDraw

from instrumento.models import Categoria, ImagemInstrumento, Instrumento, Marca


class Command(BaseCommand):
    help = "Popula o banco com instrumentos e imagens de demonstracao"

    def add_arguments(self, parser):
        parser.add_argument("--total", type=int, default=24, help="Quantidade de instrumentos")
        parser.add_argument(
            "--imagens-por-item",
            type=int,
            default=2,
            help="Quantidade de imagens por instrumento",
        )
        parser.add_argument(
            "--limpar",
            action="store_true",
            help="Remove instrumentos e imagens de demo antes de popular",
        )

    def handle(self, *args, **options):
        total = max(1, options["total"])
        imagens_por_item = max(1, options["imagens_por_item"])
        limpar = options["limpar"]

        if limpar:
            self.stdout.write(self.style.WARNING("Removendo instrumentos e imagens de demo..."))
            ImagemInstrumento.objects.filter(descricao__icontains="DEMO").delete()
            Instrumento.objects.filter(descricao__icontains="DEMO").delete()

        imagens_reais = self._listar_imagens_reais()
        if imagens_reais:
            self.stdout.write(
                self.style.SUCCESS(f"Imagens reais encontradas para seed: {len(imagens_reais)}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhuma imagem real encontrada em media/static. Sera usado fallback gerado."
                )
            )

        categorias = self._criar_categorias()
        marcas = self._criar_marcas()

        instrumentos_criados = 0
        imagens_criadas = 0

        for idx in range(1, total + 1):
            categoria = categorias[(idx - 1) % len(categorias)]
            marca = marcas[(idx - 1) % len(marcas)]

            nome = self._nome_instrumento(categoria.nome, idx)
            modelo = f"MOD-{idx:03d}"
            preco = self._preco_aleatorio(categoria.nome)
            cor = random.choice(["Preto", "Branco", "Vermelho", "Azul", "Natural", "Sunburst"])
            estoque = random.randint(2, 40)

            instrumento, created = Instrumento.objects.get_or_create(
                nome=nome,
                marca=marca,
                defaults={
                    "modelo": modelo,
                    "categoria": categoria,
                    "descricao": f"Produto DEMO para testes de vitrine, carrinho e checkout ({nome}).",
                    "preco": preco,
                    "material": random.choice(["Madeira", "Metal", "Composite"]),
                    "cor": cor,
                    "estoque": estoque,
                    "ativo": True,
                    "slug": f"{slugify(nome)}-{idx}",
                },
            )

            if not created:
                instrumento.modelo = modelo
                instrumento.categoria = categoria
                instrumento.descricao = (
                    f"Produto DEMO para testes de vitrine, carrinho e checkout ({nome})."
                )
                instrumento.preco = preco
                instrumento.material = random.choice(["Madeira", "Metal", "Composite"])
                instrumento.cor = cor
                instrumento.estoque = estoque
                instrumento.ativo = True
                instrumento.slug = instrumento.slug or f"{slugify(nome)}-{idx}"
                instrumento.save()

            instrumentos_criados += 1

            existentes = ImagemInstrumento.objects.filter(instrumento=instrumento).count()
            faltantes = max(0, imagens_por_item - existentes)

            for img_index in range(1, faltantes + 1):
                imagem = ImagemInstrumento.objects.create(
                    instrumento=instrumento,
                    descricao=f"Imagem DEMO {img_index} de {nome}",
                )

                arquivo_real = self._escolher_imagem_real(imagens_reais)
                if arquivo_real:
                    ext = arquivo_real.suffix.lower() or ".jpg"
                    with arquivo_real.open("rb") as f:
                        conteudo = ContentFile(f.read())
                    caminho = f"instrumentos/demo/{instrumento.slug}-{img_index}{ext}"
                    imagem.imagem.save(caminho, conteudo, save=True)
                else:
                    arquivo = self._gerar_imagem_demo(nome, img_index)
                    caminho = f"instrumentos/demo/{instrumento.slug}-{img_index}.jpg"
                    imagem.imagem.save(caminho, arquivo, save=True)

                imagens_criadas += 1

        self.stdout.write(self.style.SUCCESS("Seed concluido com sucesso."))
        self.stdout.write(f"- Instrumentos processados: {instrumentos_criados}")
        self.stdout.write(f"- Imagens criadas: {imagens_criadas}")

    def _criar_categorias(self):
        nomes = [
            "Violao",
            "Guitarra",
            "Baixo",
            "Teclado",
            "Bateria",
            "Percussao",
            "Sopro",
            "Acessorios",
        ]
        categorias = []
        for nome in nomes:
            categoria, _ = Categoria.objects.get_or_create(
                nome=nome,
                defaults={"descricao": f"Categoria DEMO: {nome}"},
            )
            categorias.append(categoria)
        return categorias

    def _criar_marcas(self):
        nomes = ["Yamaha", "Fender", "Tagima", "Roland", "Casio", "Ibanez"]
        marcas = []
        for nome in nomes:
            marca, _ = Marca.objects.get_or_create(
                nome=nome,
                defaults={"descricao": f"Marca DEMO: {nome}"},
            )
            marcas.append(marca)
        return marcas

    def _preco_aleatorio(self, categoria_nome):
        faixas = {
            "Violao": (Decimal("500.00"), Decimal("4500.00")),
            "Guitarra": (Decimal("900.00"), Decimal("9000.00")),
            "Baixo": (Decimal("1000.00"), Decimal("7000.00")),
            "Teclado": (Decimal("700.00"), Decimal("12000.00")),
            "Bateria": (Decimal("1200.00"), Decimal("15000.00")),
            "Percussao": (Decimal("120.00"), Decimal("2500.00")),
            "Sopro": (Decimal("600.00"), Decimal("10000.00")),
            "Acessorios": (Decimal("40.00"), Decimal("1200.00")),
        }
        minimo, maximo = faixas.get(categoria_nome, (Decimal("200.00"), Decimal("2000.00")))
        valor = random.uniform(float(minimo), float(maximo))
        return Decimal(str(round(valor, 2)))

    def _nome_instrumento(self, categoria_nome, idx):
        return f"{categoria_nome} Demo {idx:03d}"

    def _listar_imagens_reais(self):
        extensoes = {".jpg", ".jpeg", ".png", ".webp"}
        caminhos = []

        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            for arquivo in media_root.rglob("*"):
                if arquivo.is_file() and arquivo.suffix.lower() in extensoes:
                    if "instrumentos\\demo" not in str(arquivo).lower().replace("/", "\\"):
                        caminhos.append(arquivo)

        static_root = Path(settings.BASE_DIR) / "static"
        if static_root.exists():
            for arquivo in static_root.rglob("*"):
                if arquivo.is_file() and arquivo.suffix.lower() in extensoes:
                    caminhos.append(arquivo)

        return caminhos

    def _escolher_imagem_real(self, imagens_reais):
        if not imagens_reais:
            return None
        return random.choice(imagens_reais)

    def _gerar_imagem_demo(self, nome, indice):
        largura, altura = 1000, 1000
        bg = random.choice(
            [
                (18, 34, 64),
                (44, 62, 80),
                (57, 42, 90),
                (83, 44, 44),
                (35, 67, 55),
            ]
        )

        imagem = Image.new("RGB", (largura, altura), bg)
        draw = ImageDraw.Draw(imagem)

        draw.rectangle((40, 40, 960, 960), outline=(230, 230, 230), width=5)
        draw.rectangle((80, 80, 920, 350), fill=(255, 255, 255))
        draw.text((120, 170), "BRAGA MUSIC", fill=(20, 20, 20))
        draw.text((120, 230), f"{nome}", fill=(20, 20, 20))
        draw.text((120, 700), f"Imagem DEMO #{indice}", fill=(245, 245, 245))

        buffer = io.BytesIO()
        imagem.save(buffer, format="JPEG", quality=90)
        return ContentFile(buffer.getvalue())
