import discord
import os
import requests
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot allumé ! Connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(e)

# --- FONCTION POUR GÉNÉRER L'EMBED ---
def get_pokemon_embed(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.strip().lower()}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        nom = data['name'].capitalize()
        taille = data['height'] / 10  # L'API donne en décimètres, on convertit en mètres
        poids = data['weight'] / 10   # L'API donne en hectogrammes, on convertit en kg
        types = [t['type']['name'].capitalize() for t in data['types']]
        image_url = data['sprites']['front_default'] # Image du Pokémon
        
        # Création de l'Embed
        embed = discord.Embed(
            title=f"N°{data['id']} — {nom}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=image_url)
        embed.add_field(name="Type(s)", value=" / ".join(types), inline=True)
        embed.add_field(name="Taille", value=f"{taille} m", inline=True)
        embed.add_field(name="Poids", value=f"{poids} kg", inline=True)
        embed.set_footer(text="Données fournies par PokeAPI.co")
        
        return embed
    else:
        return None

# --- COMMANDES SLASH ---
@bot.tree.command(name="help", description="Affiche l'aide")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ Guide du PokéBot",
        description=(
            "Bienvenue dans l'encyclopédie Pokémon ! Voici comment utiliser le bot :\n\n"
            "**Commandes Slash (/) :**\n"
            "• `/type <nom>` : Affiche les forces et faiblesses d'un type (ex: `/type feu`)\n"
            "• `/help` : Affiche ce message d'aide\n"
            "• `/credits` : Affiche les crédits du bot\n\n"
            "**Commandes Classiques (!) :**\n"
            "• `!poke <nom>` : Stats d'un Pokémon (ex: `!poke pikachu`)\n"
            "• `!poke <id>` : Cherche par numéro (ex: `!poke 25`)\n\n"
            "**Exemples :**\n"
            "└ `/type eau` -> Voir les counters du type Eau.\n"
            "└ `!poke charizard` -> Infos sur Dracaufeu."
        ),
        color=discord.Color.red()
    )
    embed.set_thumbnail(url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png")
    embed.set_footer(text="Bot créé par Crazymilien")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="credits", description="Affiche les crédits")
async def credit_command(interaction: discord.Interaction):
    await interaction.response.send_message("Bot créé par Crazymilien")

# --- GESTION DES MESSAGES (!poke) ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower().startswith('!poke '):
        nom_pokemon = message.content[6:].strip()
        
        if nom_pokemon:
            embed_resultat = get_pokemon_embed(nom_pokemon)
            
            if embed_resultat:
                await message.channel.send(embed=embed_resultat)
            else:
                await message.channel.send(f"⚠️ Impossible de trouver le Pokémon '**{nom_pokemon}**'.")
        else:
            await message.channel.send("Tu dois préciser un nom, ex: `!poke pikachu`")

    # Important pour que les autres commandes fonctionnent
    await bot.process_commands(message)

@bot.tree.command(name="type", description="Affiche les forces et faiblesses d'un type")
@discord.app_commands.describe(element="Le type à analyser (ex: Feu, Eau, Dragon...)")
async def type_command(interaction: discord.Interaction, element: str):
    # Dictionnaire des relations (Version simplifiée pour l'exemple)
    # Format: "Type": [Super Efficace contre, Faible contre]
    type_chart = {
        "feu": {"win": "Plante, Glace, Insecte, Acier", "lose": "Eau, Sol, Roche"},
        "eau": {"win": "Feu, Sol, Roche", "lose": "Plante, Électrik"},
        "plante": {"win": "Eau, Sol, Roche", "lose": "Feu, Glace, Poison, Vol, Insecte"},
        "electrik": {"win": "Eau, Vol", "lose": "Sol"},
        "glace": {"win": "Plante, Sol, Vol, Dragon", "lose": "Feu, Combat, Roche, Acier"},
        "combat": {"win": "Normal, Glace, Roche, Ténèbres, Acier", "lose": "Vol, Psy, Fée"},
        "poison": {"win": "Plante, Fée", "lose": "Sol, Psy"},
        "sol": {"win": "Feu, Électrik, Poison, Roche, Acier", "lose": "Eau, Plante, Glace"},
        "vol": {"win": "Plante, Combat, Insecte", "lose": "Électrik, Glace, Roche"},
        "psy": {"win": "Combat, Poison", "lose": "Insecte, Spectre, Ténèbres"},
        "insecte": {"win": "Plante, Psy, Ténèbres", "lose": "Feu, Vol, Roche"},
        "roche": {"win": "Feu, Glace, Vol, Insecte", "lose": "Eau, Plante, Combat, Sol, Acier"},
        "spectre": {"win": "Psy, Spectre", "lose": "Spectre, Ténèbres"},
        "dragon": {"win": "Dragon", "lose": "Glace, Dragon, Fée"},
        "tenebres": {"win": "Psy, Spectre", "lose": "Combat, Insecte, Fée"},
        "acier": {"win": "Glace, Roche, Fée", "lose": "Feu, Combat, Sol"},
        "fee": {"win": "Combat, Dragon, Ténèbres", "lose": "Poison, Acier"},
        "normal": {"win": "Rien", "lose": "Combat"}
    }

    key = element.lower()
    if key in type_chart:
        data = type_chart[key]
        embed = discord.Embed(
            title=f"Analyse du type {element.capitalize()}",
            color=discord.Color.blue()
        )
        embed.add_field(name="✅ Fort contre", value=data["win"], inline=False)
        embed.add_field(name="❌ Faible contre", value=data["lose"], inline=False)
        embed.set_footer(text="Astuce : Utilise des attaques super efficaces pour doubler les dégâts !")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"⚠️ Le type `{element}` n'existe pas. Réessaie avec un type valide (ex: Feu, Eau...).", ephemeral=True)

@bot.tree.command(name="credits", description="Affiche les crédits")
async def credit_command(interaction: discord.Interaction):
    await interaction.response.send_message("Bot créé par Crazymilien")

bot.run(os.getenv('DISCORD_TOKEN'))