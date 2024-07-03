import asyncio
import os
import random
import time
from pathlib import Path
from threading import Thread
from typing import List, Optional, Dict

from rlbot.matchconfig.match_config import PlayerConfig, ScriptConfig
from rlbot.parsing.bot_config_bundle import BotConfigBundle
from rlbot.parsing.bot_config_bundle import get_bot_config_bundle
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.utils.game_state_util import Vector3
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.process_configuration import WrongProcessArgs

# from twitchio.ext import commands
# from twitchio import Context
from pywinauto.application import Application

from match_runner import run_match
import match_runner

BotID = str

class ContinousGames():
    def __init__(self):
        self.active_thread: Optional[Thread] = None
        self.nick = 'ContinousGames'
        self.allow_overtime = get_ot_setting()
        self.enforce_no_touch = True
        self.allowed_modes = [2, 4, 6]
        self.blue = ''
        self.orange = ''
        self.num_players = ''
        self.last_ten = []
        self.last_twenty = []
        self.skip_replay = get_replay_setting()
        self.last_score = 0
        self.kickoff_game = get_kickoff_setting()
        self.enable_selector = True
        self.last_cycle_mode = 3
        self.sorted_cars = ['rookie', 'allstar', 'tensor', 'bumblebee', 'sdc',
                            'element', 'immortal', 'necto', 'optiv1', 'kbb', 'nexto']
        score_file = open("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\save_scores.txt", "r")
        for line in score_file:
            self.last_ten.append(line.strip())
            self.last_twenty.append(line.strip())
        self.test_mode = False
        save_pid()

    async def event_ready(self):
        print(f'Ready | {self.nick}')
        await self.start_round()

    def make_bot_config(self, bundle: BotConfigBundle, car_index, team_num) -> PlayerConfig:

        if bundle == "allstar" or bundle == "rookie":
            _package_dir = Path(__file__).absolute().parent
            _resource_dir = _package_dir / "resources"

            if bundle == "allstar":
                psyonix_bot = _resource_dir / "psyonix_allstar.cfg"
            else:
                psyonix_bot = _resource_dir / "psyonix_rookie.cfg"
            bot_bundle = get_bot_config_bundle(psyonix_bot)
            bot = PlayerConfig()
            bot.config_path = bot_bundle.config_path
            bot.bot = True
            bot.rlbot_controlled = False
            bot.loadout_config = bot_bundle.generate_loadout_config(car_index, team_num)
            psyonix_bot_skill = 1.0 if bundle == "allstar" else 0.0
            bot.bot_skill = psyonix_bot_skill
            bot.team = team_num
            bot.name = bot_bundle.name
            return bot
        else:
            bot = PlayerConfig()
            bot.config_path = bundle.config_path
            bot.bot = True
            bot.rlbot_controlled = True
            bot.loadout_config = bundle.generate_loadout_config(car_index, team_num)
            bot.name = bundle.name
            bot.team = team_num
            return bot

    def start_match(self, bots: List[PlayerConfig], scripts: List[ScriptConfig], my_map, snowday):
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(3.0)
        self.active_thread = Thread(target=run_match, args=(bots, scripts, my_map, self.kickoff_game, snowday), daemon=True)
        self.active_thread.start()

    def get_num_cars(self, allowed_modes):
        num_cars_fh = open("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\new_mode.txt", "r")
        try:
            mode = num_cars_fh.read()
            mode = mode.split("!setmode")[1].strip()
            if mode.lower() == 'random':
                return None
            elif mode.lower() == 'cycle':
                self.last_cycle_mode += 1
                allowed_modes.sort()
                if self.last_cycle_mode * 2 > allowed_modes[-1]:
                    self.last_cycle_mode = allowed_modes[0] // 2
                mode = self.last_cycle_mode
            mode = int(mode) * 2
            if mode not in allowed_modes:
                mode = None
        except:
            return None
        return mode

    def get_allowed_cars(self):
        my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_allowed_cars.txt"

        try:
            with open(my_file, 'r') as fh:
                my_line = fh.readline()
                lowest_car = my_line.split("!setworstallowedcar")[1].strip().lower()
                lowest_car_index = self.sorted_cars.index(lowest_car)
                allowed_cars = self.sorted_cars[lowest_car_index:]
                return allowed_cars
        except Exception as e:
            print(f"Error reading OT file: {e}")
            return

    async def periodic_check_started(self, num_players):
        packet = GameTickPacket()  # noqa
        started = False
        timeout = 30  # game start timeout
        while not started and timeout > 0:
            await asyncio.sleep(1.0)
            try:
                if match_runner.sm is not None and match_runner.sm.game_interface is not None:
                    match_runner.sm.game_interface.update_live_data_packet(packet)
                    if packet.game_info.is_round_active and packet.game_info.game_time_remaining > 60 and \
                            packet.game_info.is_kickoff_pause:
                        await asyncio.sleep(2.0)
                        # print(packet.game_info)
                        started = True
                        get_director_choice(num_players)
                        # await asyncio.sleep(1.0)
                        # hide_hud_macro()
                else:
                    print("Waiting for Rocket League to finish starting ...")
                timeout -= 1
            except WrongProcessArgs as e:
                print(f"Error: {e}. Restarting Rocket League...")
                kill_rocket_league()  # You'll need to implement this function
                await self.start_round()  # Restart the process
            except Exception as ex:
                print(ex)

                
    # async def period_checks(self):
        

    # async def periodic_check_no_touch(self):
    #     packet = GameTickPacket()  # noqa
    #     while True:
    #         previous_ball_pos = Vector3(0, 0, -100)
    #         previous_player_pos = Vector3(0, 0, 0)
    #         await asyncio.sleep(30.0)
    #         print("Checking no_touch")
    #         no_touch_ball = False
    #         stuck_car = False
    #         try:
    #             match_runner.sm.game_interface.update_live_data_packet(packet)
    #             if packet.game_ball.physics.location == previous_ball_pos and previous_ball_pos.x != 0 and \
    #                     previous_ball_pos.y != 0:
    #                 no_touch_ball = True
    #             if packet.game_cars[0].physics.location == previous_player_pos:
    #                 stuck_car = True
    #             if no_touch_ball or stuck_car:
    #                 print("car stuck or ball no touch. Starting new round...")
    #                 await self.start_round()
    #                 print("New round started")
    #                 break
    #         except Exception as ex:
    #             print(ex)

    async def periodically_check_match_ended(self):
        packet = GameTickPacket()  # noqa
        while True:
            await asyncio.sleep(1.0)
            # print("Checking if round ended")
            previous_ball_pos = Vector3(0, 0, -100)
            # previous_player_pos = Vector3(0, 0, 0)
            previous_check_time = 1000
            no_touch_ball = False
            # stuck_car = False
            self.allow_overtime = get_ot_setting()
            skip_match = get_skip_match()
            try:
                match_runner.sm.game_interface.update_live_data_packet(packet)

                if packet.game_ball.physics.location == previous_ball_pos and previous_ball_pos.x != 0 and \
                        previous_ball_pos.y != 0 and packet.game_info.seconds_elapsed - previous_check_time > 30 and \
                        self.enforce_no_touch:
                    no_touch_ball = True
                if self.test_mode:
                    packet.game_info.is_match_ended = True
                if packet.game_info.is_match_ended or (packet.game_info.is_overtime and not self.allow_overtime) or \
                        no_touch_ball or skip_match:
                    print("Match ended. Starting new round...")
                    # get score and info

                    if not skip_match:
                        game_string = f"{self.num_players}s: {self.blue} VS {self.orange} {packet.teams[0].score} - {packet.teams[1].score} // "
                        self.last_ten.insert(0, game_string)
                        self.last_twenty.insert(0, game_string)
                        while len(self.last_ten) > 10:
                            self.last_ten.pop()
                        while len(self.last_twenty) > 20:
                            self.last_twenty.pop()
                        to_write = []
                        # check if all of last twenty are the same matchup
                        all_same = True
                        for match in self.last_twenty:
                            info = match.split()
                            num_players = int(info[0].split('s:')[0])
                            if num_players != self.num_players:
                                all_same = False
                                break
                            blue = info[1]
                            orange = info[3]
                            if blue != self.blue or orange != self.orange:
                                all_same = False
                                break
                        # all 20 are the same, total them up and change the format
                        if all_same:
                            win_loss = [0, 0]
                            total_score = [0, 0]
                            scores = []
                            for match in self.last_twenty:
                                info = match.split()
                                blue_score = int(info[4])
                                orange_score = int(info[6])
                                if blue_score > orange_score:
                                    win_loss[0] += 1
                                else:
                                    win_loss[1] += 1
                                total_score[0] += blue_score
                                total_score[1] += orange_score
                                scores.append(f"{blue_score} - {orange_score} // ")
                            # so that it's all on one line
                            to_write.append(' '.join(scores))
                            to_write.insert(0, f"Last 20 {self.num_players}s: {self.blue} VS {self.orange}: {win_loss[0]} - {win_loss[1]} // Total Score: {total_score[0]} - {total_score[1]} //")
                            to_write.extend([' '] * 10)  # append some blank lines to fill it out
                        else:
                            win_loss = [0, 0]
                            total_score = [0, 0]
                            for match in self.last_ten:
                                info = match.split()
                                blue_score = int(info[4])
                                orange_score = int(info[6])
                                if blue_score > orange_score:
                                    win_loss[0] += 1
                                else:
                                    win_loss[1] += 1
                                total_score[0] += blue_score
                                total_score[1] += orange_score
                            to_write = self.last_ten.copy()
                            to_write.insert(0, f"Last 10: {win_loss[0]} - {win_loss[1]} // Total Score: {total_score[0]} - {total_score[1]} // ")
                        score_file_last = open("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\last_scores.txt", "w")
                        score_file_last.write("\n".join(to_write))
                        score_file_last.close()
                        score_file = open("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\save_scores.txt", "w")
                        score_file.write("\n".join(self.last_twenty))
                        score_file.close()
                    await self.start_round()
                    print("New round started")
                    break
                previous_check_time = packet.game_info.seconds_elapsed

                # do skip replay
                self.skip_replay = get_replay_setting()
                new_score = packet.teams[0].score + packet.teams[1].score
                if (self.skip_replay and new_score != self.last_score and not packet.game_info.is_round_active
                    and not packet.game_info.is_kickoff_pause and not packet.game_info.is_match_ended):
                    self.last_score = new_score
                    skip_replay_macro()
            except Exception as ex:
                print(ex)

    async def start_round(self):
        try:
            print("trying to start round")
            # empty the slider files in case it's not Opti playing
            my_filenames = ['peak_blue.txt', 'peak_orange.txt']
            stream_dir = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\"
            for filename in my_filenames:
                try:
                    filename = os.path.join(stream_dir, filename)
                    with open(filename, 'w') as f2:
                        f2.write("")
                except Exception as e:
                    print(f"Error writing to file: {e}")
            mode = self.get_num_cars(self.allowed_modes)
            num_players = random.choice(self.allowed_modes) if mode is None else mode
            allowed_cars = self.get_allowed_cars()
            bot_bundles_blue = get_opponent(True, allowed_cars, self.enable_selector)
            bot_bundles_orange = get_opponent(False, allowed_cars, self.enable_selector)
            self.blue = bot_bundles_blue[0].name
            self.orange = bot_bundles_orange[0].name
            self.num_players = num_players // 2
            bots = []
            mid = num_players // 2
            for i in range(num_players):
                team_num = 0 if i < mid else 1
                if team_num == 0:
                    bots.append(self.make_bot_config(bot_bundles_blue[0], 0, team_num))
                else:
                    bots.append(self.make_bot_config(bot_bundles_orange[0], 0, team_num))
            game_map = get_map()
            scripts = [ScriptConfig("C:\\Users\\kchin\\Code\\kaiyotech\\GoalSpeed\\GoalSpeed.cfg")]
            self.kickoff_game = get_kickoff_setting()
            if self.kickoff_game:
                script = ScriptConfig(
                    "C:\\Users\\kchin\\Code\\Kaiyotech\\KickoffOnly_delay_rlbot_script\\kickoff_only.cfg")

                scripts.append(script)
            snowday = get_snowday()
            self.start_match(bots, scripts, game_map, snowday)
            await asyncio.create_task(self.periodic_check_started(num_players))
            # await asyncio.create_task(self.periodic_check_no_touch())
            await asyncio.sleep(10)

            await asyncio.create_task(self.periodically_check_match_ended())
        except WrongProcessArgs as e:
            print(f"Error: {e}. Restarting Rocket League...")
            kill_rocket_league()  # You'll need to implement this function
            await self.start_round()  # Restart the process



