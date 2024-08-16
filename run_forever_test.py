from pathlib import Path
from time import sleep

from rlbot import flat
from rlbot.managers import MatchManager, get_player_config
from rlbot.utils.maps import GAME_MAP_TO_UPK, STANDARD_MAPS

CURRENT_FILE = Path(__file__).parent


if __name__ == "__main__":
    match_manager = MatchManager(CURRENT_FILE)
    match_manager.ensure_server_started()

    current_map = 15

    match_settings = flat.MatchSettings(
        launcher=flat.Launcher.Steam,
        auto_start_bots=True,
        game_mode=flat.GameMode.Soccer,
        enable_state_setting=True,
        existing_match_behavior=flat.ExistingMatchBehavior.Continue_And_Spawn,
        skip_replays=True,
        player_configurations=[
            get_player_config(team=0,
                              path="C:\\Users\\kchin\\Code\\Kaiyotech\\opti_play_redis\\bot.toml",
                              type=flat.RLBot()),
            get_player_config(team=1,
                              path="C:\\Users\\kchin\\Code\\Kaiyotech\\nectov5\\Nexto\\bot.toml",
                              type=flat.RLBot()),
        ],
    )

    while True:
        # DO use the same map
        # current_map = (current_map + 1) % len(STANDARD_MAPS)
        match_settings.game_map_upk = GAME_MAP_TO_UPK[STANDARD_MAPS[current_map]]

        print(f"Starting match on {match_settings.game_map_upk}")

        match_manager.start_match(match_settings)

        while (
            match_manager.packet is None
            or match_manager.packet.game_info.game_state_type
            != flat.GameStateType.Ended
        ):
            if (
                match_manager.packet is not None
                and match_manager.packet.game_info.game_state_type
                == flat.GameStateType.Countdown
            ):
                match_manager.set_game_state(
                    flat.DesiredGameState(
                        game_info_state=flat.DesiredGameInfoState(game_speed=10)
                    )
                )

            sleep(1)

        # let the end screen play for 5 seconds (just for fun)
        # sleep(5)