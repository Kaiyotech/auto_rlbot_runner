import random
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
    "Farmstead_Spooky"
]


def get_random_standard_map() -> str:
    return random.choice(STANDARD_MAPS)


sm: Optional[SetupManager] = None


def get_fresh_setup_manager():
    global sm
    if sm is not None:
        try:
            sm.shut_down()
        except Exception as e:
            print(e)
    sm = SetupManager()
    return sm


def run_match(bot_configs: List[PlayerConfig], _script_configs: List[ScriptConfig], game_map: AnyStr):
    match_config = MatchConfig()
    match_config.game_mode = 'Soccer'
    if game_map is None:
        match_config.game_map = get_random_standard_map()
    else:
        match_config.game_map = game_map
    match_config.enable_state_setting = True

    match_config.player_configs = bot_configs
    match_config.mutators = MutatorConfig()
    # match_config.mutators.
    match_config.auto_save_replay = False
    match_config.instant_start = False
    match_config.skip_replays = True

    sm = get_fresh_setup_manager()
    sm.early_start_seconds = 5

    sm.connect_to_game()
    sm.load_match_config(match_config)
    sm.launch_early_start_bot_processes()
    sm.start_match()
    sm.launch_bot_processes()
    sm.infinite_loop()
