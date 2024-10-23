import os
import random
import time
from pathlib import Path
from threading import Thread
from typing import List, Optional
from rlbot.flat import *
from rlbot.managers.match import get_player_config, MatchManager

from match_runner import run_match
import match_runner

BotID = str


class ContinousGames:
    def __init__(self):
        self.active_thread: Optional[Thread] = None
        self.nick = 'ContinousGames'
        self.allow_overtime = get_ot_setting()
        self.enforce_no_touch = True
        self.stuck_ball_time = 0
        self.touch_timeout_sec = 30
        self.previous_ball_pos = Vector3(0, 0, -100)
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
        self.test_mode = False if os.environ["COMPUTERNAME"] != 'MSI' else self.test_mode

        save_pid()

        self.match_config = MatchSettings()
        self.match_config.game_mode = GameMode.Soccer
        self.match_config.enable_state_setting = True
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

    def run(self):
        while True:
            self.start_round()

    def start_round(self):
        # try:
        print("trying to start round")
        # reset touch stuff
        self.stuck_ball_time = 0
        self.previous_ball_pos = Vector3(0, 0, -100)
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
        mid = num_players // 2
        allowed_cars = self.get_allowed_cars()
        bot_bundles_blue = get_opponent(True, allowed_cars, self.enable_selector, mid)
        bot_bundles_orange = get_opponent(False, allowed_cars, self.enable_selector, mid)
        self.blue = bot_bundles_blue[0].name
        self.orange = bot_bundles_orange[0].name
        # check for mixed teams
        for bot in bot_bundles_blue:
            if bot.name != self.blue:
                self.blue = self.blue + '*'
        for bot in bot_bundles_orange:
            if bot.name != self.orange:
                self.orange = self.orange + '*'
        self.num_players = mid

        bots = bot_bundles_blue + bot_bundles_orange
        game_map = get_map()
        # todo port scripts later
        scripts = []
        # scripts = [ScriptConfig("C:\\Users\\kchin\\Code\\kaiyotech\\GoalSpeed\\GoalSpeed.cfg")]
        # self.kickoff_game = get_kickoff_setting()
        # if self.kickoff_game:
        #     script = ScriptConfig(
        #         "C:\\Users\\kchin\\Code\\Kaiyotech\\KickoffOnly_delay_rlbot_script\\kickoff_only.cfg")
        #
        #     scripts.append(script)

        snowday = get_snowday()
        self.start_match(bots, scripts, game_map, snowday, num_players)
        packet: GameTickPacket = self.match_manager.packet
        # wait to start up
        startup_seconds = 0
        while packet is None or len(packet.balls) == 0 or len(packet.players) < 2 or \
                packet.game_info.game_state_type not in (GameStateType.Kickoff,
                                                         GameStateType.Countdown, GameStateType.Active):
            packet: GameTickPacket = self.match_manager.packet
            time.sleep(1)
            startup_seconds += 1
            if startup_seconds >= 15:
                print("issue starting up match. Trying again")
                return
        self.getset_director_choice(num_players)
        self.hide_hud_macro()
        self.periodically_check_match_ended()
        print("Match Ended")

    def start_match(self, bots: List[PlayerConfiguration], scripts: List[ScriptConfiguration], my_map, snowday,
                    num_players):
        self.skip_replay = get_replay_setting()
        self.match_config.skip_replays = self.skip_replay
        run_match(bots, scripts, my_map, self.kickoff_game, snowday, self.skip_replay,
                  match_config=self.match_config,
                  match_manager=self.match_manager
                  )
        if self.test_mode:
            self.match_manager.set_game_state(
                DesiredGameState(
                    game_info_state=DesiredGameInfoState(game_speed=10)
                )
            )

    def periodically_check_match_ended(self):

        self.allow_overtime = get_ot_setting()
        while True:
            time.sleep(1.0)

            no_touch_ball = False
            skip_match = get_skip_match()
            # try:
            packet: GameTickPacket = self.match_manager.packet
            if packet is None:
                continue

            if self.stuck_ball_time != 0 and time.time() - self.stuck_ball_time > self.touch_timeout_sec and self.enforce_no_touch:
                no_touch_ball = True
            # pause on ended to allow dancing/final scoreboard for a bit (not right now)
            # if packet.game_info.game_state_type == GameStateType.Ended:
            #     time.sleep(6)
            if packet.game_info.game_state_type == GameStateType.Ended or (
                    packet.game_info.is_overtime and not self.allow_overtime) or \
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
                        to_write.insert(0,
                                        f"Last 20 {self.num_players}s: {self.blue} VS {self.orange}: {win_loss[0]} - {win_loss[1]} // Total Score: {total_score[0]} - {total_score[1]} //")
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
                        to_write.insert(0,
                                        f"Last 10: {win_loss[0]} - {win_loss[1]} // Total Score: {total_score[0]} - {total_score[1]} // ")
                    score_file_last = open(
                        "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\last_scores.txt", "w")
                    score_file_last.write("\n".join(to_write))
                    score_file_last.close()
                    score_file = open(
                        "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\save_scores.txt", "w")
                    score_file.write("\n".join(self.last_twenty))
                    score_file.close()

                break
            if len(packet.balls) > 0 and packet.balls[
                0].physics.location == self.previous_ball_pos and self.stuck_ball_time == 0:
                self.stuck_ball_time = time.time()
            elif len(packet.balls) > 0 and packet.balls[0].physics.location != self.previous_ball_pos:
                self.stuck_ball_time = 0
            self.previous_ball_pos = Vector3(packet.balls[0].physics.location.x,
                                             packet.balls[0].physics.location.y,
                                             packet.balls[0].physics.location.z
                                             ) if len(packet.balls) > 0 else Vector3(0, 0, -100)

            # except Exception as ex:
            #     print(ex)
            #     print_exc()

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

    def hide_hud_macro(self):
        command = "CycleHUD"
        print(f"hiding hud with command: {command}")
        self.match_manager.set_game_state(
            DesiredGameState(console_commands=([ConsoleCommand(command=command)]))
        )

    def getset_director_choice(self, num_players):
        print("getting and setting director choice")
        # players are 123567 director is 9 auto is 0
        my_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\set_director.txt"
        per_team = num_players // 2
        blue = list(range(0, per_team))
        orange = list(range(5, 5 + per_team))
        valid_values = blue + orange + [9, 0]
        command = "ViewDefault"
        try:
            with open(my_file, 'r') as fh:
                my_line = fh.readline()
                my_line = my_line.split("!setdirector")[1].strip()
                if my_line.lower() == 'true':
                    command = "ViewDefault"
                elif my_line.lower() == 'auto':
                    command = "ViewAutoCam"
                elif int(my_line) - 1 in valid_values:
                    value = int(my_line) - 1
                    # blue
                    if value < per_team:
                        command = f"ViewPlayer 0 {value}"
                    else:
                        command = f"ViewPlayer 1 {value - 5}"
                print(f"Setting viewer command: {command}")
                self.match_manager.set_game_state(
                    DesiredGameState(console_commands=([ConsoleCommand(command=command)]))
                )
        except Exception as e:
            print(f"Error reading director file: {e}")
            return


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


