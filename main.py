import discord
import random
from games import RedactedGame, TwentyQuestionsGame, NeedsMorePixelsGame, HiddenConnectionsGame, PointsGame, EggsGame

BOT_STUFF_ID = 1173819549326524537
H2_ID = 242558859300831232

async def async_update_message(iterable, message: discord.Message):
    for item in iterable:
        should_yield = await item.update_message(message)
        if should_yield:
            yield item

async def async_update_reaction(iterable, reaction_event: discord.RawReactionActionEvent):
    for item in iterable:
        should_yield = await item.update_reaction(reaction_event)
        if should_yield:
            yield item

with open("discord.token", "r") as token_file:
    token = token_file.read()

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.games = set()
        self.game_queue = []
        self.send_access_id = None
        self.send_count = 0
        await client.change_presence(activity=discord.Game('!commands'))
        
    async def on_raw_reaction_add(self, reaction_event: discord.RawReactionActionEvent):
        # Play each game, removing games that return False (done)
        self.games = {game async for game in async_update_reaction(self.games, reaction_event)}

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!hello'):
            await message.channel.send('Hello 1.2')
            return
        
        if message.content.startswith('!commands'):
            await message.channel.send('https://docs.google.com/document/d/1UUlaKuYEcimaRWvfkYJSa9McEC7350_wQTeRJYcJqno/edit?usp=sharing')
            return
        
        if message.content.startswith('!speak'):
            if random.randrange(1000) == 0:
                self.send_access_id = message.author.id
                self.send_count = 3
                await message.channel.send('Congratulations')
        
        if message.author.id == H2_ID:
            if message.content.startswith('!kill'):
                quit()
            if message.content.startswith('!send'):
                _, channel, to_send = message.content.split(maxsplit=2)
                channel = self.get_partial_messageable(int(channel))
                await channel.send(content=to_send)
        if message.author.id == self.send_access_id and message.content.startswith('!send'):
            _, channel, to_send = message.content.split(maxsplit=2)
            channel = self.get_partial_messageable(int(channel))
            await channel.send(content=to_send)
            self.send_count -= 1
            if self.send_count <= 0:
                self.send_access = None
        if message.content.startswith('!owner'):
            for game in self.games:
                if game.channel.id == message.channel.id:
                    await message.channel.send(game.author.mention)
            return
        if message.content.startswith('!games'):
            if len(self.games) == 0:
                games_msg = "There are no bot games running"
            else:
                games_fmt = '{type} from {owner} in <#{channel}>'
                games_msg = '\n'.join(games_fmt.format(type=type(game).__name__, owner=game.author.mention, channel=game.channel.id) for game in self.games)
            await message.channel.send(games_msg)
            return
        
        if message.content.lower().startswith('!h2nmp'):
            # Start a Needs More Pixels game
            if any(isinstance(game, NeedsMorePixelsGame) for game in self.games):
                newGame = NeedsMorePixelsGame(self, message)
                await newGame.set_image(message.attachments[0])
                self.game_queue.append(newGame)
                await message.channel.send('You have been added to the Needs More Pixels Queue')
                return
            if len(message.attachments) != 1:
                await message.channel.send('Needs More Pixels takes one image at a time')
                return
            newGame = NeedsMorePixelsGame(self, message)
            await newGame.set_image(message.attachments[0])
            self.games.add(newGame)
            await message.channel.send('Starting Needs More Pixels')
            return
        
        # Play each game, removing games that return False (done)
        self.games = {game async for game in async_update_message(self.games, message)}
        # Add a NMP if possible
        if len(self.game_queue) > 0 and not any(isinstance(game, NeedsMorePixelsGame) for game in self.games):
            newGame = self.game_queue.pop(0)
            await newGame.author.send('Your turn for Needs More Pixels')
            self.games.add(newGame)
            
                

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token)