def kill_rocket_league():
    print("Attempting to kill Rocket League")
    os.system('taskkill /f /im RocketLeague.exe')
    time.sleep(30)

def get_map():
    fh = open("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\new_map.txt", "r")
    game_map = fh.read()
    try:
        game_map = game_map.split("!setmap")[1].strip()
    except:
        game_map = None
    # first check the new ones
    for (k, v) in match_runner.NEW_STANDARD_MAPS.items():
        if game_map.lower() == k.lower():
            game_map = v
    if game_map.lower() not in [standard_map.lower() for standard_map in match_runner.STANDARD_MAPS]:
        game_map = None
    else:
        for standard_map in match_runner.STANDARD_MAPS:
            if standard_map.lower() == game_map.lower():
                game_map = standard_map
                break
    fh.close()
    return game_map


# from EastVillage
def hide_hud_macro():
    print("hiding hud")
    app = Application(backend='uia')
    try:
        app.connect(title_re='Rocket League.*')
        win = app.window(title_re='Rocket League.*')

        # Ensure the window is focused
        win.set_focus()
        time.sleep(0.5)  # Allow time for focus

        win.type_keys("{h down}" "{h up}")
    except Exception as e:
        print(f"Error executing macro: {e}")


def hide_hud_choose_1_macro():
    print("hiding hud and choosing player 1")
    app = Application(backend='uia')
    try:
        app.connect(title_re='Rocket League.*')
        win = app.window(title_re='Rocket League.*')

        # Ensure the window is focused
        win.set_focus()
        time.sleep(0.5)  # Allow time for focus

        win.type_keys("{h down}" "{h up}")
        win.type_keys("{1 down}" "{1 up}")
    except Exception as e:
        print(f"Error executing macro: {e}")


