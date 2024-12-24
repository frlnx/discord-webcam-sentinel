import asyncio

import discord
from discord.ext import tasks
from cv2 import VideoCapture, imwrite, imread


class Bot(discord.Client):
    @tasks.loop(seconds=1)
    async def monitor(self):
        if await self.movement():
            print('Movement detected!')
            await self.save_latest_frames_from_webcam()
            await self.send_images_to_discord()
        else:
            print('No movement detected')
        await self.save_latest_frames_from_webcam()

    async def save_latest_frames_from_webcam(self):
        for i, cap in enumerate(self.caps):
            output_file = f'last_frame_{i}.png'
            ret, frame = cap.read()
            if not ret:
                continue
            imwrite(output_file, frame)

    async def movement(self) -> bool:
        for i, cap in enumerate(self.caps):
            last_frame_file = f'last_frame_{i}.png'
            ret, frame = cap.read()
            if not ret:
                return False
            last_frame = imread(last_frame_file)
            if last_frame is None:
                return True
            diff = self.compare_frames(frame, last_frame)
            print(f'Difference {i}: {diff}')
            if diff < 0.1:
                return True
        return False

    @staticmethod
    def compare_frames(frame1, frame2) -> float:
        return (frame1 == frame2).mean()

    async def on_ready(self):
        if not self.user_id:
            raise ValueError('User ID is required')
        caps = [VideoCapture(i) for i in range(self.max_cams)]
        await asyncio.sleep(1)
        self.caps = [cap for cap in caps if cap.isOpened()]
        if not self.caps:
            print('No webcam found')
        self.chaoslynx_user = await self.fetch_user(self.user_id)
        if self.chaoslynx_user is None:
            print('Failed to find user')
        self.monitor.start()
        print('Bot is ready')

    async def send_images_to_discord(self):
        assert isinstance(self.caps, list)
        for i in range(len(self.caps)):
            file_path = f'last_frame_{i}.png'
            await self.chaoslynx_user.send(file=discord.File(file_path))

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')
        if message.content == 'show':
            await self.send_images_to_discord()

def main(**kwargs):
    token = kwargs.get('token')
    user_id = kwargs.get('user_id')
    max_cams = int(kwargs.get('max_cams', 1))
    intents = discord.Intents.default()
    intents.dm_messages = True
    intents.message_content = True
    intents.members = True
    intents.messages = True

    discord_client = Bot(intents=intents)
    discord_client.user_id = user_id
    discord_client.max_cams = max_cams
    discord_client.run(token)

if __name__ == '__main__':
    with open('.env', 'r') as f:
        lines = f.readlines()
        env = {line.split('=')[0].lower(): line.split('=')[1].strip() for line in lines if '=' in line}
    main(**env)
