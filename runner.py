import asyncio
import os
from collections import defaultdict
import csv
import random
import string
import json
import time
from dataclasses import dataclass
from threading import Thread
from typing import List, Dict, Set, Optional

from rlbot.matchconfig.loadout_config import LoadoutConfig
from rlbot.matchconfig.match_config import PlayerConfig, ScriptConfig
from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.utils.structures.game_data_struct import GameTickPacket
# from twitchio.ext import commands
# from twitchio import Context

from match_runner import run_match
import match_runner


class ContinousGames():
    def __init__(self):
        self.active_thread: Optional[Thread] = None
        self.nick = 'ContinousGames'

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

    def start_match(self, bots: List[PlayerConfig]):
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(3.0)
        self.active_thread = Thread(target=run_match, args=(bots, None), daemon=True)
        self.active_thread.start()

    async def periodically_check_match_ended(self):
        packet = GameTickPacket()
        while True:
            await asyncio.sleep(10.0)
            print("Checking if round ended")
            try:
                match_runner.sm.game_interface.update_live_data_packet(packet)
                if packet.game_info.is_match_ended:
                    print("Match ended. Starting new round...")
                    self.start_round()
                    print("New round started")
                    break
            except Exception as ex:
                print(ex)

    async def start_round(self):
        num_cars_fh = open("C:\\Users\\kchin\\Code\\Kaiyotech\\spectrum_play_redis\\stream_files\\new_mode.txt", "r+")
        mode = None
        try:
            mode = int(num_cars_fh.read())
            if mode not in [2, 4, 6]:
                mode = None
        except:
            pass
        num_cars_fh.write("used")
        num_cars_fh.close()
        num_players = random.choice([2, 4, 6]) if mode is None else mode
        bot_bundles = list(scan_directory_for_bot_configs("C:\\Users\\kchin\\Code\\Kaiyotech\\spectrum_play_redis"))
        bots = []
        mid = num_players // 2
        for i in range(num_players):
            team_num = 0 if i < mid else 1
            bots.append(self.make_bot_config(bot_bundles[0], 0, team_num))
        # bots = [self.make_bot_config(bundle) for bundle in bot_bundles]

        self.start_match(bots)
        await asyncio.sleep(10)

        await asyncio.create_task(self.periodically_check_match_ended())


if __name__ == '__main__':
    bot = ContinousGames()
    asyncio.run(bot.start_round())
