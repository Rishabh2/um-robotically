import discord
import io
import re
import os
from nltk.stem.snowball import SnowballStemmer
from PIL import Image
from datetime import datetime, timezone, timedelta
from collections import defaultdict

snow_stemmer = SnowballStemmer(language='english')
SENIOR_ROLE_ID = 1173817341876903956
QUESTIONEER_ID = 1237945777100427275

class PointsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        self.reacts = {'✅':'✍️', 'Pointo':'📝'}
        
        self.points_dict = defaultdict(int)
    
    def status(self) -> str:
        return 'Point Totals:\n' + '\n'.join(f'<@{user_id}> with {points} points.' for user_id, points in sorted(self.points_dict.items(), key=lambda x: x[1]))
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if not (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            return True
        
        if message.content.lower().startswith('!end'):
            await message.channel.send(self.status())
            return False
        
        if message.content.lower().startswith('!game'):
            await message.channel.send(self.status(), silent=True)
            return True
        
        if not message.content.lower().startswith('!p'):
            return True
        
        if len(message.raw_mentions) == 0:
            await message.channel.send(self.status(), silent=True)
            return True
        point_value = re.search(r'[\d-]+$', message.content.lower().split()[0])
        if not point_value:
            point_value = 1
        else:
            point_value = int(point_value.group(0))
        for user_id in message.raw_mentions:
            self.points_dict[user_id] += point_value
        await message.add_reaction('✍️')
        return True
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        if reaction_event.channel_id != self.channel.id:
            return True
        
        if reaction_event.user_id != self.author.id:
            return True
        
        if reaction_event.emoji.name in self.reacts:
            self.points_dict[reaction_event.message_author_id] += 1
            await self.channel.get_partial_message(reaction_event.message_id).add_reaction(self.reacts[reaction_event.emoji.name])
            return True
        
        return True

class EggsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        self.reacts = ['✅', 'Pointo', '🥚']
        
        self.eggs_dict = defaultdict(int)
    
    def status(self) -> str:
        return 'Total Eggs:\n' + '\n'.join(f'<@{user_id}> with {eggs} eggs.' for user_id, eggs in sorted(self.eggs_dict.items(), key=lambda x: x[1]))
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if not (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            return True
        
        if message.content.lower().startswith('!end'):
            await message.channel.send(self.status())
            return False
        
        if message.content.lower().startswith('!game'):
            await message.channel.send(self.status(), silent=True)
            return True
        
        if not message.content.lower().startswith('!e'):
            return True
        
        if len(message.raw_mentions) == 0:
            await message.channel.send(self.status(), silent=True)
            return True
        egg_value = re.search(r'[\d-]+$', message.content.lower().split()[0])
        if not egg_value:
            egg_value = 1
        else:
            egg_value = int(egg_value.group(0))
        for user_id in message.raw_mentions:
            self.eggs_dict[user_id] += egg_value
        await message.add_reaction('🥚')
        return True
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        if reaction_event.channel_id != self.channel.id:
            return True
        
        if reaction_event.user_id != self.author.id:
            return True
        
        if reaction_event.emoji.name in self.reacts:
            self.eggs_dict[reaction_event.message_author_id] += 1
            await self.channel.get_partial_message(reaction_event.message_id).add_reaction('🥚')
            return True
        
        return True

class HiddenConnectionsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        
        # Gather the individual lines
        clues = [clue.strip() for clue in message.content.split('\n')][1:]
        if all(clue.startswith('>') for clue in clues):
            clues = [clue[1:].strip() for clue in clues]
        
        self.clues = [clue for clue in clues if clue] # Remove blank lines
        self.answers = self.clues[:] # Deep copy the clues
        self.theme = '???'
        self.message = None
    
    def status(self) -> str:
        return f'Theme: {self.theme}\n' + '\n'.join(f'> {i}. {answer}' for i, answer in enumerate(self.answers, 1))
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if message.content.lower().startswith('!game'):
            self.message = await message.channel.send(self.status())
            return True
        
        if (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            if message.content.lower().startswith('!end'):
                await message.channel.send('Congratulations!')
                return False
            if message.content.lower().startswith('!add'):
                number, new_clue = message.content[4:].split(maxsplit=1)
                self.clues.insert(int(number)-1, new_clue)
                self.answers.insert(int(number)-1, new_clue)
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return True
            if message.content.lower().startswith('!edit'):
                number, new_clue = message.content[5:].split(maxsplit=1)
                new_answer = new_clue
                # check if number is a subindex (1a)
                if ord('a') <= ord(number[-1]) and ord(number[-1]) <= ord('z'):
                    number, letter = number[:-1], number[-1]
                    # Split row into sections
                    clue_sections = self.clues[int(number)-1].split(sep=' + ')
                    clue_sections[ord(letter)-ord('a')] = new_clue
                    answer_sections = self.answers[int(number)-1].split(sep=' + ')
                    answer_sections[ord(letter)-ord('a')] = new_clue
                    # Combine the results
                    new_clue = ' + '.join(section.strip() for section in clue_sections)
                    new_answer = ' + '.join(section.strip() for section in answer_sections)
                self.clues[int(number)-1] = new_clue
                self.answers[int(number)-1] = new_answer
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return True
            if message.content.lower().startswith('!delete'):
                number = int(message.content[7:])-1
                self.clues.pop(number)
                self.answers.pop(number)
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return True
            
        if message.content.lower().startswith('!rowtheme'):
            content = message.content[9:].split(maxsplit=1)
            if len(content) == 1: # Blank rowtheme, erase the row theme
                number, theme = content[0], ""
            else:
                number, theme = message.content[9:].split(maxsplit=1)
            answer = self.answers[int(number)-1]
            if hint := re.search(r"- ?\*.*\*$", answer):
                hint_text = hint.group()
                answer = answer[:len(hint_text) * -1]
            self.answers[int(number)-1] = answer.strip() + (f' - *{theme}*' if theme else "")
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.lower().startswith('!adjust'):
            indeces, answer = message.content[7:].split(maxsplit=1)
            
            # Parse indeces: row,entry, 1-indexed
            row_entry = indeces.split(sep=',')
            if len(row_entry) == 2: # normal comma delimination
                row, entry = row_entry
            elif ord('a') <= ord(row_entry[0][-1]) and ord(row_entry[0][-1]) <= ord('z'): # letter format without comma
                row, entry = row_entry[0][:-1], row_entry[0][-1]
            else: # formatting error, return
                return True
            
            # Split row into sections
            sections = self.answers[int(row)-1].split(sep=' + ')
            hint_text = None
            if hint := re.search(r"- ?\*.*\*$", sections[-1]):
                hint_text = hint.group()
                sections[-1] = sections[-1][:len(hint_text) * -1]
            # Set the entry to be the new answer
            if ord('a') <= ord(entry) and ord(entry) <= ord('z'):
                entry = ord(entry) - ord('a') + 1
            sections[int(entry)-1] = answer
            # Combine the results
            new_answer = ' + '.join(section.strip() for section in sections)
            if hint_text:
                new_answer += ' ' + hint_text.strip()
            self.answers[int(row)-1] = new_answer
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.lower().startswith('!solve'):
            number, answer = message.content[6:].split(maxsplit=1)
            rowtheme = ""
            if theme := re.search(r" - ?\*.*\*$", self.answers[int(number)-1]):
                rowtheme = theme.group()
            if theme := re.search(r" - ?\*.*\*$", answer):
                rowtheme = theme.group()
                answer = answer[:len(rowtheme) * -1]
            self.answers[int(number)-1] = answer + f"{rowtheme}"
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.lower().startswith('!clear'):
            number = int(message.content[6:])-1
            self.answers[number] = self.clues[number]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return True
        
        if message.content.lower().startswith('!theme'):
            themetext = message.content.split(maxsplit=1)
            if len(themetext) == 1: # blank !theme, reset
                self.theme = '???'
            else:
                self.theme = themetext[1]
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
        
        if message.content.lower().startswith('!game'):
            self.message = await message.channel.send(self.status(), embed=self.image_embed)
            return True
        
        if (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            if message.content.lower().startswith('!end'):
                await message.channel.send('Ending Twenty Questions')
                return False
            if message.content.lower().startswith('!delete'):
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
        
        self.text = RedactedGame.redact(message)
        self.plain_text = self.text.replace('||', '')
        self.tokens = set(re.findall(r'\|\|(.*?)\|\|', self.text))
        
        self.channel = client.get_partial_messageable(1173828105979318432)
        self.message = None
        command = message.content.lower().split()[0]
        self.is_scoregame = 'score' in command
        self.scores = defaultdict(int) if self.is_scoregame else None
    
    def status(self) -> str:
        return 'Score Totals:\n' + '\n'.join(f'<@{user_id}> with {points} words.' for user_id, points in sorted(self.scores.items(), key=lambda x: x[1]))
    
    def redact(message: discord.Message) -> str:
        messageContent = message.content[message.content.find('\n')+1:].replace('’', "'")
        
        if message.content.lower().startswith('!manualredact'): #manual censoring
            pass
        elif message.content.lower().startswith('!redactall'):
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
        
        return messageContent.replace('[','||').replace(']','||').replace('||||','')
        
    
    def censor(text: str) -> str:
        pattern = r'\|\|.*?\|\|'
        drastic_pattern = r'\|\| \|\|'
        censored = re.sub(pattern, '||XXX||', text)
        if len(censored) >= 2000:
            censored = re.sub(pattern, '||XX||', text)
        if len(censored) >= 2000:
            censored = re.sub(pattern, '||X||', text)
        
        # if still busted, take drastic measures
        while (len(censored) >= 2000):
            censored = re.sub(drastic_pattern, '', censored)
        
        return censored
        
    async def update_message(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
        if len(words) == 0:
            return True
        
        # Mod/Owner commands: !end, !reveal, !score
        if (isinstance(message.channel, discord.DMChannel) and message.author.id == self.author.id) or (message.channel.id == self.channel.id and (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles))):
            if words[0].lower().startswith('!end'):
                await message.channel.send('Game Canceled')
                return False
            if words[0].lower().startswith('!score'):
                await message.channel.send(self.status())
                return True
            if words[0].lower().startswith('!reveal'):
                await message.channel.send(self.plain_text)
                return False
            
        # Don't process messages outside the game channel
        if message.channel.id != self.channel.id:
            return True
        
        # Public commands: !game
        if words[0].lower().startswith('!game'):
            self.message = await message.channel.send(RedactedGame.censor(self.text))
            return True
        
        # Don't process words by the game creator
        if message.author.id == self.author.id:
            return True
        
        to_remove = set()
        for word in words:
            for token in self.tokens:
                if snow_stemmer.stem(re.sub(r'\W', '', word)) == snow_stemmer.stem(re.sub(r'\W', '', token)):
                    self.text = self.text.replace(f'||{token}||', token)
                    to_remove.add(token)
                    if self.is_scoregame:
                        self.scores[message.author.id] += 1
                if re.sub(r'\W', '', token).lower().endswith('in'):
                    if snow_stemmer.stem(re.sub(r'\W', '', word)) == snow_stemmer.stem(re.sub(r'\W', '', token+'g')):
                        self.text = self.text.replace(f'||{token}||', token)
                        to_remove.add(token)
                        if self.is_scoregame:
                            self.scores[message.author.id] += 1
        self.tokens = self.tokens.difference(to_remove)
        if to_remove:
            # If it the first message has been more than 10 seconds since the last message, send a new one
            # Otherwise, if it has been more than 1 second since the last edit, edit the last message
            # Otherwise, no-op
            now = datetime.now(tz=timezone.utc)
            if (not self.message) or ((now - self.message.created_at) > timedelta(seconds=10)):
                self.message = await message.channel.send(RedactedGame.censor(self.text))
            elif (not self.message.edited_at) or (self.message.edited_at and ((now - self.message.edited_at) > timedelta(seconds=1))):
                await message.add_reaction('✍️')
                await self.message.edit(content=RedactedGame.censor(self.text))
        if '||' in self.text:
            return True
        else:
            await message.channel.send('Congratulations!')
            if self.is_scoregame:
                await message.channel.send(self.status())
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
        # Pass if message is not in NMP channel or DM with author
        if not (message.channel.id == self.channel.id or (message.author.id == self.author.id and isinstance(message.channel, discord.DMChannel))):
            return True
        
        if message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles):
            if words[0].lower().startswith('!reveal'):
                self.image_file.seek(0)
                is_spoiler = 'cw' in message.content.lower() or 'spoil' in message.content.lower()
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype, spoiler=is_spoiler))
                return False
            if words[0].lower() == '!end':
                await message.channel.send('Game Canceled')
                return False
            if words[0].lower() == '!next':
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
