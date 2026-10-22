import asyncio

async def deletar_canal_com_atraso(channel, delay: int):
    """Espera o tempo determinado e deleta o canal com segurança."""
    await asyncio.sleep(delay)
    try:
        await channel.delete()
        print(f"Canal {channel.name} deletado com sucesso após {delay} segundos.")
    except Exception as e:
        print(f"Erro ao tentar deletar o canal {channel.name}: {e}")
import json
import os

ARQUIVO_ESTATISTICAS = "estatisticas_vendas.json"

def registrar_venda_total(produto_nome, quantidade, valor_total):
    """Guarda e acumula o histórico de vendas de cada produto"""
    # 1. Abre o arquivo antigo se ele já existir, senão cria uma lista vazia
    if os.path.exists(ARQUIVO_ESTATISTICAS):
        with open(ARQUIVO_ESTATISTICAS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {}

    # 2. Se o produto acabou de ser vendido pela primeira vez, inicia zerado
    if produto_nome not in dados:
        dados[produto_nome] = {"vendas_feitas": 0, "total_faturado": 0.0}

    # 3. Soma as quantidades e valores atuais aos totais salvos
    dados[produto_nome]["vendas_feitas"] += quantidade
    dados[produto_nome]["total_faturado"] += valor_total

    # 4. Grava a lista atualizada de volta no arquivo do computador
    with open(ARQUIVO_ESTATISTICAS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
        
    return dados
