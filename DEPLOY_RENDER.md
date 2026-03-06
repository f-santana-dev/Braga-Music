# Deploy do BragaMusic no Render

Este guia foi feito para publicar o projeto `BragaMusic` no Render usando Django + Gunicorn + PostgreSQL.

## 1. Antes de comecar

Voce precisa ter:
- o repositorio `Braga-Music` publicado no GitHub;
- uma conta no Render;
- o projeto ja atualizado no GitHub com os arquivos de deploy.

## 2. Criar o banco PostgreSQL no Render

1. Acesse o painel do Render.
2. Clique em `New +`.
3. Escolha `PostgreSQL`.
4. Preencha:
   - `Name`: `braga-music-db`
   - `Database`: `bragamusic`
   - `User`: `bragamusic_user`
5. Crie o banco.
6. Depois que o banco estiver pronto, use a conexao interna do proprio Render para preencher a `DATABASE_URL`.

## 3. Criar o servico web

1. No painel do Render, clique em `New +`.
2. Escolha `Web Service`.
3. Conecte o repositorio `f-santana-dev/Braga-Music`.
4. Preencha os campos assim:

- `Name`: `braga-music`
- `Region`: escolha a mais proxima
- `Branch`: `main`
- `Runtime`: `Python 3`
- `Root Directory`: deixe vazio

## 4. Build e Start Command

Use exatamente estes comandos:

### Build Command
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py bootstrap_catalogo_demo
```

Se o painel pedir uma unica linha, use:
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py bootstrap_catalogo_demo
```

### Start Command
```bash
gunicorn BragaMusic.wsgi:application
```

Nao use:
```bash
gunicorn app:app
```

Esse comando nao serve para este projeto.

## 5. Variaveis de ambiente

No Render, abra a aba `Environment` do servico e crie estas variaveis.

### Obrigatorias

#### SECRET_KEY
Use uma chave forte. Exemplo:
```env
SECRET_KEY=sua-chave-secreta-forte-aqui
```

#### DJANGO_DEBUG
```env
DJANGO_DEBUG=False
```

#### ALLOWED_HOSTS
Troque pela URL real do seu app.
Exemplo:
```env
ALLOWED_HOSTS=braga-music.onrender.com
```

#### CSRF_TRUSTED_ORIGINS
Troque pela URL real do seu app.
Exemplo:
```env
CSRF_TRUSTED_ORIGINS=https://braga-music.onrender.com
```

#### DATABASE_URL
Se o banco estiver integrado ao servico no Render, essa variavel pode ser preenchida automaticamente.
Se precisar colar manualmente, use a URL do PostgreSQL gerada pelo Render.

Exemplo:
```env
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco
```

#### AUTO_SEED_DEMO
Mantem o catalogo demo sendo criado automaticamente quando o banco estiver vazio.
```env
AUTO_SEED_DEMO=True
```

### Para pagamentos com Mercado Pago

#### MERCADO_PAGO_PUBLIC_KEY
```env
MERCADO_PAGO_PUBLIC_KEY=sua-public-key
```

#### MERCADO_PAGO_ACCESS_TOKEN
```env
MERCADO_PAGO_ACCESS_TOKEN=seu-access-token
```

Se voce ainda nao for testar pagamentos, pode deixar essas duas vazias por enquanto no Render, mas o fluxo de pagamento nao vai funcionar.

### Recomendadas

#### DJANGO_LOG_LEVEL
```env
DJANGO_LOG_LEVEL=INFO
```

#### SECURE_SSL_REDIRECT
```env
SECURE_SSL_REDIRECT=True
```

#### SESSION_COOKIE_SECURE
```env
SESSION_COOKIE_SECURE=True
```

#### CSRF_COOKIE_SECURE
```env
CSRF_COOKIE_SECURE=True
```

## 6. Resumo rapido das variaveis

Copie este modelo e ajuste os valores:

```env
SECRET_KEY=sua-chave-secreta-forte-aqui
DJANGO_DEBUG=False
ALLOWED_HOSTS=braga-music.onrender.com
CSRF_TRUSTED_ORIGINS=https://braga-music.onrender.com
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco
AUTO_SEED_DEMO=True
MERCADO_PAGO_PUBLIC_KEY=
MERCADO_PAGO_ACCESS_TOKEN=
DJANGO_LOG_LEVEL=INFO
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## 7. Fazer o deploy

1. Salve as configuracoes.
2. Clique em `Create Web Service` ou `Manual Deploy`.
3. Aguarde o build terminar.
4. Abra a URL publica gerada pelo Render.

## 8. Se der erro no primeiro deploy

Verifique nesta ordem:

1. `Start Command` esta como `gunicorn BragaMusic.wsgi:application`
2. `DJANGO_DEBUG=False`
3. `ALLOWED_HOSTS` contem o dominio correto do Render
4. `CSRF_TRUSTED_ORIGINS` contem a URL com `https://`
5. `DATABASE_URL` esta preenchida corretamente
6. o banco PostgreSQL foi criado e vinculado
7. `collectstatic` e `migrate` rodaram no build
8. `AUTO_SEED_DEMO=True` se voce quiser catalogo demo automatico

## 9. Observacao importante sobre imagens

Hoje o projeto usa `media/` local. Para portfolio isso pode funcionar em cenarios simples, mas para producao real o ideal e usar armazenamento externo, como:
- Cloudinary
- AWS S3
- Backblaze

Se a aplicacao permitir upload de arquivos por usuarios, esse ajuste sera necessario.

## 10. Catalogo demo automatico

O projeto foi configurado para executar automaticamente:
```bash
python manage.py bootstrap_catalogo_demo
```

Esse comando:
- verifica se `AUTO_SEED_DEMO=True`;
- verifica se o banco esta vazio;
- cria categorias, marcas, instrumentos e imagens demo somente quando necessario.

Com isso, se voce perder o banco e recriar outro no Render, o catalogo volta automaticamente no proximo deploy.

## 11. Comandos corretos para este projeto

### Build
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py bootstrap_catalogo_demo
```

### Start
```bash
gunicorn BragaMusic.wsgi:application
```
