


#####################################################################
# api_mercadopago.py

import mercadopago
from django.conf import settings

sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

# def criar_pagamento(itens, link_retorno, total_geral, pedido_id, payer_data=None, shipment_data=None):
#     locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
#     preference_data = {
#         "items": [
#             {
#                 "title": item['nome'],
#                 "quantity": item['quantidade'],
#                 "unit_price": float(item['preco'].replace('.', '').replace(',', '.')), 
#                 "currency_id": "BRL",
#             } for item in itens
#         ],
#         "auto_return": "all",
#         "back_urls": {
#             "success": link_retorno,
#             "pending": link_retorno,
#             "failure": link_retorno,
#         },
#         "total_amount": float(total_geral.replace('.', '').replace(',', '.')), 
#         "external_reference": str(pedido_id),
#         "metadata": {
#             "meio_pagamento": "meio_pagamento_placeholder",
#             "transaction_id": "transaction_id_placeholder",
#         },
#         "currency_id": "BRL",
#         "locale": "pt-BR"
#     }

#     # Adiciona os dados do pagador e envio se fornecidos
#     if payer_data:
#         preference_data["payer"] = payer_data
#     if shipment_data:
#         preference_data["shipments"] = shipment_data

#     # Formatar o unit_price e total_amount como string com duas casas decimais (para exibição)
#     for item in preference_data['items']:
#         item['unit_price_str'] = "{:.2f}".format(item['unit_price'])  # Armazena a string formatada
#     preference_data['total_amount_str'] = "{:.2f}".format(preference_data['total_amount'])  # Armazena a string formatada

#     # Converter unit_price e total_amount de volta para float para o Mercado Pago
#     for item in preference_data['items']:
#         item['unit_price'] = float(item['unit_price_str'])
#     preference_data['total_amount'] = float(preference_data['total_amount_str'])

#     print("preference_data:", preference_data)
#     resposta = sdk.preference().create(preference_data)
#     print("total_geral:", total_geral, "preco:", preference_data['items'][0])

#     if resposta['status'] == 201:
#         preference_id = resposta['response']['id']
#         payment_link = resposta['response'].get('init_point', None)
#         print("total_geral:", total_geral, "preco:", preference_data['items'][0])
#         if payment_link:
#             return payment_link, preference_id
#         else:
#             print("Erro: 'init_point' não encontrado na resposta.")
#             return None, None
#     else:
#         print(f"Erro ao criar a preferência: {resposta.get('message', 'Erro desconhecido')}")
#         print("Resposta completa do Mercado Pago:", resposta)
#         print("Detalhes do erro:", resposta.get('response', {}))
#         return None, None



def criar_pagamento(itens, link_retorno, total_geral, pedido_id, payer_data=None, shipment_data=None):
   
    preference_data = {
        "items": [
            {
                "title": item['nome'],
                "quantity": item['quantidade'],
                "unit_price": float(item['preco']),  # Preço já deve ser float
                "currency_id": "BRL",
            } for item in itens
        ],
        "auto_return": "all",
        "back_urls": {
            "success": link_retorno,
            "pending": link_retorno,
            "failure": link_retorno,
        },
        "total_amount": float(total_geral),  # Total geral já deve ser float
        "external_reference": str(pedido_id),
        "metadata": {
            "meio_pagamento": "meio_pagamento_placeholder",
            "transaction_id": "transaction_id_placeholder",
        },
        "currency_id": "BRL",
        "locale": "pt-BR"
    }

    # Adiciona os dados do pagador e envio se fornecidos
    if payer_data:
        preference_data["payer"] = payer_data
    if shipment_data:
        preference_data["shipments"] = shipment_data

    print("preference_data:", preference_data)
    resposta = sdk.preference().create(preference_data)
    print("total_geral:", total_geral, "preco:", preference_data['items'][0])

    if resposta['status'] == 201:
        preference_id = resposta['response']['id']
        payment_link = resposta['response'].get('init_point', None)
        print("total_geral:", total_geral, "preco:", preference_data['items'][0])
        if payment_link:
            return payment_link, preference_id
        else:
            print("Erro: 'init_point' não encontrado na resposta.")
            return None, None
    else:
        print(f"Erro ao criar a preferência: {resposta.get('message', 'Erro desconhecido')}")
        print("Resposta completa do Mercado Pago:", resposta)
        print("Detalhes do erro:", resposta.get('response', {}))
        return None, None
