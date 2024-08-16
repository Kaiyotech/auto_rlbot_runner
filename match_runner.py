import random
from pathlib import Path

from typing import List, AnyStr
from rlbot.flat import *
from rlbot.managers import MatchManager

# from here https://github.com/RLBot/RLBot/blob/master/src/main/python/rlbot/parsing/match_settings_config_parser.py#L51
STANDARD_MAPS = [
        "Stadium_P",
        "EuroStadium_P",
        "cs_p",
        "TrainStation_P",
        "Park_P",
        "UtopiaStadium_P",
        "wasteland_s_p",
        "NeoTokyo_Standard_P",
        "Underwater_P",
        "arc_standard_p",
        "farm_p",
        "beach_P",
        "Stadium_Foggy_P",
        "stadium_day_p",
        "EuroStadium_Rainy_P",
        "EuroStadium_Night_P",
        "cs_day_p",
        "Park_Rainy_P",
        "Park_Night_P",
        "TrainStation_Night_P",
        "TrainStation_Dawn_P",
        "UtopiaStadium_Dusk_P",
        "Stadium_Winter_P",
        "eurostadium_snownight_p",
        "UtopiaStadium_Snow_P",
        "Wasteland_P",
        "Wasteland_Night_P",
        "NeoTokyo_P",
        "ARC_P",
        "Labs_CirclePillars_P",
        "Labs_Cosmic_V4_P",
        "Labs_DoubleGoal_V2_P",
        "Labs_Octagon_02_P",
        "Labs_Underpass_P",
        "Labs_Utopia_P",
        "HoopsStadium_P",
        "ShatterShot_P",
        "ThrowbackStadium_P",
        "CHN_Stadium_P",
        "cs_hw_p",
        "Farm_Night_P",
        "beach_night_p",
        "music_p",
        "Stadium_Race_Day_P",
        "Outlaw_P",
        "ARC_Darc_P",
        "Wasteland_Night_S_P",
        "Park_Bman_P",
        "CHN_Stadium_Day_P",
        "Haunted_TrainStation_P",
        "BB_P",
        "ThrowbackHockey_p",
        "Labs_Basin_P",
        "Labs_Corridor_P",
        "Labs_Holyfield_P",
        "Labs_Galleon_P",
        "Labs_Galleon_Mast_P",
        "Labs_PillarGlass_P",
        "Labs_PillarHeat_P",
        "Labs_PillarWings_P",
        "Park_Snowy_P",
        "NeoTokyo_Toon_P",
        "UtopiaStadium_Lux_P",
        "Street_P",
        "HoopsStreet_P",
        "Farm_HW_P",
        "swoosh_p",
        "fni_stadium_p",
        "outlaw_oasis_p",
        "ff_dusk_p",
        "eurostadium_dusk_p",
        "farm_grs_p",
        "farm_hw_p",
        "wasteland_grs_p",
        "neotokyo_hax_p",
        "outlaw_oasis_p",
        "ff_dusk_p",
        "fni_stadium_p",
        "swoosh_p",
        "farm_grs_p",
        "farm_hw_p",
        "underwater_grs_p",
        "beach_night_grs_p",
    ]

