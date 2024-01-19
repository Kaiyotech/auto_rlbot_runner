import asyncio
import random
from threading import Thread
from typing import List, Optional

from rlbot.matchconfig.match_config import PlayerConfig
from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.utils.game_state_util import Vector3
from rlbot.utils.structures.game_data_struct import GameTickPacket
# from twitchio.ext import commands
# from twitchio import Context
from pywinauto.application import Application

from match_runner import run_match
import match_runner


class ContinousGames():
    def __init__(self):
        self.active_thread: Optional[Thread] = None
        self.nick = 'ContinousGames'
        self.allow_overtime = False
        self.allowed_modes = [2]

    async def event_ready(self):
        print(f'Ready | {self.nick}')
        await self.start_round()

    def make_bot_config(self, bundle: BotConfigBundle, car_index, team_num) -> PlayerConfig:
        bot = PlayerConfig()
        bot.config_path = bundle.config_path
        bot.bot = True
        bot.rlbot_controlled = True
        bot.loadout_config = bundle.generate_loadout_config(car_index, team_num)
        bot.name = bundle.name
        bot.team = team_num

        return bot

    def start_match(self, bots: List[PlayerConfig], map):
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(3.0)
        self.active_thread = Thread(target=run_match, args=(bots, None, map), daemon=True)
        self.active_thread.start()

    async def periodically_check_match_ended(self):
        packet = GameTickPacket()  # noqa
        while True:
            previous_ball_pos = Vector3(0, 0, -100)
            previous_player_pos = Vector3(0, 0, 0)
            await asyncio.sleep(10.0)
            print("Checking if round ended")
            no_touch_ball = False
            stuck_car = False
            try:
                match_runner.sm.game_interface.update_live_data_packet(packet)
                # if packet.game_ball.physics.location == previous_ball_pos and previous_ball_pos.x != 0 and \
                #         previous_ball_pos.y != 0:
                #     no_touch_ball = True
                if packet.game_cars[0].physics.location == previous_player_pos:
                    stuck_car = True
                if packet.game_info.is_match_ended or (packet.game_info.is_overtime and not self.allow_overtime) or \
                        no_touch_ball or stuck_car:
                    print("Match ended. Starting new round...")
                    await self.start_round()
                    print("New round started")
                    break
            except Exception as ex:
                print(ex)

    async def start_round(self):
        num_cars_fh = open("C:\\Users\\kchin\\Code\\Kaiyotech\\spectrum_play_redis\\stream_files\\new_mode.txt", "r+")
        try:
            mode = num_cars_fh.read()
            mode = mode.split("!changemode")[1].strip()
            mode = int(mode) * 2
            if mode not in self.allowed_modes:
                mode = None
        except:
            mode = None
            pass
        num_cars_fh.write("used")
        num_cars_fh.close()
        num_players = random.choice(self.allowed_modes) if mode is None else mode
        bot_bundles_0 = list(scan_directory_for_bot_configs("C:\\Users\\kchin\\Code\\Kaiyotech\\Opti_play_finals_rlbot2023"))
        # bot_bundles = list(scan_directory_for_bot_configs(
            # "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Necto\\Nexto"))
        bot_bundles_1 = list(scan_directory_for_bot_configs(
            "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Necto\\Nexto"))
        bots = []
        mid = num_players // 2
        for i in range(num_players):
            team_num = 0 if i < mid else 1
            if team_num == 0:
                bots.append(self.make_bot_config(bot_bundles_0[0], 0, team_num))
            else:
                bots.append(self.make_bot_config(bot_bundles_1[0], 0, team_num))
        # bots = [self.make_bot_config(bundle) for bundle in bot_bundles]
        fh = open("C:\\Users\\kchin\\Code\\Kaiyotech\\spectrum_play_redis\\stream_files\\new_map.txt", "r+")
        game_map = fh.read()
        try:
            game_map = game_map.split("!newmap")[1].strip()
        except:
            game_map = None
        if game_map not in match_runner.STANDARD_MAPS:
            game_map = None
        fh.close()

        self.start_match(bots, game_map)
        await asyncio.sleep(20)
        hide_hud_macro()
        await asyncio.sleep(60)

        await asyncio.create_task(self.periodically_check_match_ended())


# from EastVillage
def hide_hud_macro():
    print("hiding hud")
    app = Application()
    app.connect(title_re='Rocket League.*')
    win = app.window(title_re='Rocket League.*')
    win.type_keys("{h down}" "{h up}")


if __name__ == '__main__':
    bot = ContinousGames()
    asyncio.run(bot.start_round())
