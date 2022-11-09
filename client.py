import base64
import json
import os
import sys

import discord


class DiscordClient(discord.Client):

    async def on_ready(self):
        is_include = False
        for guild in self.guilds:
            if guild.name == 'FlaskFarm':
                is_include = True
                break
        entity = {
            'type': 'READY',
            'guild': is_include,
            'role': guild.members[0].top_role.name if is_include else ""
        }
        await self.send(entity)
        

    async def on_message(self, message):
        #print(message)
        #if message.author.id == self.user.id:
        #    return
        if message.guild == None:
            await self.process_message('DM', message)
        elif message.guild.name == 'FlaskFarm' and message.channel.name.startswith('bot'):
            await self.process_message('FF', message)
        

    async def process_message(self, mode, message):
        entity = {
            'type': mode,
            'user': message.author.name,
            'ch': message.channel.name if mode == 'FF' else 'DM',
            'id': message.id,
            'msg': message.content,
        }
        await self.send(entity)
        

    async def send(self, entity):
        text = base64.b64encode(json.dumps(entity).encode()).decode()
        print(f">>{text}")
        sys.stdout.flush()


if __name__== "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordClient(intents=intents)
    client.run(os.environ.get('DISCORD_BOT_TOKEN'))

