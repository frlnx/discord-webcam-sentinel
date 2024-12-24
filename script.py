import discord
from discord.ext import tasks
from cv2 import VideoCapture, imwrite, imread


class Bot(discord.Client):
    @tasks.loop(seconds=1)
    async def monitor(self):
        if await self.movement('last_frame.png'):
            print('Movement detected!')
            await self.save_latest_frame_from_webcam('last_frame.png')
            await self.send_image_to_discord('last_frame.png')
        else:
            print('No movement detected')
        await self.save_latest_frame_from_webcam('last_frame.png')

    async def save_latest_frame_from_webcam(self, output_file):
        ret, frame = self.cap.read()
        if not ret:
            return False
        imwrite(output_file, frame)
        return True

    async def movement(self, last_frame_file) -> bool:
        ret, frame = self.cap.read()
        if not ret:
            raise ValueError('Failed to read frame')
        last_frame = imread(last_frame_file)
        if last_frame is None:
            raise ValueError('Failed to read last frame')
        diff = self.compare_frames(frame, last_frame)
        print(f'Difference: {diff}')
        return diff < 0.1

    @staticmethod
    def compare_frames(frame1, frame2) -> float:
        return (frame1 == frame2).mean()

    async def on_ready(self):
        if not self.user_id:
            raise ValueError('User ID is required')
        self.cap = VideoCapture(0)
        if self.cap.isOpened():
            print('No webcam found')
        self.chaoslynx_user = await self.fetch_user(self.user_id)
        if self.chaoslynx_user is None:
            print('Failed to find user')
        self.monitor.start()
        print('Bot is ready')

    async def send_image_to_discord(self, file_path):
        await self.chaoslynx_user.send(file=discord.File(file_path))

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')
        if message.content == 'show':
            await self.send_image_to_discord('last_frame.png')

def main(**kwargs):
    token = kwargs.get('token')
    user_id = kwargs.get('user_id')
    intents = discord.Intents.default()
    intents.dm_messages = True
    intents.message_content = True
    intents.members = True
    intents.messages = True

    discord_client = Bot(intents=intents)
    discord_client.user_id = user_id
    discord_client.run(token)

if __name__ == '__main__':
    with open('.env', 'r') as f:
        lines = f.readlines()
        env = {line.split('=')[0].lower(): line.split('=')[1].strip() for line in lines if '=' in line}
    main(**env)
