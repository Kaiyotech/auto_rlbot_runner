import random
import time

from dataclasses import dataclass
from typing import Dict, Optional, List, AnyStr

from rlbot.matchconfig.loadout_config import LoadoutConfig
from rlbot.matchconfig.match_config import PlayerConfig, MatchConfig, MutatorConfig, ScriptConfig
from rlbot.parsing.incrementing_integer import IncrementingInteger
from rlbot.setup_manager import SetupManager, setup_manager_context


STANDARD_MAPS = [
    "DFHStadium",
    "Mannfield",
    "ChampionsField",
    "UrbanCentral",
    "BeckwithPark",
    "UtopiaColiseum",
    "Wasteland",
    "NeoTokyo",
    "AquaDome",
    "StarbaseArc",
    "Farmstead",
    "SaltyShores",
    "DFHStadium_Stormy",
    "DFHStadium_Day",
    "Mannfield_Stormy",
    "Mannfield_Night",
    "ChampionsField_Day",
    "BeckwithPark_Stormy",
    "BeckwithPark_Midnight",
    "UrbanCentral_Night",
    "UrbanCentral_Dawn",
    "UtopiaColiseum_Dusk",
    "DFHStadium_Snowy",
    "Mannfield_Snowy",
    "UtopiaColiseum_Snowy",
    "ForbiddenTemple",
    "RivalsArena",
    "Farmstead_Night",
    "SaltyShores_Night",
    "NeonFields",
    "DFHStadium_Circuit",
    "DeadeyeCanyon",
    "StarbaseArc_Aftermath",
    "Wasteland_Night",
    "BeckwithPark_GothamNight",
    "ForbiddenTemple_Day",
    "UrbanCentral_Haunted",
    "ChampionsField_NFL",
    "BeckwithPark_Snowy",
    "NeoTokyo_Comic",
    "UtopiaColiseum_Gilded",
    "SovereignHeights",
    "Farmstead_Spooky",
    "outlaw_oasis_p",
    "ff_dusk_p",
    "fni_stadium_p",
    "swoosh_p",
    "farm_grs_p",
    "farm_hw_p",
    "neotokyo_hax_p",
    "wasteland_grs_p",
    "eurostadium_dusk_p",
    "underwater_grs_p",
    "beach_night_grs_p",
]

NEW_STANDARD_MAPS = {
    "championsfield_nikefc": "swoosh_p",
    "forbiddentemple_fireandice": "fni_stadium_p",
    "deadeyecanyon_oasis": "outlaw_oasis_p",
    "estadiovida_dusk": "ff_dusk_p",
    "mannfield_dusk": "eurostadium_dusk_p",
    "farmstead_pitched": "farm_grs_p",
    "farmstead_upsidedown": "farm_hw_p",
    "wasteland_pitched": "wasteland_grs_p",
    "neotokyo_hacked": "neotokyo_hax_p",
    "aquadome_salty": "underwater_grs_p",
    "saltyshores_salty_fest": "beach_night_grs_p",
}


def get_random_standard_map() -> str:
    return random.choice(STANDARD_MAPS)


sm: Optional[SetupManager] = None


def get_fresh_setup_manager(_match_config: MatchConfig):
    global sm
    # try to keep same
    if sm is not None: # and sm.match_config != match_config:
        try:
            sm.shut_down()
        except Exception as e:
            print(e)
    # elif sm is None:
    sm = SetupManager()

    return sm


def run_match(bot_configs: List[PlayerConfig], script_configs: List[ScriptConfig], game_map: AnyStr, kickoff_game,
              snowday):
    MAX_RETRIES = 10  # You can adjust the maximum number of attempts
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            match_config = MatchConfig()
            if snowday:
                match_config.game_mode = 'Hockey'
            else:
                match_config.game_mode = 'Soccer'
            if game_map is None:
                match_config.game_map = get_random_standard_map()
            else:
                match_config.game_map = game_map
            match_config.enable_state_setting = False
            match_config.script_configs = script_configs

            match_config.player_configs = bot_configs
            match_config.mutators = MutatorConfig()

            match_config.enable_rendering = True
            match_config.auto_save_replay = False
            match_config.instant_start = False
            match_config.skip_replays = False
            if kickoff_game:
                print("starting kickoff game")
                match_config.enable_state_setting = True
                match_config.skip_replays = True

                # if sm is None:
            sm = get_fresh_setup_manager(match_config)
            sm.early_start_seconds = 5
            sm.connect_to_game()
            sm.load_match_config(match_config)
            sm.launch_early_start_bot_processes()
            sm.start_match()
            sm.launch_bot_processes()
            sm.infinite_loop()
            break

        except TimeoutError as e:
            retry_count += 1
            if retry_count < MAX_RETRIES:
                print(f"TimeoutError occurred. Retrying (attempt {retry_count} of {MAX_RETRIES})...")
                time.sleep(10)  # Add a brief delay before retrying
            else:
                print(f"Maximum retries reached. Error: {e}")
                # Consider more sophisticated error handling if retries fail




