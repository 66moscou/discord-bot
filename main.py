import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import io

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")
CARGO_MEMBRO_ID = 1242669440169148486
ARQUIVO_PAINEL = "painel.json"
CANAL_BOAS_VINDAS_ID = 1241248843220258888
CANAL_SAÍDA_ID = 1490923862358098115
ID_CATEGORIA_CALL= 1255722186333749322

# ===== TICKETS =====
tickets_abertos = {}

# ===== CARGOS DE SETAGEM =====
CARGO_SET1 = 1307723016649576548
CARGO_SET2 = 1216962925810552842
CARGO_SET3 = 1240052551454425108
CARGO_SET4 = 1239400472872222820
CARGO_SET5 = 1307723431068045354
CARGO_SET6 = 1242638261000732762
CARGO_SET7 = 1307721831947571281
CARGO_SET8 = 1244488869769121832
CARGO_SET9 = 1441219402883399833

CARGO_ATENDIMENTO = 1255721912588304516

CATEGORIA_TICKET_SUPORTE = 1491973977919193189
CATEGORIA_TICKET_COMPRA = 1491974004964196352
CATEGORIA_TICKET_DUVIDAS = 1491974034991087750

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ================= SISTEMA DE ARQUIVO =================

def salvar_painel(msg_id, canal_id):
    with open(ARQUIVO_PAINEL, "w") as f:
        json.dump({"message_id": msg_id, "channel_id": canal_id}, f)


def carregar_painel():
    if not os.path.exists(ARQUIVO_PAINEL):
        return None
    with open(ARQUIVO_PAINEL, "r") as f:
        return json.load(f)


def apagar_painel():
    if os.path.exists(ARQUIVO_PAINEL):
        os.remove(ARQUIVO_PAINEL)


# ================= BOTÃO VERIFICAÇÃO =================

class PainelVerificacao(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificar",
        style=discord.ButtonStyle.green,
        custom_id="botao_verificar_permanente"
    )
    async def verificar(self, interaction: discord.Interaction, button: discord.ui.Button):

        cargo = interaction.guild.get_role(CARGO_MEMBRO_ID)

        if cargo is None:
            await interaction.response.send_message(
                "❌ Cargo não encontrado.",
                ephemeral=True
            )
            return

        if cargo in interaction.user.roles:
            await interaction.response.send_message(
                "✔ Você já está verificado!",
                ephemeral=True
            )
            return

        await interaction.user.add_roles(cargo)

        await interaction.response.send_message(
            "🎉 Você foi verificado com sucesso!",
            ephemeral=True
        )


# ============== LOOP DE STATUS ==============

from discord.ext import tasks

@tasks.loop(seconds=15)
async def atualizar_status():
    total_membros = sum(guild.member_count for guild in bot.guilds)
    total_servidores = len(bot.guilds)

    status = discord.Game(
        name=f"by 💢 66moscou | Membros: {total_servidores} / {total_membros}"
    )

    await bot.change_presence(
        status=discord.Status.online,
        activity=status
    )

# ================= ON_READY =================

@bot.event
async def on_ready():

    # 👇 REGISTRA TODAS AS VIEWS PERSISTENTES
    bot.add_view(PainelVerificacao())
    bot.add_view(ViewSetagem())
    bot.add_view(ViewCallBooster())
    bot.add_view(ViewTicket())
    bot.add_view(ViewStaffTicket())
    bot.add_view(PainelAdmin())

    # 🔥 ESSA LINHA É O QUE FALTA
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} comandos sincronizados!")
    except Exception as e:
        print(e)
    
    # 👇 INICIA O STATUS DINÂMICO
    if not atualizar_status.is_running():
        atualizar_status.start()

    print(f"✅ Bot online como {bot.user}")


# ================= EVENTOS ENTRADA =================

