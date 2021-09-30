from webserver import keep_alive
import discord, os, json
from discord import FFmpegPCMAudio
from discord.errors import ClientException
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, CommandNotFound
from lib import libhelina as lbh
from embedder import embeds

arrows_emojis = ['⬆️', '⬇️', '➡️', '⬅️']
num_emojis = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']

idscontainer, datacontainer = {}, {}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
bot = commands.Bot(command_prefix="rj ")
bot.remove_command('help')

@bot.event
async def on_ready():
    print('bot is online.')

@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    if not user.bot and message.author == bot.user:
        await message.remove_reaction(str(reaction), user)
        args = message.embeds[0].footer.text.split("-")
        limit, rtype = int(args[0]), int(args[1])
        channel = message.channel
        starter_channel = user.voice.channel
        guild = message.guild
        reaction = str(reaction)
        global idscontainer, datacontainer

        if starter_channel == None:
            await channel.send("Please connect to a voice channel before using command.")
            return

        if reaction in arrows_emojis[:2]:
            if reaction == arrows_emojis[0]:limit -= 5
            if reaction == arrows_emojis[1]:limit += 5
            if limit < 5:limit = 5
            if rtype == 0:
                if int(args[2]) == 0:data, ids = lbh.getChannels()
                else:data, ids = lbh.searchRG(args[3])
                embed = embeds.embedder(data, limit, rtype, int(args[2]), args[3])
            else:
                data, ids = lbh.getStations(0)
                embed = embeds.embedder3(data, limit, rtype)
            datacontainer[channel.id][message.id] = data
            idscontainer[channel.id][message.id] = ids
            await message.edit(embed=embed)
            return

        if reaction in num_emojis:
            await message.remove_reaction(arrows_emojis[0], bot.user)
            for i in range(len(num_emojis)-1):
                await message.remove_reaction(num_emojis[i+1], bot.user)
            await message.remove_reaction(arrows_emojis[1], bot.user)
            indx = num_emojis.index(reaction)
            if rtype == 0:
                if int(args[2]) == 0:data, ids = lbh.getChannels()
                else:data, ids = lbh.searchRG(args[3])
                embed = embeds.embedder2(data, (limit-5)+indx-1, rtype, int(args[2]), args[3])
            if rtype == 1:
                data, ids = lbh.getStations(0)
                embed = embeds.embedder4(data, (limit-5)+indx-1, rtype)
            datacontainer[channel.id][message.id] = data
            idscontainer[channel.id][message.id] = ids
            await message.edit(embed=embed)
            stationid = ids[(limit-5)+indx-1]
            await message.add_reaction(arrows_emojis[3])
            await message.add_reaction("🛑")
            if rtype == 0:await message.add_reaction("💖")
            await message.add_reaction(arrows_emojis[2])

        if reaction in (arrows_emojis[3], arrows_emojis[2]):
            if reaction == arrows_emojis[3]: stationIndex = limit-1
            if reaction == arrows_emojis[2]: stationIndex = limit+1
            if stationIndex < 1: stationIndex = 1
            ids = idscontainer[channel.id][message.id]
            data = datacontainer[channel.id][message.id]
            stationid = ids[stationIndex-1]
            if rtype == 0:embed = embeds.embedder2(data, stationIndex-1, rtype, int(args[2]), args[3])
            if rtype == 1:embed = embeds.embedder4(data, stationIndex-1, rtype)
            await message.edit(embed=embed)

        try:
            vc = await starter_channel.connect()
        except ClientException:
            vc = discord.utils.get(bot.voice_clients, guild=guild)
            vc.stop()

        if reaction == "🛑" and vc.is_connected():
            if vc.is_playing(): vc.stop()
            await vc.disconnect()
            return

        if reaction == "💖":
            try:datacontainer[channel.id]
            except KeyError:
                datacontainer[channel.id]= {}
                idscontainer[channel.id] = {}
            sid = idscontainer[channel.id][message.id][limit-1]
            data = list(datacontainer[channel.id][message.id][limit-1])
            with open("favourite.json", "r") as f:
                containers = json.load(f)
            try: containers[str(user.id)][0]
            except KeyError: containers[str(user.id)] = [[],[]]
            if sid not in containers[str(user.id)][0]:
                containers[str(user.id)][0].append(sid)
                containers[str(user.id)][1].append(data)
                await channel.send("Added to your liked playlist. Use **fav** to play liked playlist.")
            else:
                await channel.send("Removed from your liked playlist. click on heart again to re-add.")
                containers[str(user.id)][0].remove(sid)
                containers[str(user.id)][1].remove(data)
            with open("favourite.json", "w") as f:
                json.dump(containers, f)
            return

        if not vc.is_playing():
            if rtype == 0:
                URL = lbh.getListenUrl(stationid)
            else: URL = stationid
            vc.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send('`Unknown command`\nPlease use right command to operate. `help` for commands details.')
    if isinstance(error, CommandInvokeError):return