def choose_player_x_macro(x):
    print(f"choosing player {x}")
    app = Application(backend='uia')
    try:
        app.connect(title_re='Rocket League.*')
        win = app.window(title_re='Rocket League.*')

        # Ensure the window is focused
        win.set_focus()
        time.sleep(0.5)  # Allow time for focus
        win.type_keys("{h down}" "{h up}")
        win.type_keys(f"{{{x} down}}" f"{{{x} up}}")
        win.type_keys("{q down}" "{q up}")  # for FOV change
    except Exception as e:
        print(f"Error executing macro: {e}")


def skip_replay_macro():

    app = Application(backend='uia')
    try:
        app.connect(title_re='Rocket League.*')
        win = app.window(title_re='Rocket League.*')

        # Ensure the window is focused
        win.set_focus()
        time.sleep(1.5)  # Allow time for focus
        win.type_keys("{x down}" "{x up}")
        # win.click_input(button='right')
        # for _ in range(0, 15):
        #     time.sleep(0.5)
        #     win.click_input(button='right')
    except Exception as e:
        print(f"Error executing macro: {e}")


def get_opponent(blue, allowed_opponents, enable_selector):
    split_command = "!setoppo" if not blue else "!setoppoblue"
    oppo_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\opponent.txt" if not blue\
        else "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\opponent_blue.txt"
    if enable_selector:
        bot_bundle = [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot.cfg")]
    else:
        bot_bundle = [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.cfg")]
    try:
        with open(oppo_file, 'r') as fh:
            line = fh.readline()
            # if line.startswith("used"):
            #     return bot_bundle
            line = line.split(split_command)[1].strip().lower()
            if line == 'level1':
                line = random.choice(['rookie', 'allstar'])
            elif line == 'level2':
                line = random.choice(['tensor', 'allstar'])
            elif line == 'level3':
                line = random.choice(['bumblebee', 'sdc'])
            elif line == 'level4':
                line = random.choice(['necto', 'element', 'immortal'])
            elif line == 'level5':
                line = random.choice(['nexto', 'optiv1', 'kbb'])
            elif line == 'submodel':
                line = random.choice(['opti-gp', 'opti-fr', 'opti-flick', 'opti-db', 'opti-dt'])

            if line == 'opti' or line == 'selector':
                if enable_selector:
                    return bot_bundle
                else:   # return GP if not enabled selector yet
                    return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.cfg")]
            elif line == 'opti_gp' or line == 'opti-gp':
                return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.cfg")]
            elif line == 'opti-fr' or line == 'opti_fr':
                return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_fr.cfg")]
            elif line == 'opti-ko' or line == 'opti_ko':
                return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_ko.cfg")]
            elif line == 'opti-flick' or line == 'opti_flick':
                return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_flick.cfg")]
            elif line == 'opti-db' or line == 'opti_db':
                return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_db.cfg")]
            elif line == 'opti-dt' or line == 'opti_dt':
                return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_dt.cfg")]
            # elif line == 'opti-pinch' or line == 'opti_pinch':
            #     return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_pinch.cfg")]

            # standardize the names so I can filter
            if line == 'kaiyobumbut':
                line = 'kbb'
            elif line == "all-star" or line == "all star":
                line = 'allstar'

            # put the minimum allowed
            if line not in allowed_opponents:
                line = allowed_opponents[0]

            if line == 'necto':
                bot_bundle = list(scan_directory_for_bot_configs(
             "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Necto\\Necto"))
            elif line == 'nexto':
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Necto\\Nexto"))
            elif line == "optiv1":
                bot_bundle = list(scan_directory_for_bot_configs("C:\\Users\\kchin\\Code\\Kaiyotech\\Opti_play_finals_rlbot2023"))
            elif line == "sdc":
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Self-driving car"))
            elif line == "tensor":
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\tensorbot"))
            elif line == "immortal":
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\immortal"))
            elif line == "element":
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\element"))
            elif line == "kbb":
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\Code\\Kaiyotech\\KaiyoBumBot_play\\src"
                ))
            # elif line == "allstar":
            #     bot_bundle = ["allstar"]
            # elif line == "rookie":
            #     bot_bundle = ["rookie"]
            elif line == "bumblebee":
                bot_bundle = list(scan_directory_for_bot_configs(
                    "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Botimus&Bumblebee"))
            # elif line == "kamael":
            #     bot_bundle = list(scan_directory_for_bot_configs(
            #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Kamael_family"))

            # fh.seek(0, 0)
            # fh.write("used\n")
            return bot_bundle

    except Exception as e:
        print(f"Error reading opponent file: {e}. File was {oppo_file}. ")
        return bot_bundle