@bot.event
async def on_member_join(member):
    canal = bot.get_channel(CANAL_BOAS_VINDAS_ID)

    if canal:
        embed = discord.Embed(
            title="🎉 Bem-vindo ao servidor!",
            description=f"***Olá*** {member.mention}, ***seja bem-vindo(a) a*** **{member.guild.name} !**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await canal.send(embed=embed)


# ================= EVENTO DE SAÍDA =================

@bot.event
async def on_member_remove(member):
    canal = bot.get_channel(CANAL_SAÍDA_ID)

    if canal:
        embed = discord.Embed(
            title="👋 Um membro saiu do servidor",
            description=f"**Menos um zé povin, {member.mention} saiu da {member.guild.name} !**",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Esperamos te ver novamente!")

        await canal.send(embed=embed)


# ================= /PAINEL =================

@bot.tree.command(name="painel", description="Criar painel de verificação")
@app_commands.default_permissions(administrator=True)
async def painel(interaction: discord.Interaction):

    if carregar_painel():
        await interaction.response.send_message(
            "⚠ Já existe um painel ativo.",
            ephemeral=True
        )
        return

    # 👇 evita erro de interação
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🔐 Verificação",
        description="Clique no botão abaixo para se verificar.",
        color=discord.Color.blue()
    )

    msg = await interaction.channel.send(
        embed=embed,
        view=PainelVerificacao()
    )

    salvar_painel(msg.id, interaction.channel.id)

    await interaction.followup.send(
        "✅ Painel criado com sucesso!",
        ephemeral=True
    )


# ================= /REMOVERPAINEL =================

@bot.tree.command(name="removerpainel", description="Remover painel de verificação")
@app_commands.default_permissions(administrator=True)
async def removerpainel(interaction: discord.Interaction):

    dados = carregar_painel()

    if not dados:
        await interaction.response.send_message(
            "❌ Não existe painel salvo.",
            ephemeral=True
        )
        return

    canal = bot.get_channel(dados["channel_id"])

    try:
        msg = await canal.fetch_message(dados["message_id"])
        await msg.delete()
    except:
        pass

    apagar_painel()

    await interaction.response.send_message(
        "🗑 Painel removido!",
        ephemeral=True
    )


# ================= /CLEAR MODERNO =================

@bot.tree.command(name="clear", description="Apagar mensagens do canal")
@app_commands.describe(
    quantidade="Número de mensagens para apagar (ignorar se usar all)",
    modo="Use 'all' para limpar o máximo possível"
)
async def clear(
    interaction: discord.Interaction,
    quantidade: int = None,
    modo: str = None
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser admin para usar esse comando.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    # ===== CLEAR ALL =====
    if modo == "all":
        total = 0

        while True:
            deleted = await interaction.channel.purge(limit=100)
            if not deleted:
                break
            total += len(deleted)
            if len(deleted) < 100:
                break

        await interaction.followup.send(
            f"🧹 Canal limpo! {total} mensagens apagadas.",
            ephemeral=True
        )
        return

    # ===== CLEAR NORMAL =====
    if quantidade and quantidade > 0:
        deleted = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(
            f"🧹 {len(deleted)} mensagens apagadas.",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            "❌ Use `/clear quantidade:10` ou `/clear modo:all`",
            ephemeral=True
        )


# ================= /BAN =================

@bot.tree.command(name="ban", description="Banir um membro do servidor")
@app_commands.describe(
    membro="Membro que será banido",
    motivo="Motivo do banimento"
)
async def ban(
    interaction: discord.Interaction,
    membro: discord.Member,
    motivo: str = "Sem motivo informado"
):

    # verifica permissão
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser admin para usar este comando.",
            ephemeral=True
        )
        return

    # impede auto-ban
    if membro == interaction.user:
        await interaction.response.send_message(
            "❌ Você não pode se banir.",
            ephemeral=True
        )
        return

    # impede banir cargo maior
    if membro.top_role >= interaction.user.top_role:
        await interaction.response.send_message(
            "❌ Você não pode banir alguém com cargo igual ou maior.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        # tenta mandar DM
        try:
            await membro.send(
                f"🚫 Você foi banido do servidor **{interaction.guild.name}**.\n"
                f"Motivo: {motivo}"
            )
        except:
            pass

        await membro.ban(reason=motivo)

        await interaction.followup.send(
            f"🔨 {membro} foi banido.\nMotivo: {motivo}",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ Não tenho permissão para banir este usuário.",
            ephemeral=True
        )


        # ================= /CALLBOOSTER =================

@bot.tree.command(name="callbooster", description="Criar painel de Call Booster")
@app_commands.default_permissions(administrator=True)
async def callbooster(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎧 Call Booster",
        description="Clique no botão abaixo para criar seu canal de voz personalizado.",
        color=discord.Color.dark_purple()
    )

    # envia o painel no canal
    await interaction.channel.send(
        embed=embed,
        view=ViewCallBooster()
    )

    # responde o comando só para quem usou
    await interaction.response.send_message(
        "✅ Painel enviado.",
        ephemeral=True
    )


# ================= SISTEMA CALL BOOSTER AVANÇADO =================

class ModalCriarCall(discord.ui.Modal, title="Criar Canal de Voz"):

    nome = discord.ui.TextInput(
        label="Nome da Call",
        placeholder="Ex: Call dos Booster",
        max_length=40
    )

    async def on_submit(self, interaction: discord.Interaction):

        mensagem = "🔐 Agora selecione o cargo que poderá entrar:"

        if interaction.response.is_done():
            await interaction.followup.send(
                mensagem,
                view=ViewSelecionarCargo(self.nome.value),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                mensagem,
                view=ViewSelecionarCargo(self.nome.value),
                ephemeral=True
            )

class ViewSelecionarCargo(discord.ui.View):
    def __init__(self, nome_canal):
        super().__init__(timeout=None)
        self.add_item(SelectCargo(nome_canal))

class SelectCargo(discord.ui.RoleSelect):

    def __init__(self, nome_canal):
        super().__init__(
            placeholder="Selecione o cargo permitido",
            min_values=1,
            max_values=1
        )
        self.nome_canal = nome_canal

    async def callback(self, interaction: discord.Interaction):

        cargo = self.values[0]
        guild = interaction.guild
        categoria = guild.get_channel(ID_CATEGORIA_CALL)

        if not categoria:
            await interaction.response.send_message(
                "❌ Categoria não encontrada.",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False),
            cargo: discord.PermissionOverwrite(connect=True),
            interaction.user: discord.PermissionOverwrite(
                connect=True,
                manage_channels=True,
                mute_members=True,
                move_members=True
            )
        }

        canal = await guild.create_voice_channel(
            name=self.nome_canal,
            category=categoria,
            overwrites=overwrites
        )

        # envia painel de controle na call
        await canal.send(
            "🎛 **Controles da Call**",
            view=ViewControleCall(canal.id, interaction.user.id)
        )

        msg = f"✅ Call criada: {canal.mention}"

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


# ================= CONTROLES DA CALL =================

class ViewControleCall(discord.ui.View):

    def __init__(self, canal_id, dono_id):
        super().__init__(timeout=None)
        self.canal_id = canal_id
        self.dono_id = dono_id

    async def verificar_dono(self, interaction):

        if interaction.user.id != self.dono_id:
            await interaction.response.send_message(
                "❌ Apenas quem criou a call pode usar isso.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="🔒 Limitar", style=discord.ButtonStyle.gray)
    async def limitar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.verificar_dono(interaction):
            return

        canal = interaction.guild.get_channel(self.canal_id)

        if canal.user_limit == 0:
            await canal.edit(user_limit=5)
            msg = "🔒 Canal limitado a 5 usuários."
        else:
            await canal.edit(user_limit=0)
            msg = "🔓 Limite removido."

        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="✏ Renomear", style=discord.ButtonStyle.blurple)
    async def renomear(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.verificar_dono(interaction):
            return

        class ModalRenomear(discord.ui.Modal, title="Renomear canal"):

            nome = discord.ui.TextInput(label="Novo nome")

            async def on_submit(self2, interaction2: discord.Interaction):

                canal = interaction.guild.get_channel(self.canal_id)
                await canal.edit(name=self2.nome.value)

                await interaction2.response.send_message(
                    "✅ Canal renomeado.",
                    ephemeral=True
                )

        await interaction.response.send_modal(ModalRenomear())

    @discord.ui.button(label="🗑 Deletar", style=discord.ButtonStyle.red)
    async def deletar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.verificar_dono(interaction):
            return

        canal = interaction.guild.get_channel(self.canal_id)

    # responde ANTES de deletar
        await interaction.response.send_message(
            "🗑 Deletando canal...",
                ephemeral=True
        )

        await canal.delete()


# ================= BOTÃO CRIAR CANAL =================

class ViewCallBooster(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Criar Canal",
        style=discord.ButtonStyle.green,
        custom_id="botao_call_booster"
    )
    async def criar_canal(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.response.is_done():
            await interaction.followup.send(
                "Abrindo formulário...",
                ephemeral=True
            )
            await interaction.followup.send_modal(ModalCriarCall())
        else:
            await interaction.response.send_modal(ModalCriarCall())


# ================= /SETAGEM =================

@bot.tree.command(name="setagem", description="Criar painel de setagem de cargos")
@app_commands.default_permissions(administrator=True)
async def setagem(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎭 Escolha seus cargos",
        description="Selecione abaixo os cargos que deseja receber.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed,
        view=ViewSetagem()
    )


# ================= SISTEMA DE SETAGEM DE CARGOS =================

class SelectCargos(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label="Once Human", value=str(CARGO_SET1)),
            discord.SelectOption(label="Cod - MWIII", value=str(CARGO_SET2)),
            discord.SelectOption(label="The Forest", value=str(CARGO_SET3)),
            discord.SelectOption(label="FiveM", value=str(CARGO_SET4)),
            discord.SelectOption(label="Crossfire", value=str(CARGO_SET5)),
            discord.SelectOption(label="BloodStrike", value=str(CARGO_SET6)),
            discord.SelectOption(label="Minecraft", value=str(CARGO_SET7)),
            discord.SelectOption(label="Fortnite", value=str(CARGO_SET8)),
            discord.SelectOption(label="Valorant", value=str(CARGO_SET9)),
        ]

        super().__init__(
            placeholder="Selecione os cargos que deseja...",
            min_values=1,
            max_values=9,
            options=options,
            custom_id="menu_setagem_cargos"
        )

    async def callback(self, interaction: discord.Interaction):

        membro = interaction.user
        adicionados = 0

        for cargo_id in self.values:

            cargo = interaction.guild.get_role(int(cargo_id))

            # 👇 evita erro se cargo não existir
            if cargo is None:
                continue

            if cargo not in membro.roles:
                await membro.add_roles(cargo)
                adicionados += 1

        await interaction.response.send_message(
            f"✅ {adicionados} cargos adicionados!",
            ephemeral=True
        )


class ViewSetagem(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectCargos())


# ================= SISTEMA DE TICKET =================

async def criar_ticket(interaction, nome, categoria_id):
    guild = interaction.guild
    user = interaction.user

    # 🚫 BLOQUEIO DE TICKET DUPLICADO
    if user.id in tickets_abertos:
        canal_existente = tickets_abertos[user.id]
        await interaction.response.send_message(
            f"❌ Você já possui um ticket aberto: {canal_existente.mention}",
            ephemeral=True
        )
        return

    # 👇 COLOCA AQUI
    staff_role = guild.get_role(CARGO_ATENDIMENTO)
    categoria = guild.get_channel(categoria_id)

    if staff_role is None:
        await interaction.response.send_message(
            "❌ Cargo de atendimento não encontrado.",
            ephemeral=True
        )
        return

    if categoria is None:
        await interaction.response.send_message(
            "❌ Categoria não encontrada.",
            ephemeral=True
        )
        return

    # 👇 resto do código continua
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),

        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True
        ),

        staff_role: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True
        ),

        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True
        )
    }

    canal = await guild.create_text_channel(
        name=f"{nome}-{user.name}".replace(" ", "-").lower(),
        category=categoria,
        overwrites=overwrites
    )

    # ✅ SALVA QUE O USUÁRIO TEM TICKET ABERTO
    tickets_abertos[user.id] = canal

    embed = discord.Embed(
    title="🎫 Ticket aberto com sucesso",
    description=(
        f"👋 Olá {user.mention}\n\n"
        f"📌 **Categoria:** {nome.capitalize()}\n"
        f"📊 **Status:** 🟡 Aguardando atendimento\n\n"
        f"{staff_role.mention} irá assumir este ticket em breve.\n\n"
        f"💬 Descreva seu problema com detalhes."
    ),
    color=discord.Color.orange()
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"ID: {user.id}")

    msg = await canal.send(
        embed=embed,
        view=ViewStaffTicket(msg.id)
    )

    await interaction.response.send_message(
        f"✅ Ticket criado: {canal.mention}",
        ephemeral=True
    )


