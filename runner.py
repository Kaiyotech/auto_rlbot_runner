import asyncio
import os
import random
import time
from pathlib import Path
from threading import Thread
from typing import List, Optional
from traceback import print_exc

from rlbot.flat import *
from rlbot.managers.match import get_player_config, MatchManager

from pywinauto.application import Application

from match_runner import run_match
import match_runner

BotID = str


class ContinousGames:
    def __init__(self):
        self.active_thread: Optional[Thread] = None
        self.nick = 'ContinousGames'

        self.match_config = MatchSettings()
        self.match_config.game_mode = GameMode.Soccer
        self.match_config.enable_state_setting = False
        self.match_config.script_configurations = []
        self.match_config.auto_start_bots = True
        self.match_config.enable_rendering = True
        self.match_config.auto_save_replay = False
        self.match_config.instant_start = False
        self.match_config.launcher = Launcher.Epic
        # match_config.existing_match_behavior = ExistingMatchBehavior.Restart
        self.match_config.existing_match_behavior = ExistingMatchBehavior.Continue_And_Spawn

        # make sure rlbot binary is in same directory
        CURRENT_FILE = Path(__file__).parent
        self.match_manager = MatchManager(CURRENT_FILE)
        self.match_manager.ensure_server_started()
        print("Press enter once the rocketplugin is hosted")
        input()

    async def event_ready(self):
        print(f'Ready | {self.nick}')
        await self.start_round()

    def start_match(self, bots: List[PlayerConfiguration], scripts: List[ScriptConfiguration], my_map):
        run_match(bots, scripts, my_map,
                                      match_config=self.match_config,
                                      match_manager=self.match_manager)

    async def periodically_check_match_ended(self):
        packet = GameTickPacket()  # noqa
        while True:
            await asyncio.sleep(1.0)
            if packet is None:
                continue

            try:
                packet: GameTickPacket = self.match_manager.packet

                if packet.game_info.game_state_type == GameStateType.Ended:
                    print("Press Enter to start new match")
                    input()
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

        bot_bundles_blue = get_opponent(True)
        bot_bundles_orange = get_opponent(False)
        bots = bot_bundles_blue + bot_bundles_orange
        game_map = get_map()

        self.start_match(bots, [], game_map)

        await asyncio.sleep(10)

        await asyncio.create_task(self.periodically_check_match_ended())


def get_map():
    fh = open("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\new_map.txt", "r")
    game_map = fh.read()
    try:
        game_map = game_map.split("!setmap")[1].strip()
    except:
        game_map = None
    # first make it into the upk name for v5
    for (k, v) in match_runner.MAP_NAME_CONVERSION.items():
        if game_map.lower() == k.lower():
            game_map = v
            break
    if game_map.lower() not in [standard_map.lower() for standard_map in match_runner.STANDARD_MAPS]:
        game_map = None

    fh.close()
    return game_map


def get_opponent(blue):
    team = 0 if blue else 1
    oppo_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\showmatch.txt"
    bot_bundle = []
    try:
        with open(oppo_file, 'r') as fh:
            lines = fh.readlines()
            for line in lines:
                # if line.startswith("used"):
                #     return bot_bundle
                split = "Blue:" if blue else "Orange:"
                if not line.startswith(split):
                    continue
                line = line.split(split)[1].strip().lower()
                line = line.split(',')

                for car in line:
                    car = car.strip()
                    # empty, return
                    if len(car) < 2:
                        continue

                    if car == 'opti' or car == 'selector':
                        bot_bundle.append(get_player_config(team=team,
                                                path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot.toml",
                                                type=RLBot()))
                        continue
                    elif car == 'opti_gp' or car == 'opti-gp':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.toml",
                                                    type=RLBot()))
                        continue
                    elif car == 'opti-fr' or car == 'opti_fr':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_fr.toml",
                                                    type=RLBot()))
                        continue
                    elif car == 'opti-ko' or car == 'opti_ko':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_ko.toml",
                                                    type=RLBot()))
                        continue
                    elif car == 'opti-flick' or car == 'opti_flick':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_flick.toml",
                                                    type=RLBot()))
                        continue
                    elif car == 'opti-db' or car == 'opti_db':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_db.toml",
                                                    type=RLBot()))
                        continue
                    elif car == 'opti-dt' or car == 'opti_dt':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_dt.toml",
                                                    type=RLBot()))
                        continue
                    elif car == 'opti-defense' or car == 'opti_defense':
                        bot_bundle.append(get_player_config(team=team,
                                                    path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_defense.toml",
                                                    type=RLBot()))
                        continue

            return bot_bundle

    except Exception as e:
        print(f"Error reading opponent file: {e}. File was {oppo_file}. ")
        return bot_bundle


if __name__ == '__main__':
    bot = ContinousGames()
    asyncio.run(bot.start_round())