def get_director_choice(num_players):
    # players are 123567 director is 9 auto is 0
    my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_director.txt"
    per_team = num_players // 2
    blue = list(range(1, per_team + 1))
    orange = list(range(5, 5 + per_team))
    valid_values = blue + orange + [9, 0]
    try:
        with open(my_file, 'r') as fh:
            my_line = fh.readline()
            my_line = my_line.split("!setdirector")[1].strip()
            if my_line.lower() == 'true':
                choose_player_x_macro(9)
            elif my_line.lower() == 'auto':
                choose_player_x_macro(0)
            elif int(my_line) in valid_values:
                choose_player_x_macro(int(my_line))
            else:
                choose_player_x_macro(9)
    except Exception as e:
        print(f"Error reading peak file: {e}")
        return


def get_ot_setting():
    my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_ot.txt"

    try:
        with open(my_file, 'r') as fh:
            my_line = fh.readline()
            my_line = my_line.split("!setallowot")[1].strip()
            if my_line.lower() == 'true':
                return True
            else:
                return False
    except Exception as e:
        print(f"Error reading OT file: {e}")
        return True


def get_snowday():
    my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_snowday.txt"

    try:
        with open(my_file, 'r') as fh:
            my_line = fh.readline()
            my_line = my_line.split("!setsnowday")[1].strip()
            if my_line.lower() == 'true':
                return True
            else:
                return False
    except Exception as e:
        print(f"Error reading snowday file: {e}")
        return False