MAP_NAME_CONVERSION = {
    "DFHStadium": "Stadium_P",
    "Mannfield": "EuroStadium_P",
    "ChampionsField": "cs_p",
    "UrbanCentral": "TrainStation_P",
    "BeckwithPark": "Park_P",
    "UtopiaColiseum": "UtopiaStadium_P",
    "Wasteland": "wasteland_s_p",
    "NeoTokyo": "NeoTokyo_Standard_P",
    "AquaDome": "Underwater_P",
    "StarbaseArc": "arc_standard_p",
    "Farmstead": "farm_p",
    "SaltyShores": "beach_P",
    "DFHStadium_Stormy": "Stadium_Foggy_P",
    "DFHStadium_Day": "stadium_day_p",
    "Mannfield_Stormy": "EuroStadium_Rainy_P",
    "Mannfield_Night": "EuroStadium_Night_P",
    "ChampionsField_Day": "cs_day_p",
    "BeckwithPark_Stormy": "Park_Rainy_P",
    "BeckwithPark_Midnight": "Park_Night_P",
    "UrbanCentral_Night": "TrainStation_Night_P",
    "UrbanCentral_Dawn": "TrainStation_Dawn_P",
    "UtopiaColiseum_Dusk": "UtopiaStadium_Dusk_P",
    "DFHStadium_Snowy": "Stadium_Winter_P",
    "Mannfield_Snowy": "eurostadium_snownight_p",
    "UtopiaColiseum_Snowy": "UtopiaStadium_Snow_P",
    "Badlands": "Wasteland_P",
    "Badlands_Night": "Wasteland_Night_P",
    "TokyoUnderpass": "NeoTokyo_P",
    "Arctagon": "ARC_P",
    "Pillars": "Labs_CirclePillars_P",
    "Cosmic": "Labs_Cosmic_V4_P",
    "DoubleGoal": "Labs_DoubleGoal_V2_P",
    "Octagon": "Labs_Octagon_02_P",
    "Underpass": "Labs_Underpass_P",
    "UtopiaRetro": "Labs_Utopia_P",
    "Hoops_DunkHouse": "HoopsStadium_P",
    "DropShot_Core707": "ShatterShot_P",
    "ThrowbackStadium": "ThrowbackStadium_P",
    "ForbiddenTemple": "CHN_Stadium_P",
    "RivalsArena": "cs_hw_p",
    "Farmstead_Night": "Farm_Night_P",
    "SaltyShores_Night": "beach_night_p",
    "NeonFields": "music_p",
    "DFHStadium_Circuit": "Stadium_Race_Day_P",
    "DeadeyeCanyon": "Outlaw_P",
    "StarbaseArc_Aftermath": "ARC_Darc_P",
    "Wasteland_Night": "Wasteland_Night_S_P",
    'BeckwithPark_GothamNight': "Park_Bman_P",
    "ForbiddenTemple_Day": "CHN_Stadium_Day_P",
    "UrbanCentral_Haunted": "Haunted_TrainStation_P",
    "ChampionsField_NFL": "BB_P",
    "ThrowbackStadium_Snowy": "ThrowbackHockey_p",
    "Basin": "Labs_Basin_P",
    "Corridor": "Labs_Corridor_P",
    "Loophole": "Labs_Holyfield_P",
    "Galleon": "Labs_Galleon_P",
    "GalleonRetro": "Labs_Galleon_Mast_P",
    "Hourglass": "Labs_PillarGlass_P",
    "Barricade": "Labs_PillarHeat_P",
    "Colossus": "Labs_PillarWings_P",
    "BeckwithPark_Snowy": "Park_Snowy_P",
    "NeoTokyo_Comic": "NeoTokyo_Toon_P",
    "UtopiaColiseum_Gilded": "UtopiaStadium_Lux_P",
    "SovereignHeights": "Street_P",
    "Hoops_TheBlock": "HoopsStreet_P",
    "Farmstead_Spooky": "Farm_HW_P",
    "ChampionsField_NikeFC": "swoosh_p",
    "ForbiddenTemple_FireAndIce": "fni_stadium_p",
    "DeadeyeCanyon_Oasis": "outlaw_oasis_p",
    "EstadioVida_Dusk": "ff_dusk_p",
    "Mannfield_Dusk": "eurostadium_dusk_p",
    "Farmstead_Pitched": "farm_grs_p",
    "Farmstead_Upsidedown": "farm_hw_p",
    "Wasteland_Pitched": "wasteland_grs_p",
    "Neotokyo_Hacked": "neotokyo_hax_p",
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


def run_match(bot_configs: List[PlayerConfiguration], script_configs: List[ScriptConfiguration], game_map: AnyStr,
              kickoff_game,
              snowday, skip_replay,
              match_config: MatchSettings,
              match_manager: MatchManager):

    if snowday:
        match_config.game_mode = GameMode.Hockey
    else:
        match_config.game_mode = GameMode.Soccer
    if game_map is None:
        match_config.game_map_upk = get_random_standard_map()
    else:
        match_config.game_map_upk = game_map
    match_config.script_configurations = script_configs

    match_config.player_configurations = bot_configs

    match_config.skip_replays = skip_replay
    match_config.launcher = Launcher.Epic
    match_config.existing_match_behavior = ExistingMatchBehavior.Restart

    # todo reenable this later
    # if kickoff_game:
    #     print("starting kickoff game")
    #     match_config.enable_state_setting = True
    #     match_config.skip_replays = True

    match_manager.start_match(match_config)

    return






