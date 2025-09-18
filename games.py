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

class Game():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        self.active = True
    
    async def update_message(self, message: discord.Message) -> None:
        pass
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> None:
        pass

class PointsGame(Game):
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        Game.__init__(self, client, message)
        
        self.reacts = {
            '✅':('✍️', 1),
            'Pointo':('📝', 1),
            'nopointo':('🤏', -1),
            'VeryNoPointo':('🙏', -1)}
        self.points_dict = defaultdict(int)
    
    def status(self) -> str:
        return 'Point Totals:\n' + '\n'.join(f'<@{user_id}> with {points} points.' for user_id, points in sorted(self.points_dict.items(), key=lambda x: x[1]))
    
    async def update_message(self, message: discord.Message) -> None:
        if message.channel.id != self.channel.id:
            return
        
        if not (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            return
        
        content = message.content.lower()
        if content.startswith('!end'):
            await message.channel.send(self.status())
            self.active = False
            return
        
        if content.startswith('!game'):
            await message.channel.send(self.status(), silent=True)
            return
        
        if not (content.startswith('!p') or content.startswith('!reset')):
            return
        
        if len(message.raw_mentions) == 0:
            await message.channel.send(self.status(), silent=True)
        elif content.startswith('!reset'):
            for user_id in message.raw_mentions:
                self.points_dict[user_id] = 0
            await message.add_reaction('✍️')
        else:
            point_value = re.search(r'[\d-]+$', message.content.lower().split()[0])
            if not point_value:
                point_value = 1
            else:
                point_value = int(point_value.group(0))
            for user_id in message.raw_mentions:
                self.points_dict[user_id] += point_value
            await message.add_reaction('✍️')
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> None:
        if reaction_event.channel_id != self.channel.id:
            return
        
        if reaction_event.user_id != self.author.id:
            return
        
        if reaction_event.emoji.name in self.reacts:
            reaction, points = self.reacts[reaction_event.emoji.name]
            self.points_dict[reaction_event.message_author_id] += points
            await self.channel.get_partial_message(reaction_event.message_id).add_reaction(reaction)

class EggsGame(Game):
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        Game.__init__(self, client, message)
        
        self.reacts = ['✅', 'Pointo', '🥚']
        self.eggs_dict = defaultdict(int)
    
    def status(self) -> str:
        return 'Total Eggs:\n' + '\n'.join(f'<@{user_id}> with {eggs} eggs.' for user_id, eggs in sorted(self.eggs_dict.items(), key=lambda x: x[1]))
    
    async def update_message(self, message: discord.Message) -> None:
        if message.channel.id != self.channel.id:
            return
        
        if not (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            return
        
        content = message.content.lower()
        if content.startswith('!end'):
            await message.channel.send(self.status())
            self.active = False
            return
        
        if content.startswith('!game'):
            await message.channel.send(self.status(), silent=True)
            return
        
        if not (content.startswith('!e') or content.startswith('!reset')):
            return
        
        if len(message.raw_mentions) == 0:
            await message.channel.send(self.status(), silent=True)
        elif content.startswith('!reset'):
            for user_id in message.raw_mentions:
                self.eggs_dict[user_id] = 0
            await message.add_reaction('✍️')
        else:
            egg_value = re.search(r'[\d-]+$', message.content.lower().split()[0])
            if not egg_value:
                egg_value = 1
            else:
                egg_value = int(egg_value.group(0))
            for user_id in message.raw_mentions:
                self.eggs_dict[user_id] += egg_value
            await message.add_reaction('🥚')
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> None:
        if reaction_event.channel_id != self.channel.id:
            return
        
        if reaction_event.user_id != self.author.id:
            return
        
        if reaction_event.emoji.name in self.reacts:
            self.eggs_dict[reaction_event.message_author_id] += 1
            await self.channel.get_partial_message(reaction_event.message_id).add_reaction('🥚')

class HiddenConnectionsGame(Game):
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        Game.__init__(self, client, message)
        
        self.message = None
        
        lines = [line.strip() for line in message.content.split('\n')]
        theme = lines[0]
        theme_index = theme.find(" ") + 1
        self.theme = theme[theme_index:] if theme_index else '???'
        
        # Rows are stored as arrays of individual clues, with the final clue being the optional rowtheme
        # Rows stores the solving puzzle, puzzle is the base
        self.rows = [line.split(' + ') for line in lines[1:]]
        self.puzzle = []
        for row in self.rows:
            row.append("")
            self.puzzle.append(row[:])
    
    def status(self) -> str:
        return f'Theme: {self.theme}\n' + '\n'.join(f'> {i}. ' + " + ".join(row[:-1]) +  (f' - *{row[-1]}*' if row[-1] else '') for i, row in enumerate(self.rows, 1))
    
    async def update_message(self, message: discord.Message) -> None:
        if message.channel.id != self.channel.id:
            return
        
        content = message.content.lower()
        
        if content.startswith('!game'):
            self.message = await message.channel.send(self.status())
            return
        if content.startswith('!debug'):
            print(self.theme)
            print(self.rows)
            print(self.puzzle)
        
        # Mod and Author actions (end, add, edit, delete)
        if (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            if content.startswith('!end'):
                await message.channel.send('Congratulations!')
                self.active = False
                return
            if content.startswith('!add'):
                row_number, new_row = message.content[4:].split(maxsplit=1)
                new_row = new_row.split(' + ')
                new_row.append("")
                self.rows.insert(int(row_number)-1, new_row[:])
                self.puzzle.insert(int(row_number)-1, new_row[:])
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return
            if content.startswith('!delete'):
                row_number = int(content[7:])-1
                self.rows.pop(row_number)
                self.puzzle.pop(row_number)
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return
            if content.startswith('!edit'):
                # Two possibilities, full row edit or partial edit
                row_number, edit = message.content[5:].split(maxsplit=1)
                if ord('a') <= ord(row_number[-1]) and ord(row_number[-1]) <= ord('z'):
                    row_number, index = int(row_number[:-1]) - 1, ord(row_number[-1]) - ord('a')
                    self.puzzle[row_number][index] = edit
                    self.rows[row_number][index] = edit
                else:
                    row_number = int(row_number) - 1
                    self.puzzle[row_number] = edit.split(' + ')
                    self.puzzle[row_number].append('')
                    self.rows[row_number] = self.puzzle[row_number][:]
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
                return
        
        # Public actions (theme, rowtheme, solve, adjust, clear)
        if content.startswith('!theme'):
            themetext = message.content.split(maxsplit=1)
            if len(themetext) == 1: # blank !theme, reset
                self.theme = '???'
            else:
                self.theme = themetext[1]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return
        if content.startswith('!rowtheme'):
            rowtheme = message.content[9:].split(maxsplit=1)
            if len(rowtheme) == 1: # Blank rowtheme, erase the row theme
                row_number, theme = int(rowtheme[0]) - 1, ""
            else:
                row_number, theme = rowtheme
                row_number = int(row_number) - 1
            self.rows[row_number][-1] = theme
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return
        if content.startswith('!clear'):
            row_number = content[6:]
            if ord('a') <= ord(row_number[-1]) and ord(row_number[-1]) <= ord('z'):
                row_number, index = int(row_number[:-1]) - 1, ord(row_number[-1]) - ord('a')
                self.rows[row_number][index] = self.puzzle[row_number][index]
            else:
                row_number = int(content[6:]) - 1
                self.rows[row_number] = self.puzzle[row_number][:]
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return
        if content.startswith('!solve'):
            row_number, solution = message.content[6:].split(maxsplit=1)
            row_number = int(row_number) - 1
            # Check if solution contains a rowtheme
            if hint := re.search(r" - \*(.+)\*$", solution):
                rowtheme = hint.group(1)
                solution = solution[:len(hint.group()) * -1]
            else:
                rowtheme = self.rows[row_number][-1]
            solution = solution.split(' + ')
            solution.append(rowtheme)
            self.rows[row_number] = solution
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return
        if content.startswith('!adjust'):
            row_number, edit = message.content[7:].split(maxsplit=1)
            row_number, index = int(row_number[:-1]) - 1, ord(row_number[-1]) - ord('a')
            self.rows[row_number][index] = edit
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return
        if content.startswith('!acronym'):
            # Two possibilities, full row edit or partial edit
            row_number, acronym = message.content[8:].split(maxsplit=1)
            if ord('a') <= ord(row_number[-1]) and ord(row_number[-1]) <= ord('z'):
                # partial clue
                row_number, index = int(row_number[:-1]) - 1, ord(row_number[-1]) - ord('a')
            else:
                row_number, index = int(row_number) - 1, 0
            re_acro = r'\(.*\)([^\(\)]*)$'
            re_sub = r'(' + acronym + r')\1'
            old_entry = self.rows[row_number][index]
            new_entry = re.sub(re_acro, re_sub, old_entry)
            self.rows[row_number][index] = new_entry
            await message.add_reaction('✍️')
            if self.message:
                await self.message.edit(content=self.status())
            return

class TwentyQuestionsGame(Game):
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        Game.__init__(self, client, message)

        self.questions = []
        self.reacts = ['✅', '❌', '❓', '⚔️']
        self.custom_reacts = ['fifty']
        self.win_reacts = ['👑']
        if message.attachments:
            self.image_embed = discord.Embed().set_image(url=message.attachments[0].url)
        else:
            self.image_embed = None
        self.message: discord.Message = None
        theme_index = message.content.find(" ") + 1
        self.theme = message.content[theme_index:] if theme_index else 'Twenty Questions'
    
    async def update_message(self, message: discord.Message) -> None:
        if message.channel.id != self.channel.id:
            return
        
        content = message.content.lower()
        if content.startswith('!game'):
            self.message = await message.channel.send(self.status(), embed=self.image_embed)
            return
        
        if (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles)):
            if content.startswith('!end'):
                await message.channel.send('Ending Twenty Questions')
                self.active = False
            if content.startswith('!theme'):
                themetext = message.content.split(maxsplit=1)
                if len(themetext) == 1: # blank !theme, reset
                    self.theme = 'Twenty Questions'
                else:
                    self.theme = themetext[1]
                await message.add_reaction('✍️')
                if self.message:
                    await self.message.edit(content=self.status())
            if content.startswith('!delete'):
                if len(content) > 7:
                    row_number = int(content[7:])-1
                    await message.channel.send(f'Deleted {self.questions.pop(row_number)}')
                else:
                    await message.channel.send(f'Deleted {self.questions.pop()}')
                if self.message:
                    await self.message.edit(content=self.status())
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> None:
        if reaction_event.user_id != self.author.id:
            return
        if reaction_event.channel_id != self.channel.id:
            return
        
        message = await self.channel.fetch_message(reaction_event.message_id)
        if reaction_event.emoji.name in self.custom_reacts:
            self.questions.append(f'{message.content} <:{reaction_event.emoji.name}:{reaction_event.emoji.id}>')
            await self.channel.send(f'{len(self.questions)} Question(s) Asked')
            if self.message:
                await self.message.edit(content=self.status(), embed=self.image_embed)
            return
        if reaction_event.emoji.name in self.reacts:
            self.questions.append(f'{message.content} {reaction_event.emoji.name}')
            await self.channel.send(f'{len(self.questions)} Question(s) Asked')
            if self.message:
                await self.message.edit(content=self.status(), embed=self.image_embed)
            return
        if reaction_event.emoji.name in self.win_reacts:
            await self.channel.send(f'Congrats! You found the answer in {len(self.questions)} questions.')
            self.active = False
            return
            
    def status(self) -> str:
        return self.theme + '\n' + '\n'.join(f'> {i}. {question}' for i, question in enumerate(self.questions, 1))
            
class RedactedGame(Game):
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        Game.__init__(self, client, message)
        
        self.text = RedactedGame.redact(message)
        self.plain_text = self.text.replace('||', '')
        self.tokens = set(re.findall(r'\|\|(.*?)\|\|', self.text))
        
        self.channel = client.get_partial_messageable(1173828105979318432)
        self.message = None
        command = message.content.lower().split()[0]
        self.is_scoregame = 'score' in command or 'point' in command
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
        
    async def update_message(self, message: discord.Message) -> None:
        words = message.content.replace(',','').lower().split()
        if len(words) == 0:
            return
        
        # Mod/Owner commands: !end, !reveal, !score
        if (isinstance(message.channel, discord.DMChannel) and message.author.id == self.author.id) or (message.channel.id == self.channel.id and (message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles))):
            if words[0].lower().startswith('!end'):
                await message.channel.send('Game Canceled')
                self.active = False
                return
            if words[0].lower().startswith('!reveal'):
                await message.channel.send(self.plain_text)
                self.active = False
                return
            if words[0].lower().startswith('!score'):
                await message.channel.send(self.status())
                return
            
        # Don't process messages outside the game channel
        if message.channel.id != self.channel.id:
            return
        
        # Public commands: !game
        if words[0].lower().startswith('!game'):
            self.message = await message.channel.send(RedactedGame.censor(self.text))
            return
        
        # Don't process words by the game creator
        if message.author.id == self.author.id:
            return
        
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
        if '||' not in self.text:
            await message.channel.send('Congratulations!')
            if self.is_scoregame:
                await message.channel.send(self.status())
            self.active = False

class NeedsMorePixelsGame(Game):
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        Game.__init__(self, client, message)
        
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
        
    async def update_message(self, message: discord.Message) -> None:
        words = message.content.replace(',','').lower().split()
        # Pass if message is not in NMP channel or DM with author
        if not (message.channel.id == self.channel.id or (message.author.id == self.author.id and isinstance(message.channel, discord.DMChannel))):
            return
        
        content = message.content.lower()
        if message.author.id == self.author.id or any(role.id == QUESTIONEER_ID for role in message.author.roles):
            if content.startswith('!reveal'):
                self.image_file.seek(0)
                is_spoiler = 'cw' in content or 'spoil' in content
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype, spoiler=is_spoiler))
                self.active = False
                return
            if content.startswith('!end'):
                await message.channel.send('Game Canceled')
                self.active = False
                return
            if content.startswith('!next'):
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
                    return
                self.image_file.seek(0)
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype))
                self.active = False
