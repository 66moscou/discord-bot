import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")
CARGO_MEMBRO_ID = 1242669440169148486
ARQUIVO_PAINEL = "painel.json"
CANAL_BOAS_VINDAS_ID = 1241248843220258888
CANAL_SAÍDA_ID = 1490923862358098115
ID_CATEGORIA_CALL= 1255722186333749322

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
        name=f"by 💢 66moscou | Membros {total_servidores} / {total_membros}"
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


# ================= START =================

bot.run(TOKEN)
