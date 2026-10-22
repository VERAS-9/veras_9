import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import asyncio
from utils import deletar_canal_com_atraso  
import os
from dotenv import load_dotenv

CHAVE_PIX_DONO = os.getenv('CHAVE_PIX_DONO')
NOME_DONO_PIX = "Renan de S. Prates"       

PRODUTOS = {
    "cash_1k": {"nome": "💵 cash 1K", "preco": 3.50},
    "cash_5k": {"nome": "💵 cash 5K", "preco": 17.50},
    "cash_10k": {"nome": "💵 cash 10K", "preco": 35.00},
    "cash_20k": {"nome": "💵 cash 20K", "preco": 70.00},
    "cash_30k": {"nome": "💵 cash 30K", "preco": 105.00},
    "cash_40k": {"nome": "💵 cash 40K", "preco": 140.00},
    "cash_50k": {"nome": "💵 cash 50K", "preco": 175.00},
    "passe": {"nome": "🎫 Passe", "preco": 25.00},
    "caixas_5": {"nome": "📦 5 Caixas", "preco": 10.00}
}



ESTOQUE_CODIGOS = ["adm lhe entregou o cash", "passe se entrege em breve", "caixas serao entregues em breve"]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Painel de Validação para os Administradores (Botões Sim e Não)
class PainelAdmView(View):
    def __init__(self, cliente_id, produto_key, quantidade, ticket_channel):
        super().__init__(timeout=None)
        self.cliente_id = cliente_id
        self.produto_key = produto_key
        self.quantidade = quantity = quantidade
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="Aprovar (Sim)", style=discord.ButtonStyle.success, custom_id="aprovar_venda")
    async def aprovar(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Apenas administradores podem validar!", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.cliente_id)
        produto = PRODUTOS[self.produto_key]
        
        await interaction.response.defer()
        
        # Desativa os botões para evitar cliques duplos
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Entrega automática do produto se houver estoque de códigos
        if len(ESTOQUE_CODIGOS) >= self.quantidade:
            codigos_entregues = []
            for _ in range(self.quantidade):
                codigos_entregues.append(ESTOQUE_CODIGOS.pop(0))
            
            lista_txt = "\n".join(codigos_entregues)
            try:
                await member.send(f"🛍️ **Obrigado pela compra! Aqui está seu produto ({produto['nome']}):**\n```\n{lista_txt}\n```")
                await self.ticket_channel.send("✅ **Pagamento Aprovado!** O produto foi enviado diretamente na mensagem privada (DM) do cliente.")
            except discord.Forbidden:
                await self.ticket_channel.send(f"⚠️ **Aviso:** A DM do cliente está fechada! Aqui está o produto:\n```\n{lista_txt}\n```")
        else:
            await self.ticket_channel.send("⚠️ **Aviso:** O pagamento foi aceito, mas o estoque de códigos no script acabou! O ADM deve entregar o produto manualmente no chat.")

        await self.ticket_channel.send("🔒 Este ticket foi finalizado com sucesso.")
        ID_CANAL_LOG_VENDAS = 1562244870117130301  
        canal_vendas = interaction.client.get_channel(ID_CANAL_LOG_VENDAS)
        
        if canal_vendas:
            # # 1. Puxa as informações dinâmicas salvas na classe do Admin
            try:
                produto_real = PRODUTOS[self.produto_key]
                prod_nome = produto_real["nome"]
                qtd = self.quantidade
                val_uni = produto_real["preco"]
                tot_pago = val_uni * qtd
                import utils
                dados_vendas = utils.registrar_venda_total(prod_nome, qtd, tot_pago)

            except Exception as e:
                print(f"❌ ERRO INVISÍVEL DA VENDA: {e}")
                prod_nome = "Produto Adquirido"
                qtd = 1
                val_uni = 0.0
                tot_pago = 0.0
                

            embed_comprovante = discord.Embed(title="🛒 Venda Realizada com Sucesso!", color=0x00ff00)
            embed_comprovante.add_field(name="Produto:", value=prod_nome, inline=False)
            embed_comprovante.add_field(name="Quantidade:", value=f"**{qtd}x**", inline=True)
            embed_comprovante.add_field(name="Valor Unitário:", value=f"R$ {val_uni:.2f}", inline=True)
            embed_comprovante.add_field(name="Total Pago:", value=f"**R$ {tot_pago:.2f}**", inline=False)
            embed_comprovante.add_field(name="Comprador:", value=f"<@{self.cliente_id}>", inline=False)
            embed_comprovante.set_footer(text="Obrigado pela preferência! Compre você também.")
            await canal_vendas.send(embed=embed_comprovante)

        asyncio.create_task(deletar_canal_com_atraso(self.ticket_channel, 120))



    @discord.ui.button(label="Recusar (Não)", style=discord.ButtonStyle.danger, custom_id="recusar_venda")
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Apenas administradores podem recusar!", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        await self.ticket_channel.send("❌ **Pagamento Recusado.** O comprovante enviado não foi localizado em nosso banco ou o valor está incorreto.")
        await self.ticket_channel.send("🔒 **Este ticket foi encerrado e será apagado automaticamente em 20 minutos.**")
        # Linha 142 (ou próxima) - Caso o cliente suma por 20 minutos
        asyncio.create_task(deletar_canal_com_atraso(self.ticket_channel, 1200))



# Painel Interativo de Quantidade dentro do Ticket (+ e -)
class PainelQuantidadeView(View):
    def __init__(self, cliente_id, produto_key):
        super().__init__(timeout=None)
        self.cliente_id = cliente_id
        self.produto_key = produto_key
        self.quantidade = 1

    def gerar_embed(self):
        produto = PRODUTOS[self.produto_key]
        total = produto["preco"] * self.quantidade

        
        embed = discord.Embed(title="🛒 Detalhes do seu Pedido", color=0x00ff00)
        embed.add_field(name="Produto:", value=produto["nome"], inline=False)
        embed.add_field(name="Quantidade:", value=f"**{self.quantidade}x**", inline=True)
        embed.add_field(name="Valor Unitário:", value=f"R$ {produto['preco']:.2f}", inline=True)
        embed.add_field(name="Total a Pagar:", value=f"**R$ {total:.2f}**", inline=False)
        embed.add_field(name="PIX PARA TRANSFERÊNCIA:", value=f"Escaneie o QR Code abaixo para efetuar o pagamento.\n\n**Nome:** {NOME_DONO_PIX}", inline=False)
        embed.set_footer(text="Faça o Pix e clique no botão abaixo para enviar o comprovante no chat.")
        embed.set_image(url="https://media.discordapp.net/attachments/1561737248716623913/1562237250908192911/qrcode-pix.png?ex=6ad9eb11&is=6ad89991&hm=950687d644e4ff8f9336ccae58728050ee1e0759a16b671f65a6e609a3de5ba1&=&format=webp&quality=lossless&width=320&height=320")
        return embed

    @discord.ui.button(label="-", style=discord.ButtonStyle.secondary, custom_id="diminuir_qtd")
    async def diminuir(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.cliente_id:
            await interaction.response.send_message("Você não pode alterar este carrinho.", ephemeral=True)
            return
        if self.quantidade > 1:
            self.quantidade - 1
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="+", style=discord.ButtonStyle.secondary, custom_id="aumentar_qtd")
    async def aumentar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.cliente_id:
            await interaction.response.send_message("Você não pode alterar este carrinho.", ephemeral=True)
            return
        self.quantidade += 1
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Enviar Comprovante", style=discord.ButtonStyle.primary, custom_id="chamar_adm")
    async def enviar_comprovante(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.cliente_id:
            await interaction.response.send_message("Você não pode interagir aqui.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        embed_adm = discord.Embed(
            title="🔔 Pagamento Aguardando Verificação", 
            description=f"O cliente {interaction.user.mention} enviou um comprovante.\nConfira o extrato do seu banco antes de tomar uma ação.",
            color=0xffa500
        )
        view_adm = PainelAdmView(self.cliente_id, self.produto_key, self.quantidade, interaction.channel)
        await interaction.channel.send(content="@everyone", embed=embed_adm, view=view_adm)

# Menu Dropdown Inicial da Loja
class DropdownProdutos(Select):
    def __init__(self):
                options = [
            discord.SelectOption(label="1K Cash", description="R$ 3,50 - Adicione 1K de cash à sua conta", value="cash_1k", emoji="💵"),
            discord.SelectOption(label="5K Cash", description="R$ 17,50 - Adicione 5K de cash à sua conta", value="cash_5k", emoji="💵"),
            discord.SelectOption(label="10K Cash", description="R$ 35,00 - Adicione 10K de cash à sua conta", value="cash_10k", emoji="💵"),
            discord.SelectOption(label="20K Cash", description="R$ 70,00 - Adicione 20K de cash à sua conta", value="cash_20k", emoji="💵"),
            discord.SelectOption(label="30K Cash", description="R$ 105,00 - Adicione 30K de cash à sua conta", value="cash_30k", emoji="💵"),
            discord.SelectOption(label="40K Cash", description="R$ 140,00 - Adicione 40K de cash à sua conta", value="cash_40k", emoji="💵"),
            discord.SelectOption(label="50K Cash", description="R$ 175,00 - Adicione 50K de cash à sua conta", value="cash_50k", emoji="💵"),
            discord.SelectOption(label="Passe", description="R$ 25,00 - Desbloqueie o Passe", value="passe", emoji="🎫"),
            discord.SelectOption(label="5 Caixas", description="R$ 10,00 - Combo com 5 caixas secretas", value="caixas_5", emoji="📦"),
        ] 
                super().__init__(placeholder="o que deseja comprar...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        categoria = discord.utils.get(guild.categories, name="🛒 LOJA TICKETS")
        if not categoria:
            categoria = await guild.create_category("🛒 LOJA TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        nome_canal = f"carrinho-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(name=nome_canal, category=categoria, overwrites=overwrites)
        
        await interaction.response.send_message(f"✅ Seu carrinho foi aberto em {ticket_channel.mention}!", ephemeral=True)

        view_quantidade = PainelQuantidadeView(interaction.user.id, self.values[0])
        embed_pagamento = view_quantidade.gerar_embed()
        await ticket_channel.send(embed=embed_pagamento, view=view_quantidade)


    

class LojaInicialView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DropdownProdutos())

@bot.event
async def on_ready():
    print(f"🤖 Bot {bot.user.name} está online e pronto para vender com os novos preços!")

@bot.command()
@commands.has_permissions(administrator=True)
async def configurar_loja(ctx):
    embed = discord.Embed(
        title="🛒 CENTRAL DE VENDAS AUTOMÁTICA",
        description="Escolha um dos nossos pacotes digitais no menu abaixo para iniciar o seu pedido via Pix de forma 100% segura.",
        color=0x2f3136
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1561737248716623913/1562432849183907891/939def57-5d53-4701-b1fb-d060ef8affb3.png?ex=6ad9f87b&is=6ad8a6fb&hm=0cd790a5afb1e3447436a58ee4383ce215eb5756b3d2bef722806a2672c93495")
    await ctx.send(embed=embed, view=LojaInicialView())



@bot.command(name="vendas")
@commands.has_permissions(administrator=True)
async def ver_vendas(ctx):
    import os
    import json
    
    ARQUIVO_ESTATISTICAS = "estatisticas_vendas.json"
    
    if not os.path.exists(ARQUIVO_ESTATISTICAS):
        await ctx.send("❌ Nenhuma venda foi registrada no sistema ainda!")
        return
        
    with open(ARQUIVO_ESTATISTICAS, "r", encoding="utf-8") as f:
        dados_vendas = json.load(f)
        
    if not dados_vendas:
        await ctx.send("❌ O arquivo de estatísticas está vazio!")
        return

    embed_relatorio = discord.Embed(title="📊 Painel Geral de Vendas Acumuladas", color=0x0000ff)
    valor_final_loja = 0.0
    
    for nome_do_prod, info in dados_vendas.items():
        vendas_acumuladas = info["vendas_feitas"]
        total_produto = info["total_faturado"]
        valor_final_loja += total_produto
        
        embed_relatorio.add_field(
            name=f"📦 {nome_do_prod}",
            value=f"• Total vendido: **{vendas_acumuladas}x**\n• Arrecadado: **R$ {total_produto:.2f}**",
            inline=False
        )
    
    embed_relatorio.add_field(name="💰 FATURAMENTO TOTAL DA LOJA:", value=f"🍀 **R$ {valor_final_loja:.2f}**", inline=False)
    embed_relatorio.set_footer(text="Relatório gerado sob demanda da administração.")
    
    await ctx.send(embed=embed_relatorio)

@ver_vendas.error
async def ver_vendas_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Apenas administradores podem usar este comando!")


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN) 