# ===== BOTÕES DE TICKET =====
class ViewTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Suporte", emoji="🛠️", style=discord.ButtonStyle.primary, custom_id="ticket_suporte")
    async def suporte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await criar_ticket(interaction, "suporte", CATEGORIA_TICKET_SUPORTE)

    @discord.ui.button(label="Compra", emoji="💰", style=discord.ButtonStyle.success, custom_id="ticket_compra")
    async def compra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await criar_ticket(interaction, "compra", CATEGORIA_TICKET_COMPRA)

    @discord.ui.button(label="Dúvidas", emoji="❓", style=discord.ButtonStyle.secondary, custom_id="ticket_duvidas")
    async def duvidas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await criar_ticket(interaction, "duvidas", CATEGORIA_TICKET_DUVIDAS)


# ===== PAINEL STAFF =====
class ViewStaffTicket(discord.ui.View):
    def __init__(self, message_id=None):
        super().__init__(timeout=None)
        self.assumido_por = None
        self.message_id = message_id

    def is_staff(self, interaction):
        return any(role.id == CARGO_ATENDIMENTO for role in interaction.user.roles)

    @discord.ui.button(label="Assumir", emoji="👤", style=discord.ButtonStyle.success, custom_id="staff_assumir")
    async def assumir(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not self.is_staff(interaction):
            await interaction.response.send_message(
                "❌ Apenas staff pode usar isso.",
                ephemeral=True
            )
            return

        if self.assumido_por:
            await interaction.response.send_message(
                f"⚠ Já assumido por {self.assumido_por.mention}",
                ephemeral=True
            )
            return

        self.assumido_por = interaction.user

        # 👇 PEGA A MENSAGEM ORIGINAL
        try:
            msg = await interaction.channel.fetch_message(self.message_id)
            embed = msg.embeds[0]

            # 👇 ALTERA O TEXTO
            nova_desc = embed.description.replace(
                "🟡 Aguardando atendimento",
                f"🟢 Atendido por {interaction.user.mention}"
            )

            embed.description = nova_desc
            embed.color = discord.Color.green()

            await msg.edit(embed=embed)

        except Exception as e:
            print("Erro ao editar embed:", e)

        await interaction.response.send_message(
            f"👤 Ticket assumido por {interaction.user.mention}"
        )

        class ModalRenomear(discord.ui.Modal, title="Renomear Ticket"):
            nome = discord.ui.TextInput(label="Novo nome do ticket")

            async def on_submit(self2, interaction2: discord.Interaction):
                await interaction.channel.edit(name=self2.nome.value)
                await interaction2.response.send_message("✅ Nome alterado.", ephemeral=True)

        await interaction.response.send_modal(ModalRenomear())

    @discord.ui.button(label="Finalizar", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="staff_finalizar")
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not self.is_staff(interaction):
            await interaction.response.send_message(
                "❌ Apenas staff pode usar isso.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("📁 Gerando transcript...", ephemeral=True)

        channel = interaction.channel

        mensagens = []
        async for msg in channel.history(limit=None, oldest_first=True):
            data = msg.created_at.strftime("%d/%m/%Y %H:%M")
            conteudo = msg.content if msg.content else "[sem texto]"

            if msg.attachments:
                conteudo += " [anexo]"
            if msg.embeds:
                conteudo += " [embed]"

            mensagens.append(f"[{data}] {msg.author}: {conteudo}")

        transcript = "\n".join(mensagens)

        arquivo = discord.File(
            io.StringIO(transcript),
            filename=f"transcript-{channel.name}.txt"
        )

        try:
            await interaction.user.send(
                f"📄 Transcript do ticket {channel.name}",
                file=arquivo
            )
        except:
            pass

        for user_id, canal in list(tickets_abertos.items()):
            if canal.id == channel.id:
                del tickets_abertos[user_id]
                break

        await channel.send("🔒 Ticket encerrado.")
        await channel.delete()


# ========= COMANDO /TICKET =========
@bot.tree.command(name="ticket", description="Abrir painel de ticket")
async def ticket(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🎫 Central de Atendimento",
        description=(
            "Selecione abaixo o tipo de atendimento que você precisa.\n\n"
            "🛠️ **Suporte** - Problemas / ajuda\n"
            "💰 **Compra** - Produtos / serviços\n"
            "❓ **Dúvidas** - Perguntas gerais\n\n"
            "📌 *Nossa equipe responderá o mais rápido possível.*"
        ),
        color=discord.Color.from_rgb(35, 39, 42)
    )

    embed.set_footer(text="Sistema de tickets • 66moscou")
    
    await interaction.channel.send(
        embed=embed,
        view=ViewTicket()
    )

    await interaction.followup.send(
        "✅ Painel enviado.",
        ephemeral=True
    )


# ======== PAINEL ADMINISTRAÇÃO / CONFIG =======
class PainelAdmin(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def check_admin(self, interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas administradores podem usar isso.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="🧹 Limpar Chat", style=discord.ButtonStyle.secondary, custom_id="admin_clear")
    async def clear(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.check_admin(interaction):
            return

        await interaction.channel.purge(limit=50)

        await interaction.response.send_message(
            "🧹 50 mensagens apagadas.",
            ephemeral=True
        )

    @discord.ui.button(label="🔨 Banir", style=discord.ButtonStyle.danger, custom_id="admin_ban")
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.check_admin(interaction):
            return

        class ModalBan(discord.ui.Modal, title="Banir usuário"):
            user_id = discord.ui.TextInput(label="ID do usuário")
            motivo = discord.ui.TextInput(label="Motivo", required=False)

            async def on_submit(self2, interaction2: discord.Interaction):

                membro = interaction2.guild.get_member(int(self2.user_id.value))

                if not membro:
                    await interaction2.response.send_message("❌ Usuário não encontrado.", ephemeral=True)
                    return

                await membro.ban(reason=self2.motivo.value or "Sem motivo")

                await interaction2.response.send_message(
                    f"🔨 {membro} foi banido.",
                    ephemeral=True
                )

        await interaction.response.send_modal(ModalBan())

    @discord.ui.button(label="🎫 Ticket", style=discord.ButtonStyle.primary, custom_id="admin_ticket")
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.check_admin(interaction):
            return

        embed = discord.Embed(
            title="🎫 Sistema de Tickets",
            description="Escolha uma categoria abaixo:",
            color=discord.Color.blue()
        )

        await interaction.channel.send(embed=embed, view=ViewTicket())

        await interaction.response.send_message("✅ Painel de ticket enviado.", ephemeral=True)

    @discord.ui.button(label="🔐 Verificação", style=discord.ButtonStyle.success, custom_id="admin_verificacao")
    async def verificacao(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not await self.check_admin(interaction):
            return

        embed = discord.Embed(
            title="🔐 Verificação",
            description="Clique no botão abaixo para se verificar.",
            color=discord.Color.green()
        )

        await interaction.channel.send(embed=embed, view=PainelVerificacao())

        await interaction.response.send_message("✅ Painel de verificação enviado.", ephemeral=True)


@bot.tree.command(name="admin", description="Abrir painel administrativo")
@app_commands.default_permissions(administrator=True)
async def admin(interaction: discord.Interaction):

    embed = discord.Embed(
        title="⚙️ Painel Administrativo",
        description=(
            "Use os botões abaixo para gerenciar o servidor.\n\n"
            "🧹 Limpeza rápida\n"
            "🔨 Moderação\n"
            "🎫 Sistema de tickets\n"
            "🔐 Verificação"
        ),
        color=discord.Color.dark_theme()
    )

    embed.set_footer(text="Sistema administrativo moderno")

    await interaction.response.send_message(
        embed=embed,
        view=PainelAdmin()
    )
    

    # ========== ABRIR PAINEL ADM ==========
    @bot.tree.command(name="admin", description="Abrir painel administrativo")
    @app_commands.default_permissions(administrator=True)
    async def admin(interaction: discord.Interaction):

        embed = discord.Embed(
            title="⚙️ Painel Administrativo",
            description=(
                "Use os botões abaixo para gerenciar o servidor.\n\n"
                "🧹 Limpeza rápida\n"
                "🔨 Moderação\n"
                "🎫 Sistema de tickets\n"
                "🔐 Verificação"
            ),
            color=discord.Color.dark_theme()
        )

        embed.set_footer(text="Sistema administrativo moderno")

        await interaction.response.send_message(
            embed=embed,
            view=PainelAdmin()
        )


# ================= START =================

bot.run(TOKEN)