def get_replay_setting():
    my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_skip_replay.txt"

    try:
        with open(my_file, 'r') as fh:
            my_line = fh.readline()
            my_line = my_line.split("!setskipreplay")[1].strip()
            if my_line.lower() == 'true':
                return True
            else:
                return False
    except Exception as e:
        print(f"Error reading skip replay file: {e}")
        return


def get_kickoff_setting():
    my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_kickoff.txt"

    try:
        with open(my_file, 'r') as fh:
            my_line = fh.readline()
            my_line = my_line.split("!setkickoffgame")[1].strip()
            if my_line.lower() == 'true':
                return True
            else:
                return False
    except Exception as e:
        print(f"Error reading skip replay file: {e}")
        return


def get_skip_match():
    my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_skip.txt"

    try:
        with open(my_file, 'r+') as fh:
            my_line = fh.readline()
            if my_line == '!skipmatch':
                print("Skipping match")
                fh.truncate(0)  # empty the file so it's not reused
                return True
            else:
                return False
    except Exception as e:
        print(f"Error reading skip match file: {e}")
        return


def save_pid():
    pid = os.getpid()
    with open("runner_pid.txt", "w") as f:
        f.write(str(pid))


if __name__ == '__main__':
    bot = ContinousGames()
    asyncio.run(bot.start_round())
