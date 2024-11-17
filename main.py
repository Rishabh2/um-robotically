import discord
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
        
    async def on_raw_reaction_add(self, reaction_event: discord.RawReactionActionEvent):
        # Play each game, removing games that return False (done)
        self.games = {game async for game in async_update_reaction(self.games, reaction_event)}

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!hello'):
            await message.channel.send('Hello 1.2')
            return
        
        if message.author.id == H2_ID:
            if message.content.startswith('!kill'):
                quit()
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
        
        if message.content.lower().startswith('!20q'):
            # Start a 20 questions game
            if any(isinstance(game, TwentyQuestionsGame) and game.channel.id == message.channel.id for game in self.games):
                await message.channel.send('There is a game of this type running in this channel')
                return
            self.games.add(TwentyQuestionsGame(self, message))
            await message.channel.send('Starting 20 questions')
            return
        
        if message.content.lower().startswith('!hc'):
            # Start a Hidden Connections game
            if any(isinstance(game, HiddenConnectionsGame) and game.channel.id == message.channel.id for game in self.games):
                await message.channel.send('There is a game of this type running in this channel')
                return
            self.games.add(HiddenConnectionsGame(self, message))
            await message.channel.send('Starting Hidden Connections Game')
            return
        
        if message.content.lower().startswith('!nmp'):
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
        
        if message.content.lower().startswith('!redact') or message.content.lower().startswith('!manualredact'):
            # Start a Redacted game
            # Check if its just a redact test
            if message.content.lower().split()[0].endswith('test'):
                await message.channel.send(RedactedGame.censor(RedactedGame.redact(message)))
                return
            if any(isinstance(game, RedactedGame) for game in self.games):
                await message.channel.send('There is a game of this type running')
                return
            if len(message.content) >= 2000:
                await message.channel.send('Your game is too long, there is a 2000 character limit')
                return
            self.games.add(RedactedGame(self, message))
            await message.channel.send('Starting Redacted Game')
            return
        
        if message.content.lower().startswith('!point'):
            # Start a Points game
            if any(isinstance(game, PointsGame) and game.channel.id == message.channel.id for game in self.games):
                await message.channel.send('There is a game of this type running in this channel')
                return
            self.games.add(PointsGame(self, message))
            await message.channel.send('Starting Points Game')
            return
        
        if message.content.lower().startswith('!egg'):
            # Start Egg
            if any(isinstance(game, EggsGame) and game.channel.id == message.channel.id for game in self.games):
                await message.channel.send('There is a game of this type running in this channel')
                return
            self.games.add(EggsGame(self, message))
            await message.channel.send('Egg')
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
