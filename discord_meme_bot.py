import os
import discord
from discord.ext import commands
from gradiomeme_agent_api import GradioMemeAgent
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get tokens from environment variables
token = os.getenv('DISCORD_TOKEN', "")
hf_token = os.getenv('HF_TOKEN', "")

# Initialize the bot with ALL intents
intents = discord.Intents.all()  # Use all intents to ensure we can detect commands
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize GradioMemeAgent
print("Setting up Gradio Meme Agent...")
meme_finder = GradioMemeAgent()
print("Gradio Meme Agent ready!")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (id: {guild.id})')
        # Print bot's permissions in this guild
        bot_member = guild.get_member(bot.user.id)
        if bot_member:
            print(f'  Permissions: {bot_member.guild_permissions}')

    # Print all registered commands
    print("Registered commands:")
    for command in bot.commands:
        print(f"- {command.name}: {command.help}")

    # Print bot's activity status
    activity = discord.Game(name="!meme to get a meme")
    await bot.change_presence(activity=activity)
    print("Bot status set to: !meme to get a meme")


@bot.event
async def on_message(message):
    # Debug: Print all messages the bot can see
    print(f"Message received: {message.content} from {message.author}")

    # Check if the message is a command
    if message.content.startswith('!'):
        print(f"Command detected: {message.content}")

    # Don't respond to our own messages
    if message.author == bot.user:
        return

    # Process commands
    await bot.process_commands(message)


@bot.command(name='meme', help='Get a relevant meme based on your message or recent conversation')
async def get_meme(ctx, *, text=None):
    try:
        print(
            f"Meme command received from {ctx.author} in {ctx.guild.name}#{ctx.channel.name}")
        print(f"Command text: {text}")

        # If no text provided, use recent messages as context
        if not text:
            # Get the last 5 messages for context
            messages = []
            async for message in ctx.channel.history(limit=5):
                if message.author != bot.user:  # Don't include bot's own messages
                    messages.append(
                        f"{message.author.name}: {message.content}")
            # Reverse to get chronological order
            text = " ".join(reversed(messages))
            print(f"Using context: {text}")

        # Get meme using MemeFinder
        result = meme_finder.find_relevant_meme(text)

        # Debug the result
        print(f"Debug - Meme result: {result}")

        # Check if we have a valid result with a filename
        if result and isinstance(result, dict):
            # Get the meme path - handle both 'meme_path' and 'filename' keys
            meme_path = None
            if 'meme_path' in result:
                meme_path = result['meme_path']
            elif 'filename' in result:
                meme_path = os.path.join('data/memes', result['filename'])

            print(f"Attempting to send meme from path: {meme_path}")

            if meme_path and os.path.exists(meme_path):
                # Send the meme file
                with open(meme_path, 'rb') as f:
                    meme_file = discord.File(f)
                    message = await ctx.send(file=meme_file)
                    print(f"Meme sent successfully: {meme_path}")

                    # Add description as a follow-up message
                    description = ""
                    if 'description' in result:
                        description = f"Description: {result['description']}"
                    else:
                        description = f"Meme: {os.path.basename(meme_path)}"

                    if result.get('llm_selected'):
                        description += " (Selected by AI 🤖)"
                    await ctx.send(description)
                    print(f"Description sent: {description}")

                    # Add robot emoji if selected by AI
                    if result.get('llm_selected'):
                        await message.add_reaction('🤖')
                        print("Added robot emoji reaction")
            else:
                error_msg = f"Sorry, I couldn't find the meme file. Path: {meme_path}"
                print(error_msg)
                await ctx.send(error_msg)
        else:
            error_msg = "Sorry, I couldn't find a relevant meme for that context."
            print(error_msg)
            await ctx.send(error_msg)

    except Exception as e:
        error_msg = f"Error in get_meme: {str(e)}"
        print(error_msg)
        await ctx.send("Sorry, something went wrong while finding a meme.")

# Add a simple test command


@bot.command(name='ping', help='Check if the bot is responsive')
async def ping(ctx):
    print(f"Ping command received from {ctx.author}")
    await ctx.send(f"Pong! Bot latency: {round(bot.latency * 1000)}ms")

# Run the bot
if __name__ == "__main__":
    print("Starting bot...")
    bot.run(token)
