#!/usr/bin python3

import pandas as pd
import numpy as np


def process_match_lineups():
    """This function is used to make two dictionaries to a) hold unique match ups to track box scores 
       b) track players on the floor after each period

    Returns:
        league_matches: {
            game_id: {
                team_1: {
                    box_score: 0,
                    player_1: plus_minus,
                    player_2: plus_minus, 
                    etc..
                },
                team_2: {
                    box_score: 0,
                    player_1: plus_minus,
                    player_2: plus_minus, 
                    etc..
                },
            }
        }

        match_starters: {
            game_id: {
                period_1: {
                    team_1: {
                        player_1: true,
                        player_2: true,
                        etc..
                    },
                    team_2: {
                        player_1: true,
                        player_2: true,
                        etc..
                    },
                },
                period_2: {
                    etc..
                },
            }
        }

    """

    league_matches = {}
    match_starters = {}

    match_lineups = pd.read_csv('Game_Lineup.txt')

    for i, row in match_lineups.iterrows():
        game_id = row['Game_id']
        team_id = row['Team_id']
        person_id = row['Person_id']
        period = row['Period']

        if league_matches.get(game_id) is None:
            league_matches[game_id] = {}
            match_starters[game_id] = {}

        if league_matches[game_id].get(team_id) is None:
            league_matches[game_id][team_id] = {}
            match_starters[game_id][team_id] = {}

        if league_matches[game_id][team_id].get('box_score') is None:
            league_matches[game_id][team_id]['box_score'] = 0

        league_matches[game_id][team_id][person_id] = 0

        if match_starters[game_id][team_id].get(period) is None:
            match_starters[game_id][team_id][period] = {}

        match_starters[game_id][team_id][period][person_id] = True

    return (league_matches, match_starters)


def process_game_logs(league_matches, match_starters):
    """This function is used to determine the action to take from the play by log

    Args:
        league_matches (object): the dictionary containing box score & player plus minus 
        match_starters (object): the dictionary containing the starters & active players for every period

   Returns:
        object: league_matches - see process_match_lineups() for data structure

    """

    play_by_play = pd.read_csv('Play_by_Play.txt',
                               dtype={'Event_Msg_Type': np.int8, 'Period': np.int8, 'Action_Type': np.int8, 'Option1': np.int8})

    active_after_ft = []
    sub_after_ft = []

    for i, row in play_by_play.iterrows():
        game_id = row['Game_id']
        team_id = row['Team_id']
        event = row['Event_Msg_Type']
        action = row['Action_Type']
        option = row['Option1']
        player = row['Person1']
        sub = row['Person2']
        period = row['Period']

        game = league_matches[game_id]

        # continue for invalid team_id. e.g. game start
        if game.get(team_id) is None:
            continue

        # - differential score at start of period
        if event == 12:
            teams = list(match_starters[game_id].keys())

            for unique_team in teams:
                opponent = getOpponent(game, unique_team)
                players = list(match_starters[game_id][unique_team][period].keys())

                for unique_player in players:
                    if match_starters[game_id][unique_team][period][unique_player] is True:
                        league_matches[game_id][unique_team][unique_player] -= (league_matches[game_id][unique_team]['box_score'] - league_matches[game_id][opponent]['box_score'])

        # reset players to update if free throws are finished
        if (event != 3) and (event != 8) and (event != 11):
             # update players subbed out during a free throw
            if (len(active_after_ft) > 0):
                for unique_player in active_after_ft:
                    league_matches[game_id][unique_player['team_id']][unique_player['player_id']] -= (league_matches[game_id][unique_player['team_id']]['box_score'] - league_matches[game_id][unique_player['opponent_id']]['box_score'])

            if (len(sub_after_ft) > 0):
                for unique_player in sub_after_ft:
                    league_matches[game_id][unique_player['team_id']][unique_player['player_id']] += (league_matches[game_id][unique_player['team_id']]['box_score'] - league_matches[game_id][unique_player['opponent_id']]['box_score'])

            active_after_ft = []
            sub_after_ft = []

        # update score when shot is made
        if (event == 1) and (action != 0):
            league_matches[game_id][team_id]['box_score'] += option

        # update score after a free throw
        if (event == 3) and (option > 0) and (action != 0):
            league_matches[game_id][team_id]['box_score'] += 1

        # calculate plus minus for players subbed out
        if (event == 8) or (event == 11):
            current_team = team_id
            opponent = getOpponent(game, team_id)

            if (match_starters[game_id][team_id][period].get(player)) is None:
                current_team = opponent
                opponent = team_id

            if (league_matches[game_id][current_team].get(sub)) is None:
                league_matches[game_id][current_team][sub] = 0

            bench_player = {'team_id': current_team,
                            'player_id': player, 
                            'opponent_id': opponent
                            }
            active_player = {'team_id': current_team,
                             'player_id': sub, 
                             'opponent_id': opponent
                             }
            active_after_ft.append(active_player)
            sub_after_ft.append(bench_player)
            match_starters[game_id][current_team][period][player] = False
            match_starters[game_id][current_team][period][sub] = True

        # calculate plus minus for player at the end of the quarter
        if event == 13:
            teams = list(match_starters[game_id].keys())

            for unique_team in teams:
                opponent = getOpponent(game, unique_team)
                players = list(match_starters[game_id][unique_team][period].keys())

                for unique_player in players:
                    if match_starters[game_id][unique_team][period][unique_player] is True:
                        league_matches[game_id][unique_team][unique_player] += (league_matches[game_id][unique_team]['box_score'] - league_matches[game_id][opponent]['box_score'])

    return league_matches


def getOpponent(game, team_id):
    """This function determines the team_id of the opposing team 

    Args:
        game (object): A game dictionary containing the keys of both teams
        team_id (str): The current team id.

    Returns:
        str: The team_id of the opposing team

    """
    team_keys = [*game]
    opponent = list(filter(lambda x: x != team_id, team_keys))[0]
    return opponent


def write_plus_minus_csv(plus_minus_data):
    """This function writes the plus minus data 

    Args:
        plus_minus_data (object): A game dictionary containing the keys of both teams

    Returns:
        bool: True for success. False otherwise.

    """

    df = pd.read_csv('results/results_template.csv',
                     dtype={'Player_Plus/Minus': np.int8})

    for i, row in df.iterrows():
        game_id = row['Game_id']
        player = row['Person_id']

        current_game = plus_minus_data[game_id]
        team_keys = [*current_game]

        for team in team_keys:
            if plus_minus_data[game_id][team].get(player) is None:
                continue
            else:
                df.at[i, 'Player_Plus/Minus'] = plus_minus_data[game_id][team][player]

    df.to_csv('results/Q1_BBALL.csv', index=False)
    return True


def calc_plus_minus():
    """This function calculates the plus minus and writes a csv file"""
    league_matches, match_starters = process_match_lineups()
    results = process_game_logs(league_matches, match_starters)
    write_plus_minus_csv(results)


calc_plus_minus()