def get_opponent(blue, allowed_opponents, enable_selector, teamsize):
    team = 0 if blue else 1
    # #testing (doesn't seem to work though, lol)
    # bot_bundle = []
    # for _ in range(teamsize):
    #     bot_bundle.append(get_player_config(team=team,
    #                                         path="C:\\Users\\kchin\\Code\\Kaiyotech\\rlbot-python-example\\src\\bot.toml",
    #                                         type=RLBot()))
    #
    # return bot_bundle
    split_command = "!setoppo" if not blue else "!setoppoblue"
    oppo_file = "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\opponent.txt" if not blue \
        else "C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\stream_files\\opponent_blue.txt"
    if enable_selector:
        bot_bundle = []
        for _ in range(teamsize):
            bot_bundle.append(get_player_config(team=team,
                                                path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot.toml",
                                                type=RLBot()))

    else:
        bot_bundle = []
        for _ in range(teamsize):
            bot_bundle.append(get_player_config(team=team,
                                                path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.toml",
                                                type=RLBot()))
    try:
        with (open(oppo_file, 'r') as fh):
            line = fh.readline()
            # if line.startswith("used"):
            #     return bot_bundle
            line = line.split(split_command)[1].strip().lower()
            line = line.split(',')
            # reduce line to teamsize if too big
            while len(line) > teamsize:
                line.pop()
            # pad out with the first player if too small
            if len(line) < teamsize:
                num_to_pad = teamsize - len(line)
                for i in range(teamsize - num_to_pad, teamsize):
                    line.append(line[0])
            index = -1
            for car in line:
                index += 1
                car = car.strip()
                # badly formed, just use selector
                if len(car) < 2:
                    car = 'opti'
                if car == 'level1':
                    car = random.choice(['rookie', 'allstar'])
                elif car == 'level2':
                    car = random.choice(['tensor', 'allstar'])
                elif car == 'level3':
                    car = random.choice(['bumblebee', 'sdc'])
                elif car == 'level4':
                    car = random.choice(['necto', 'element', 'immortal'])
                elif car == 'level5':
                    car = random.choice(['nexto', 'optiv1', 'kbb'])
                elif car == 'submodel':
                    car = random.choice(['opti-gp', 'opti-fr', 'opti-flick', 'opti-db', 'opti-dt', 'opti-defense'])

                if car == 'opti' or car == 'selector':
                    if enable_selector:
                        continue
                    else:  # return GP if not enabled selector yet
                        bot_bundle[index] = get_player_config(team=team,
                                                              path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.toml",
                                                              type=RLBot())
                        continue
                elif car == 'opti_gp' or car == 'opti-gp':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_gp.toml",
                                                          type=RLBot())
                    continue
                elif car == 'opti-fr' or car == 'opti_fr':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_fr.toml",
                                                          type=RLBot())
                    continue
                elif car == 'opti-ko' or car == 'opti_ko':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_ko.toml",
                                                          type=RLBot())
                    continue
                elif car == 'opti-flick' or car == 'opti_flick':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_flick.toml",
                                                          type=RLBot())
                    continue
                elif car == 'opti-db' or car == 'opti_db':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_db.toml",
                                                          type=RLBot())
                    continue
                elif car == 'opti-dt' or car == 'opti_dt':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_dt.toml",
                                                          type=RLBot())
                    continue
                elif car == 'opti-defense' or car == 'opti_defense':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_defense.toml",
                                                          type=RLBot())
                    continue
                # elif car == 'opti-pinch' or car == 'opti_pinch':
                #     return [get_bot_config_bundle("C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot_pinch.cfg")]

                # standardize the names so I can filter
                if car == 'kaiyobumbut':
                    car = 'kbb'
                elif car == "all-star" or car == "all star":
                    car = 'allstar'

                # put the minimum allowed
                if car not in allowed_opponents:
                    car = allowed_opponents[0]

                if car == 'necto':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\nectov5\\Necto\\bot.toml",
                                                          type=RLBot())
                    continue
                elif car == 'nexto':
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\nectov5\\Nexto\\bot.toml",
                                                          type=RLBot())
                    continue
                # todo convert other bots eventually maybe
                elif car == "optiv1":
                    bot_bundle[index] = get_player_config(team=team,
                                                          path="C:\\Users\\kchin\\Code\\Kaiyotech\\Opti_play_v1",
                                                          type=RLBot())
                    continue
                # elif car == "sdc":
                #     bot_bundle[index] = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Self-driving car"))[0]
                #     continue
                # elif car == "tensor":
                #     bot_bundle[index] = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\tensorbot"))[0]
                #     continue
                # elif car == "immortal":
                #     bot_bundle[index] = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\immortal"))[0]
                #     continue
                # elif car == "element":
                #     bot_bundle[index] = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\element"))[0]
                #     continue
                # elif car == "kbb":
                #     bot_bundle[index] = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\Code\\Kaiyotech\\KaiyoBumBot_play\\src"
                #     ))[0]
                #     continue
                # elif car == "allstar":
                #     bot_bundle = ["allstar"]
                # elif car == "rookie":
                #     bot_bundle = ["rookie"]
                # elif car == "bumblebee":
                #     bot_bundle[index] = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Botimus&Bumblebee"))[0]
                #     continue
                # elif car == "kamael":
                #     bot_bundle = list(scan_directory_for_bot_configs(
                #         "C:\\Users\\kchin\\AppData\\Local\\RLBotGUIX\\RLBotPackDeletable\\RLBotPack-master\\RLBotPack\\Kamael_family"))

                # fh.seek(0, 0)
                # fh.write("used\n")
                index += 1

            return bot_bundle

    except Exception as e:
        print(f"Error reading opponent file: {e}. File was {oppo_file}. ")
        return bot_bundle

    # todo add psyonix back eventually
    # def make_bot_config(self, bundle: BotConfigBundle, car_index, team_num) -> PlayerConfig:
    #
    #     if bundle == "allstar" or bundle == "rookie":
    #         _package_dir = Path(__file__).absolute().parent
    #         _resource_dir = _package_dir / "resources"
    #
    #         if bundle == "allstar":
    #             psyonix_bot = _resource_dir / "psyonix_allstar.cfg"
    #         else:
    #             psyonix_bot = _resource_dir / "psyonix_rookie.cfg"
    #         bot_bundle = get_bot_config_bundle(psyonix_bot)
    #         bot = PlayerConfig()
    #         bot.config_path = bot_bundle.config_path
    #         bot.bot = True
    #         bot.rlbot_controlled = False
    #         bot.loadout_config = bot_bundle.generate_loadout_config(car_index, team_num)
    #         psyonix_bot_skill = 1.0 if bundle == "allstar" else 0.0
    #         bot.bot_skill = psyonix_bot_skill
    #         bot.team = team_num
    #         bot.name = bot_bundle.name
    #         return bot
    #     else:
    #         bot = PlayerConfig()
    #         bot.config_path = bundle.config_path
    #         bot.bot = True
    #         bot.rlbot_controlled = True
    #         bot.loadout_config = bundle.generate_loadout_config(car_index, team_num)
    #         bot.name = bundle.name
    #         bot.team = team_num
    #         return bot


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


if __name__ == "__main__":
    cont_games = ContinousGames()
    cont_games.run()
