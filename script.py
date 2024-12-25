import asyncio

import discord
from discord.ext import tasks
from discord.errors import DiscordServerError
from cv2 import VideoCapture, imwrite, imread


class Bot(discord.Client):
    @tasks.loop(seconds=1)
    async def monitor(self):
        if await self.any_movement():
            print('Movement detected!')
            await self.send_images_to_discord()
        await self.save_latest_frames_from_webcam()

    async def save_latest_frames_from_webcam(self):
        for i, cap in enumerate(self.caps):
            output_file = f'last_frame_{i}.png'
            ret, frame = cap.read()
            if not ret:
                continue
            self.save_frame(output_file, frame)

    def save_frame(self, output_file, frame):
        imwrite(output_file, frame)

    async def any_movement(self) -> bool:
        for i, cap in enumerate(self.caps):
            if await self.movement(cap, i):
                return True
        return False

    async def movement(self, cap: VideoCapture, i: int) -> bool:
        last_frame_file = f'last_frame_{i}.png'
        ret, frame = cap.read()
        if not ret:
            return False
        last_frame = imread(last_frame_file)
        if last_frame is None:
            return False
        diff = self.compare_frames(frame, last_frame)
        if diff < 0.1:
            self.save_frame(f'current_frame_{i}.png', frame)
            return True

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
            await self.close()
        self.notification_user = await self.fetch_user(self.user_id)
        if self.notification_user is None:
            print('Failed to find user')
        self.monitor.start()
        print('Bot is ready')

    async def send_images_to_discord(self):
        assert isinstance(self.caps, list)
        for i in range(len(self.caps)):
            for filename in ['current_frame', 'last_frame']:
                file_path = f'{filename}_{i}.png'
                try:
                    await self.notification_user.send(file=discord.File(file_path))
                except DiscordServerError as e:
                    print(f'Failed to send image: {e}')

    async def on_message(self, message):
        if message.author != self.notification_user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')
        if message.content == 'shutdown':
            await self.close()
        if message.content == 'show':
            await self.send_images_to_discord()

    async def close(self):
        self.monitor.cancel()
        await super().close()
        for cap in self.caps:
            cap.release()
        exit(0)

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