@bot.command(aliases=['hlp', 'h'])
async def help(ctx):
    await ctx.send("Prefix = rj help\n**play**: To start the radio\n**Options**:\n  1 for hindi radio\n  2 for US only radio\n**search [search key]**: Search related stations from All over the world")

@bot.command(aliases=['inv', 'invit'])
async def invite(ctx):
    await ctx.send(embed=embeds.invite_embed())

@bot.command(aliases=['jn'])
async def join(ctx):
    link='https://discord.gg/PyzaTzs2cF'
    await ctx.send('Join helina development server for any help or feedback/bug report.'+link)

@bot.command(aliases=['source', 'source-code'])
async def code(ctx):
    await ctx.send(embed=embeds.source_embed())

@bot.command(aliases=['credit', 'cred', 'creds'])
async def credits(ctx):
    embed = discord.Embed(title="Helina", color=0x03f8fc)
    embed.add_field(name='API Disclaim: ', value="This API is owned by radio garden and live365.", inline=False)    
    embed.add_field(name='Developed by:', value='0x0is1', inline=False)
    await ctx.send(embed=embed)

@bot.command(aliases=['radio', 'rd', 'rdo', 'listen'])
async def play(ctx, rtype=1):
    channel_id = ctx.message.channel.id
    if rtype == 1:
        data, ids = lbh.getChannels()
        embed = embeds.embedder(data, 5, rtype-1, 0, "None")
    else:
        data, ids = lbh.getStations(0)
        embed = embeds.embedder3(data, 5, rtype-1)
    message = await ctx.send(embed=embed)
    try:datacontainer[channel_id]
    except KeyError:
        datacontainer[channel_id]= {}
        idscontainer[channel_id] = {}
    datacontainer[channel_id][message.id] = data
    idscontainer[channel_id][message.id] = ids
    await message.add_reaction(arrows_emojis[0])
    a = len(ids)
    if a > 5: a = 5
    for i in range(a):
        await message.add_reaction(num_emojis[i+1])
    await message.add_reaction(arrows_emojis[1])

@bot.command(aliases=['srch', 'find', 'look', 'collect'])
async def search(ctx, query, rtype=1):
    channel_id = ctx.message.channel.id
    data, ids = lbh.searchRG(query)
    embed = embeds.embedder(data, 5, rtype-1, 1, query)
    message = await ctx.send(embed=embed)
    try:datacontainer[channel_id]
    except KeyError:
        datacontainer[channel_id]= {}
        idscontainer[channel_id] = {}
    datacontainer[channel_id][message.id] = data
    idscontainer[channel_id][message.id] = ids
    await message.add_reaction(arrows_emojis[0])
    a = len(ids)
    if a > 5: a = 5
    for i in range(a):
        await message.add_reaction(num_emojis[i+1])
    await message.add_reaction(arrows_emojis[1])

@bot.command(aliases=['fav', 'best', 'favorite', 'liked'])
async def favourite(ctx):
    channel_id = ctx.message.channel.id
    with open("favourite.json", "r") as f:
        rawdata = json.load(f)
        try:ids, data = rawdata[str(ctx.message.author.id)]
        except KeyError: 
            await ctx.send("No favourite stations available.\nReact on 💖 to add the station to favourite.")
            return
    if len(data[0]) == 4:rtype = 2
    else:rtype = 1
    if rtype == 1:embed = embeds.embedder(data, 5, rtype-1, 0, "None")
    else:embed = embeds.embedder3(data, 5, rtype-1)
    message = await ctx.send(embed=embed)
    try:datacontainer[channel_id]
    except KeyError:
        datacontainer[channel_id]= {}
        idscontainer[channel_id] = {}
    datacontainer[channel_id][message.id] = data
    idscontainer[channel_id][message.id] = ids
    await message.add_reaction(arrows_emojis[0])
    a = len(ids)
    if a > 5: a = 5
    for i in range(a):
        await message.add_reaction(num_emojis[i+1])
    await message.add_reaction(arrows_emojis[1])

keep_alive()

bot.run('Nzc0NTEzMjQ3ODMxMTk1NjQ4.X6Y3rA.UP6x7WgXNNUqVS6wE7wBzq2cy3M')
