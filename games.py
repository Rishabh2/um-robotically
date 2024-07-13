import discord
import io
import re
import os
from nltk.stem.snowball import SnowballStemmer
from PIL import Image
from datetime import datetime, timezone, timedelta

snow_stemmer = SnowballStemmer(language='english')

class HiddenConnectionsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        
        # Gather the individual lines
        clues = [clue.strip() for clue in message.content.split('\n')][1:]
        if all(clue.startswith('>') for clue in clues):
            clues = [clue[1:].strip() for clue in clues]
        
        self.clues = clues
        self.answers = clues[:] # Deep copy the clues
        self.theme = '???'
        self.message = None
        self.numbered = message.content.startswith('!hc#')
        self.answerThemeList = []
    
    def status(self) -> str:
        if self.numbered:
            for i in enumerate(1):
                answerThemeList[i-1] = ""
            return f'Hidden Connections Theme: {self.theme}\n' + '\n'.join(f'> {i}. {answer}' for i, answer in enumerate(self.answers, 1))
        else:
            i = 0
            for answer in self.answers:
                answerThemeList[i] = ""
                i++
            return f'Hidden Connections Theme: {self.theme}\n' + '\n'.join(f'> {answer}' for answer in self.answers)
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if message.content.startswith('!game'):
            self.message = await message.channel.send(self.status())
            return True
        
        if (message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles)):
            if message.content.startswith('!end'):
                await message.channel.send('Congratulations!')
                return False
            if message.content.startswith('!add'):
                number, new_clue = message.content[4:].split(maxsplit=1)
                self.clues.insert(int(number)-1, new_clue)
                self.answers.insert(int(number)-1, new_clue)
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return True
            if message.content.startswith('!edit'):
                number, new_clue = message.content[5:].split(maxsplit=1)
                self.clues[int(number)-1] = new_clue
                self.answers[int(number)-1] = new_clue
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return True
            
        if message.content.startswith('!rowtheme'):
            number, theme = message.content[9:].split(maxsplit=1)
            answerThemeList[number] = theme
            answer = self.answers[int(number)-1]
            if hint := re.search(r"- ?\*.*\*$", answer):
                hint_text = hint.group()
                answer = answer[:len(hint_text) * -1]
            self.answers[int(number)-1] = answer.strip() + f' - *{theme}*'
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.startswith('!adjust'):
            indeces, answer = message.content[7:].split(maxsplit=1)
            # Parse indeces: row,entry, 1-indexed
            row, entry = indeces.split(sep=',')
            # Split row into sections
            sections = self.answers[int(row)-1].split(sep=' + ')
            hint_text = None
            if hint := re.search(r"- ?\*.*\*$", sections[-1]):
                hint_text = hint.group()
                sections[-1] = sections[-1][:len(hint_text) * -1]
            # Set the entry to be the new answer
            sections[int(entry)-1] = answer
            # Combine the results
            new_answer = ' + '.join(section.strip() for section in sections)
            if hint_text:
                new_answer += ' ' + hint_text.strip()
            self.answers[int(row)-1] = new_answer + rowThemeList[int(row)-1]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.startswith('!solve'):
            number, answer = message.content[6:].split(maxsplit=1)
            self.answers[int(number)-1] = answer + answerThemeList[number]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.startswith('!clear'):
            number = int(message.content[6:])-1
            self.answers[number] = self.clues[number]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.startswith('!theme'):
            self.theme = message.content.split(maxsplit=1)[1]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        return True
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions

class TwentyQuestionsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        self.questions = []
        self.reacts = ['✅', '❌', '❓', '⚔️']
        self.custom_reacts = ['fifty']
        self.win_reacts = ['👑']
        if message.attachments:
            self.image_embed = discord.Embed().set_image(url=message.attachments[0].url)
        else:
            self.image_embed = None
        self.message: discord.Message = None
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if message.content.startswith('!game'):
            self.message = await message.channel.send(self.status(), embed=self.image_embed)
            return True
        
        if (message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles)):
            if message.content.startswith('!end'):
                await message.channel.send('Ending Twenty Questions')
                return False
            if message.content.startswith('!delete'):
                await message.channel.send(f'Deleted {self.questions.pop()}')
                return True
        return True
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        if reaction_event.user_id != self.author.id:
            return True
        if reaction_event.channel_id != self.channel.id:
            return True
        message = await self.channel.fetch_message(reaction_event.message_id)
        if reaction_event.emoji.name in self.custom_reacts:
            self.questions.append(f'{message.content} <:{reaction_event.emoji.name}:{reaction_event.emoji.id}>')
            await self.channel.send(f'{len(self.questions)} Question(s) Asked')
            if self.message:
                await self.message.edit(content=self.status(), embed=self.image_embed)
            return True
        if reaction_event.emoji.name in self.reacts:
            self.questions.append(f'{message.content} {reaction_event.emoji.name}')
            await self.channel.send(f'{len(self.questions)} Question(s) Asked')
            if self.message:
                await self.message.edit(content=self.status(), embed=self.image_embed)
            return True
        if reaction_event.emoji.name in self.win_reacts:
            await self.channel.send(f'Congrats! You found the answer in {len(self.questions)} questions.')
            return False
        return True
            
    def status(self) -> str:
        return 'Twenty Questions:\n' + '\n'.join(self.questions)
            
class RedactedGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        messageContent = message.content[message.content.find('\n')+1:].replace('’', "'")
        
        if message.content.startswith('!manualredact'): #manual censoring
            pass
        elif message.content.startswith('!redactall'):
            messageContent = re.sub(r"([\w']+)", r'||\1||', messageContent)
        else: #auto censoring
            newContent = ''
            for line in messageContent.split('\n'):
                colonIndex = line.find(':')+1
                if colonIndex != -1:
                    prefix = line[:colonIndex]
                    body = line[colonIndex:]
                    if prefix and prefix != 'Hint:':
                        body = re.sub(r"([\w']+)", r'||\1||', body)
                    newContent += prefix + body + '\n'
                else:
                    newContent += line + '\n'
            messageContent = newContent
        
        self.text = messageContent.replace('[','||').replace(']','||').replace('||||','')
        self.plain_text = self.text.replace('||', '')
        self.tokens = set(re.findall(r'\|\|(.*?)\|\|', self.text))
        
        
        self.channel = client.get_partial_messageable(1173828105979318432)
        self.message = None
    
    def censor(self) -> str:
        pattern = r'\|\|.*?\|\|'
        drastic_pattern = r'\|\| \|\|'
        censored = re.sub(pattern, '||XXX||', self.text)
        if len(censored) >= 2000:
            censored = re.sub(pattern, '||XX||', self.text)
        if len(censored) >= 2000:
            censored = re.sub(pattern, '||X||', self.text)
        
        # if still busted, take drastic measures
        while (len(censored) >= 2000):
            censored = re.sub(drastic_pattern, '', censored)
        
        return censored
        
    async def update_message(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
        if len(words) == 0:
            return True
        
        # Parse the !game and !end command in a DM or the game
        if (isinstance(message.channel, discord.DMChannel) and message.author.id == self.author.id) or message.channel.id == self.channel.id:
            if words[0] == '!game':
                self.message = await message.channel.send(self.censor())
                return True
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
        # Don't process messages outside the game channel
        if message.channel.id != self.channel.id:
            return True
        
        # Let the game creator or mod end the game
        if message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles):
            if words[0] == '!reveal':
                await message.channel.send(self.plain_text)
                return False
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
        
        # Don't process words by the game creator
        if message.author.id == self.author.id:
            return True
        
        to_remove = set()
        for word in words:
            for token in self.tokens:
                if snow_stemmer.stem(re.sub(r'\W', '', word)) == snow_stemmer.stem(re.sub(r'\W', '', token)):
                    self.text = self.text.replace(f'||{token}||', token)
                    to_remove.add(token)
                if re.sub(r'\W', '', token).lower().endswith('in'):
                    if snow_stemmer.stem(re.sub(r'\W', '', word)) == snow_stemmer.stem(re.sub(r'\W', '', token+'g')):
                        self.text = self.text.replace(f'||{token}||', token)
                        to_remove.add(token)
        self.tokens = self.tokens.difference(to_remove)
        if to_remove:
            # If it the first message has been more than 10 seconds since the last message, send a new one
            # Otherwise, if it has been more than 1 second since the last edit, edit the last message
            # Otherwise, no-op
            now = datetime.now(tz=timezone.utc)
            if (not self.message) or ((now - self.message.created_at) > timedelta(seconds=10)):
                self.message = await message.channel.send(self.censor())
            elif (not self.message.edited_at) or (self.message.edited_at and ((now - self.message.edited_at) > timedelta(seconds=1))):
                await message.add_reaction('✍️')
                await self.message.edit(content=self.censor())
        if '||' in self.text:
            return True
        else:
            await message.channel.send('Congratulations!')
            return False
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions

class NeedsMorePixelsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = client.get_partial_messageable(1173827731079827586) # NMP channel
        self.image_file = io.BytesIO()
        self.filetype = os.path.splitext(message.attachments[0].filename)[-1]
        if self.filetype.lower() == ".jpg":
            self.filetype = ".jpeg"
        self.resize_values = None
        words = message.content.split()
        if len(words) == 2:
            self.round_count = int(words[1])
        else:
            self.round_count = 10
    
    async def set_image(self, attachment: discord.Attachment) -> None:
        await attachment.save(self.image_file)
        
    async def update_message(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
        if message.channel.id != self.channel.id:
            return True
        
        if message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles):
            if words[0] == '!reveal':
                self.image_file.seek(0)
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype))
                return False
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
            if words[0] == '!next':
                self.image_file.seek(0)
                img = Image.open(self.image_file)
                # Calculate the resize values on the first round
                if not self.resize_values:
                    if img.width < img.height:
                        total_mult_factor = img.width / 5 # Start with 5 boxes
                        individual_mult_factor = pow(total_mult_factor, 1 / (self.round_count - 1))
                        self.resize_values = [(int(5 * pow(individual_mult_factor, i)), int((5 * pow(individual_mult_factor, i) * img.height) // img.width)) for i in range(self.round_count)]
                    else:
                        total_mult_factor = img.height / 5 # Start with 5 boxes
                        individual_mult_factor = pow(total_mult_factor, 1 / (self.round_count - 1))
                        self.resize_values = [(int((5 * pow(individual_mult_factor, i) * img.width) // img.height), int(5 * pow(individual_mult_factor, i))) for i in range(self.round_count)]
                    self.current_round = 1    
                if self.current_round <= self.round_count:
                    pixelfactor = self.resize_values[self.current_round - 1]
                    imgSmall = img.resize(pixelfactor, resample=Image.Resampling.BILINEAR)
                    imgBig = imgSmall.resize(img.size, Image.Resampling.NEAREST)
                    newImg = io.BytesIO()
                    imgBig.save(newImg, self.filetype[1:])
                    newImg.seek(0)
                    await message.channel.send(f'Round {self.current_round}/{self.round_count}', file=discord.File(newImg, filename="nmp"+self.filetype))
                    self.current_round += 1
                    return True
                self.image_file.seek(0)
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype))
                return False
            
        return True
            
            
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions
