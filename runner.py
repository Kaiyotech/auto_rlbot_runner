import asyncio
from threading import Thread
from typing import List, Optional
from traceback import print_exc

from rlbot.flat import *
from rlbot.managers.match import get_player_config

from match_runner import run_match

BotID = str


class ContinousGames():
    def __init__(self):
        self.match_runner = None
        self.active_thread: Optional[Thread] = None

    def start_match(self, bots: List[PlayerConfiguration], game_map):
        self.match_runner = run_match(bots, game_map)

    async def periodically_check_match_ended(self):
        packet = GameTickPacket()  # noqa
        while True:
            await asyncio.sleep(1.0)

            try:
                packet: GameTickPacket = self.match_runner.packet

                if packet.game_info.game_state_type == GameStateType.Ended:
                    print("Match ended. Starting new round...")
                    await self.start_round()
                    print("New round started")
                    break

            except Exception as ex:
                print(ex)
                print_exc()

    async def start_round(self):
        # try:
        print("trying to start round")

        bots = []
        for _ in range(2):
            bots.append(get_player_config(team=0,
                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\nectov5\\Nexto\\bot.toml",
                                          type=RLBot()))

        for _ in range(2):
            bots.append(get_player_config(team=1,
                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\nectov5\\Nexto\\bot.toml",
                                          type=RLBot()))

        game_map = 'outlaw_oasis_p'

        self.start_match(bots, game_map)
        await asyncio.sleep(10)

        await asyncio.create_task(self.periodically_check_match_ended())


if __name__ == '__main__':
    bot = ContinousGames()
    asyncio.run(bot.start_round())
