'''
Script to populate a database with Fall 2024 data.
'''

from faceit import Faceit
from database.models import Team, Player, TeamCaptain, Match, Map, PlayerStat, Placement
from database import database
import os
import json
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict
import traceback

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

FACEIT_KEY = os.getenv("FACEIT_KEY")
TOURNAMENT_IDS = json.loads(os.getenv("FACEIT_TOURNAMENT_IDS"))
PLAYOFF_IDS = json.loads(os.getenv("FACEIT_PLAYOFFS_IDS"))
THIRD_PLACE_IDS = json.loads(os.getenv("FACEIT_THIRD_PLACE_IDS"))
GROUP_AMOUNT = int(os.getenv("FACEIT_GROUP_AMOUNT"))
faceit = Faceit(FACEIT_KEY)

database.connect()
database.create_tables([Team, Player, TeamCaptain, Match, Map, PlayerStat, Placement])

players_db: list[Player] = []
matches_db: list[Match] = []
teams_db: list[Team] = []
maps_db: list[Map] = []
teamcaptain_db: list[TeamCaptain] = []
playerstats_db: list[PlayerStat] = []

for tournament_id in TOURNAMENT_IDS:
    offset = 0
    pageAmount = 100
    matches: list[dict] = faceit.get_championship_matches(tournament_id, "past", pageAmount, offset)
    championship_details = faceit.get_championship_details(tournament_id)
    championship_name: str = championship_details.get('name')
    division_name = championship_name.split()[0]
    division_num = int(division_name[1])

    print(f"Division {str(division_num)}:")

    while len(matches) != 0:
        print(f"Running offset {offset}")
        for match in matches:
            try:
                try: 
                    Match.get_by_id(match.get("match_id"))
                    continue
                except DoesNotExist:
                    pass

                team1: dict = match.get("teams").get("faction1")
                team1_db = Team.initialize(match, team1, division_num)
                team2: dict = match.get("teams").get("faction2")
                team2_db = Team.initialize(match, team2, division_num)

                try:
                    teams_db.remove(team1_db)
                except:
                    pass
                teams_db.append(team1_db)
            
                try:
                    teams_db.remove(team2_db)
                except:
                    pass
                teams_db.append(team2_db)

                match_db = Match.initialize(match, team1, team2)

                if match_db not in matches_db:
                    matches_db.append(match_db)

                if team1_db.name == 'bye' or team2_db.name == 'bye':
                    continue

                for player in team1.get("roster"):
                    player: dict
                    player_db = Player.initialize(player, team1)
                    try:
                        players_db.remove(player_db)
                    except:
                        pass
                    players_db.append(player_db)

                for player in team2.get("roster"):
                    player: dict
                    player_db = Player.initialize(player, team2)
                    try:
                        players_db.remove(player_db)
                    except:
                        pass
                    players_db.append(player_db)
                
                match_stats: dict = faceit.get_match_stats(match.get("match_id"))
                rounds = match_stats.get("rounds")
                if rounds == None:
                    continue

                for map in match_stats.get("rounds"):
                    map: dict
                    map_db = Map.initialize(map, match)

                    if map_db not in maps_db:
                        maps_db.append(map_db)

                    teams: list[dict] = map.get("teams")
                    for team in teams:
                        players: list[dict] = team.get("players")
                        for player in players:
                            playerstat_db = PlayerStat.initialize(player, map_db)
                            
                            if playerstat_db not in playerstats_db:
                                playerstats_db.append(playerstat_db)
            except Exception as e:
                print(f"Match {match.get("match_id")} failed.")
                traceback.print_exc()

        offset += pageAmount
        matches: list[dict] = faceit.get_championship_matches(tournament_id, "past", pageAmount, offset)

with database.atomic():
    Team.replace_many([obj.__data__ for obj in teams_db]).execute()
    Player.replace_many([obj.__data__ for obj in players_db]).execute()
    Match.replace_many([obj.__data__ for obj in matches_db]).execute()
    Map.replace_many([obj.__data__ for obj in maps_db]).execute()
    PlayerStat.replace_many([obj.__data__ for obj in playerstats_db]).execute()

print("Done.")