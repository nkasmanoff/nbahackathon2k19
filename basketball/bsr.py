#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 10:54:50 2019

@author: noahkasmanoff


Contained in this script is the collection of total # of offensive points scored while a player is on the court. 

The next step is to generalize this for defensive points allowed while on the court, and make an additional counter for 
possessions to have occured. 


This is wrong, but right. 

"""

import pandas as pd
import warnings
warnings.filterwarnings("ignore")


def substitution_correction(subs,lineup):
    """
    
    Go through a game dataframe. Correct and confirm that the
    substitution team assignments are correct.

    Parameters
    ----------

    subs : df
        pandas dataframe of every substitution to occur during a game.

    lineups : df
        provided data, the lineup for that given game

    Returns
    -------

    subs : df
        Corrected version of subs where the
        team assignments for the player are correct.

    """
    
    #Step 1 of cleaning, delete extra cols and make a person1 col to merge w/ subs.
    lineup['Person1'] = lineup['Person_id']    
    
    del lineup['Period'],lineup['status'],lineup['Game_id']
    del subs['Team_id']
    
    first = pd.merge(subs, lineup,
        on = ['Person1'], how = 'left')
    first.drop_duplicates(inplace=True)
    del lineup['Person1']
    
    
    weird = first[['Person2','Team_id']]  #now act in parralel. make a df of "first" with only nan cols.
    #and weird has every col except but just p2 and team.
    nanmask = first['Team_id'].isna().values
    weird = weird[~nanmask]
    nanfirst = first[nanmask]
    nanfirst.dropna(axis=1,inplace=True) #remove nan columns to be added back on
    weird['Person1'] = weird['Person2']
    weird = weird[['Person1','Team_id']]
    
    second = pd.merge(nanfirst, weird,
        on = ['Person1'], how = 'left')
    del first['Person_id']
    second.drop_duplicates(inplace=True) #remove extraneious cols and shove this into the first[nanmask]!
    if len(second.values) >0:
        first[nanmask] = second.values #and that's it.

    subs = first[['Game_id','Event_Num','Event_Msg_Type','Period','WC_Time','PC_Time','Action_Type','Option1','Option2',
                'Option3','Team_id','Person1','Person2','Team_id_type','Event_Msg_Type_Description']]

    corrected_subs = subs
    return corrected_subs


def freethrowexceptions(z):
    """Apply statement to encode end of a possession for free throws. 
    The tricky case here is confirm this is the final free throw attempt, and if it did not go in. 
    
    In other cases the other possession change flags will capture the end of the possession, 
    but this does.
    
    """
    
    if z['Event_Msg_Type'] == 3:
        if z['Action_Type_Description'].split(' ')[-1] == z['Action_Type_Description'].split(' ')[-3]: #if final free throw
                
            if z['Option1'] == 1 and z['Action_Type_Description'].split(' ')[-1] != '1':
                    #made final free throw. 
                    return True
      
    
    return False


def possession_flagger(pbp_singlegame):
    """
    
    Flags the end of a possession as designated by the rules for this question, and creates a counter similar
    to the one for points scored of each team, denoting the total # of possessions that team has 
    throughout the game. 
    
    Parameters
    ----------
    
    pbp_singlegame : dataframe
        Pandas dataframe of the play by play of the game, already slightly modified. 
        
    Returns
    -------
    
    pbp_singlegame : dataframe
        Pandas dataframe of the play by play of the game, even more modified such that the possesions of each team is now
        attached. 
    
    
    """
    #first, sort according to event num, have to do this for possessions, but not other stuff. 
    pbp_singlegame.sort_values(['Event_Num'],
        ascending=[True],inplace=True)
        
    
    #create new column for each type of possession change, combine at the end. 
    pbp_singlegame['Poss Change 1'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 1 else False)
    pbp_singlegame['Poss Change Rebound'] = ((pbp_singlegame['Team_id'] != pbp_singlegame['Team_id'].shift(-1)) & (pbp_singlegame['Event_Msg_Type_Description'].str.contains('Rebound')))   
    pbp_singlegame['Poss Change 5'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 5 else False)
    pbp_singlegame['Poss Change 13'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 13 else False)
    pbp_singlegame['Poss Change 6'] = pbp_singlegame.apply(lambda z: freethrowexceptions(z),axis=1)
    
    #merge all those possession change types together. 
    pbp_singlegame['Poss Change'] = pbp_singlegame[pbp_singlegame.columns[-5:]].sum(axis=1)
    pbp_singlegame.drop(columns = pbp_singlegame.columns[-6:-1],inplace=True)
   # return pbp_singlegame
    pbp_singlegame.sort_values(['Period','PC_Time','Option1','WC_Time','Event_Num'],
            ascending=[True,False,True,True,True],inplace=True)
    
    pbp_singlegame['npossessions'] = pbp_singlegame.groupby('Team_id', axis = 0,sort=False)['Poss Change'].cumsum()

    team1npossessions = pbp_singlegame.loc[pbp_singlegame.iloc[:,10] == teams[0]]
    team2npossessions = pbp_singlegame.loc[pbp_singlegame.iloc[:,10] == teams[1]]
    del pbp_singlegame['npossessions'] #this is because it copies, don't do this. 
    
    pbp_singlegame = pd.merge(pbp_singlegame, team1npossessions.loc[:,['Event_Num','npossessions']], on = 'Event_Num', how = 'left')
    pbp_singlegame = pd.merge(pbp_singlegame, team2npossessions.loc[:,['Event_Num','npossessions']], on = 'Event_Num', how = 'left')

    # fill forward for NaNs
    pbp_singlegame.loc[:,['npossessions_x', 'npossessions_y']] = pbp_singlegame.loc[:,['npossessions_x', 'npossessions_y']].fillna(method = 'ffill')
    pbp_singlegame.loc[:,['npossessions_x', 'npossessions_y']] = pbp_singlegame.loc[:,['npossessions_x', 'npossessions_y']].fillna(0) # for the start of the game
    return pbp_singlegame


def score_aggregator(pbp_singlegame):
    """
    
    Aggregates the score of the game. 

    Parameters
    ----------
    
    pbp_singlegame : dataframe
        Pandas dataframe of the play by play of the game. 
        
    Returns
    -------
    
    pbp_singlegame : dataframe
        Pandas dataframe of the play by play of the game, even more modified such that the score of each team is now
        attached. 
    
        
    """
    
    #first, make all non-scoring plays have their option 1 value equal 0. This is the value corresponding to made points anyway. 
    
    pbp_singlegame.loc[(pbp_singlegame['Event_Msg_Type'] == 3)&(pbp_singlegame['Option1'] != 1), 'Option1'] = 0
    pbp_singlegame.loc[pbp_singlegame['Event_Msg_Type'] == 2, 'Option1'] = 0
    pbp_singlegame.loc[pbp_singlegame['Event_Msg_Type'] == 5, 'Option1'] = 0
    pbp_singlegame.loc[pbp_singlegame['Event_Msg_Type'] == 6, 'Option1'] = 0
    
    pbp_singlegame['score'] = pbp_singlegame.groupby('Team_id', axis = 0,sort=False)['Option1'].cumsum()
    team1score = pbp_singlegame.loc[pbp_singlegame.iloc[:,10] == teams[0]]
    team2score = pbp_singlegame.loc[pbp_singlegame.iloc[:,10] == teams[1]]
    del pbp_singlegame['score'] #this is because it copies, don't do this. 
    
    pbp_singlegame = pd.merge(pbp_singlegame, team1score.loc[:,['Event_Num','score']], on = 'Event_Num', how = 'left')
    pbp_singlegame = pd.merge(pbp_singlegame, team2score.loc[:,['Event_Num','score']], on = 'Event_Num', how = 'left')

    # fill forward for NaNs
    pbp_singlegame.loc[:,['score_x', 'score_y']] = pbp_singlegame.loc[:,['score_x', 'score_y']].fillna(method = 'ffill')
    pbp_singlegame.loc[:,['score_x', 'score_y']] = pbp_singlegame.loc[:,['score_x', 'score_y']].fillna(0) # for the start of the game
    
    return pbp_singlegame


def sub(playersin, bench, substitution):
    """
    
    Function to calculate plus/minus for individuals when they subout
    and calculate difference when subbing in.

    Parameters
    ----------

    playersin : df
        dataframe of players on the court, has columns 'Team_id', 'Person_id', diffin
        and 'pm'

    bench : df
        dataframe of players on the bench, has columns 'Team_id', 'Person_id', diffin
        and 'pm'

    substitution : df
        a single row from the play-by-play dataframe for which the substitution occurs
        Event Msg Type: 8

    Returns :
    playersin, bench
    -------
    """

    teamid = substitution['Team_id']
    print('teamid',teamid)
    suboutID = substitution['Person1']
    subinID = substitution['Person2']
    score1 = substitution['score_x']
    score2 = substitution['score_y']
    
    offensive_nposs1 = substitution['npossessions_x'] +1
    offensive_nposs2 = substitution['npossessions_y'] + 1

    if teamid == teams[0]:
        diff = score1 - score2
        opts = score1
        dpts = score2
        offensive_nposs = offensive_nposs1
        defensive_nposs = offensive_nposs2

    else:
        diff = score2 - score1
        opts = score2
        dpts = score1
        offensive_nposs = offensive_nposs2
        defensive_nposs = offensive_nposs1

    suboutindex = (playersin['Person_id'] == suboutID)

    # calculates plus minus of the player at the subout index. 
    playersin.loc[suboutindex,'pm'] = playersin.loc[suboutindex,'pm']     + diff - playersin.loc[suboutindex,'diffin']
    #maybe an if statement for this being the first time being subbed out? 
    playersin.loc[suboutindex,'opts'] = playersin.loc[suboutindex,'opts']     + opts -  playersin.loc[suboutindex,'plusin']
    playersin.loc[suboutindex,'dpts'] = playersin.loc[suboutindex,'dpts']     + dpts -  playersin.loc[suboutindex,'minusin']
    playersin.loc[suboutindex,'offensive_nposs'] = playersin.loc[suboutindex,'offensive_nposs']     + offensive_nposs -  playersin.loc[suboutindex,'off_possin']
    playersin.loc[suboutindex,'defensive_nposs'] = playersin.loc[suboutindex,'defensive_nposs']     + defensive_nposs -  playersin.loc[suboutindex,'def_possin']

    if ~bench['Person_id'].str.contains(subinID).any(): # if the player isn't in the "bench" df, which is means the player was subbed out. 
                                                        
            playersin = playersin.append(
            {'Team_id': teamid, 'Person_id':subinID, 'diffin':diff, 'pm':0,
             'plusin':0,'opts':0,'minusin':0,'dpts':0,'off_possin':0,'offensive_nposs':0,
            'def_possin':0,'defensive_nposs':0},
            ignore_index = True)   #initializes that player as 0s
                    
    else: # if he's in the benchdf already, 
        playersin = playersin.append(bench.loc[bench['Person_id'] == subinID])
        bench = bench.loc[~(bench['Person_id'] == subinID)]
        
    bench = bench.append(playersin.loc[playersin['Person_id'] == suboutID]) #now bench is appended with this player and his updated 
    playersin = playersin.loc[~(playersin['Person_id'] == suboutID)]

    # set the score difference for new player
    playersin.loc[playersin['Person_id'] == subinID, 'diffin'] = diff
    playersin.loc[playersin['Person_id'] == subinID, 'plusin'] = opts #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 
    playersin.loc[playersin['Person_id'] == subinID, 'minusin'] = dpts #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 
    playersin.loc[playersin['Person_id'] == subinID, 'off_possin'] = offensive_nposs #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 
    playersin.loc[playersin['Person_id'] == subinID, 'def_possin'] = defensive_nposs #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 


    return playersin, bench



def startperiod(playersin, bench, startrow):
    """ 
    
    Function to switch out players at the start of the period
    and calculate the score difference coming in

    Parameters
    ----------

    playersin : df
        dataframe of players on the court, has columns 'Team_id', 'Person_id', diffin
        and 'pm'

    bench : df
        dataframe of players on the bench, has columns 'Team_id', 'Person_id', diffin
        and 'pm'

    startrow : df
        a single row from the play-by-play dataframe for which the start of the period occurs
        Event Msg Type: 12

    Returns 
    -------

    playersin, bench
    """

    score1 = startrow['score_x']
    score2 = startrow['score_y']
    offensive_nposs1 = startrow['npossessions_x']
    offensive_nposs2 = startrow['npossessions_y']
    diff = score1 - score2
    period = startrow['Period']

    # identify who is coming in at the start of the period
    periodstarters = lineup.loc[(lineup['Game_id'] == game) & (lineup['Period'] == period)]
    allplayers = pd.concat([bench, playersin])

    # allocate players going in and those on the bench
    playersintemp = pd.concat([
            playersin.loc[playersin['Person_id'].isin(periodstarters['Person_id'])], \
            bench.loc[bench['Person_id'].isin(periodstarters['Person_id'])]
        ])
    benchtemp = pd.concat([
            bench.loc[~bench['Person_id'].isin(periodstarters['Person_id'])], \
            playersin.loc[~playersin['Person_id'].isin(periodstarters['Person_id'])]
        ])

    playersin = playersintemp
    bench = benchtemp

    # check to see if there are players first coming in at the start of the period
    check = periodstarters['Person_id'].isin(allplayers['Person_id'])
    if ~check.all():
        newplayers = periodstarters.loc[~check]
        for index,newplayer in newplayers.iterrows():
            playersin = playersin.append(
                {'Team_id': newplayer['Team_id'],
                 'Person_id': newplayer['Person_id'],
                 'diffin':0,
                 'pm':0,
                 'plusin':0,
                 'opts':0,
                 'minusin':0,
                 'dpts':0,
                 'off_possin':0,
                 'offensive_nposs':0,
                'def_possin':0,
                'defensive_nposs':0},
                ignore_index = True)

    # set the score difference for all players at the start of the period
    playersin.loc[playersin['Team_id'] == teams[0],'diffin'] = diff
    playersin.loc[playersin['Team_id'] == teams[1],'diffin'] = -diff
    
    playersin.loc[playersin['Team_id'] == teams[0],'plusin'] = score1
    playersin.loc[playersin['Team_id'] == teams[1],'plusin'] = score2
    
    playersin.loc[playersin['Team_id'] == teams[0],'minusin'] = score2
    playersin.loc[playersin['Team_id'] == teams[1],'minusin'] = score1
    
    playersin.loc[playersin['Team_id'] == teams[0],'off_possin'] = offensive_nposs1
    playersin.loc[playersin['Team_id'] == teams[1],'off_possin'] = offensive_nposs2  

    playersin.loc[playersin['Team_id'] == teams[0],'def_possin'] = offensive_nposs2
    playersin.loc[playersin['Team_id'] == teams[1],'def_possin'] = offensive_nposs1  


    return playersin, bench


def endperiod(playersin, bench, endrow):
    """ Function to calculate the plus minus for everyone at the end of the period

    Parameters
    ----------

    playersin : df
        dataframe of players on the court, has columns 'Team_id', 'Person_id', diffin
        and 'pm'

    bench : df
        dataframe of players on the bench, has columns 'Team_id', 'Person_id', diffin
        and 'pm'

    startrow : df
        a single row from the play-by-play dataframe for which the start of the period occurs
        Event Msg Type: 12

    Returns :
    playersin, bench
    -------
    
    """

    score1 = endrow['score_x']
    score2 = endrow['score_y']
    
    offensive_nposs1 = endrow['npossessions_x']
    offensive_nposs2 = endrow['npossessions_y']
    
    diff = score1 - score2
    
    # calculate plus minus for everyone at the end of the period
    playersin.loc[playersin['Team_id'] == teams[0], 'pm']  = playersin.loc[playersin['Team_id'] == teams[0],'pm']  + diff - playersin.loc[playersin['Team_id'] == teams[0],'diffin']
    playersin.loc[playersin['Team_id'] == teams[1], 'pm']  = playersin.loc[playersin['Team_id'] == teams[1],'pm']  - diff - playersin.loc[playersin['Team_id'] == teams[1],'diffin']
       # 
    playersin.loc[playersin['Team_id'] == teams[0], 'opts']  = playersin.loc[playersin['Team_id'] == teams[0],'opts']  +score1 - playersin.loc[playersin['Team_id'] == teams[0],'plusin']
    playersin.loc[playersin['Team_id'] == teams[0], 'dpts']  = playersin.loc[playersin['Team_id'] == teams[0],'dpts']  +score2 - playersin.loc[playersin['Team_id'] == teams[0],'minusin']

    playersin.loc[playersin['Team_id'] == teams[1], 'opts']  = playersin.loc[playersin['Team_id'] == teams[1],'opts']  +score2- playersin.loc[playersin['Team_id'] == teams[1],'plusin']
    playersin.loc[playersin['Team_id'] == teams[1], 'dpts']  = playersin.loc[playersin['Team_id'] == teams[1],'dpts']  +score1 - playersin.loc[playersin['Team_id'] == teams[1],'minusin']


    playersin.loc[playersin['Team_id'] == teams[0], 'offensive_nposs']  = playersin.loc[playersin['Team_id'] == teams[0],'offensive_nposs']  + offensive_nposs1 - playersin.loc[playersin['Team_id'] == teams[0],'off_possin']
    playersin.loc[playersin['Team_id'] == teams[1], 'offensive_nposs']  = playersin.loc[playersin['Team_id'] == teams[1],'offensive_nposs']  + offensive_nposs2 - playersin.loc[playersin['Team_id'] == teams[1],'off_possin']
   
    playersin.loc[playersin['Team_id'] == teams[0], 'defensive_nposs']  = playersin.loc[playersin['Team_id'] == teams[0],'defensive_nposs']  + offensive_nposs2 - playersin.loc[playersin['Team_id'] == teams[0],'def_possin']
    playersin.loc[playersin['Team_id'] == teams[1], 'defensive_nposs']  = playersin.loc[playersin['Team_id'] == teams[1],'defensive_nposs']  + offensive_nposs1 - playersin.loc[playersin['Team_id'] == teams[1],'def_possin']
       
    return playersin, bench



#%%
#load in data. 
pbp = pd.read_csv('Basketball Analytics/Play_by_Play.txt',delimiter='\t')
lineup = pd.read_csv('Basketball Analytics/Game_Lineup.txt',delimiter='\t')
codes = pd.read_csv('Basketball Analytics/Event_Codes.txt',delimiter = '\t')

sample_games = pbp['Game_id'].unique()

for game_num in range(len(sample_games))[0:1]:
    pbp = pd.read_csv('Basketball Analytics/Play_by_Play.txt',delimiter='\t')
    lineup = pd.read_csv('Basketball Analytics/Game_Lineup.txt',delimiter='\t')
    codes = pd.read_csv('Basketball Analytics/Event_Codes.txt',delimiter = '\t')

    game = sample_games[game_num] # for now, not iterative.
    print("game id: ", game)
    print("game num: ",game_num)
    teams = lineup.loc[lineup['Game_id'] == game]['Team_id'].unique() #locate the two teams in the game. 
    
    
    #sort according to this, it may end up changing . 
    pbp_singlegame = pbp.loc[pbp['Game_id'] == sample_games[game_num]] 
    
    #translate using codes
    pbp_singlegame = pbp_singlegame.merge( codes,
        on = ['Event_Msg_Type', 'Action_Type'], how = 'left')
    
    #obtain starting lineups
    starting_lineup = lineup.loc[(lineup['Game_id'] == game)] #starting lineup of the game
    
    subsmask = pbp_singlegame['Event_Msg_Type'] == 8
    subs = pbp_singlegame[subsmask] #dataframe of all substitutions. 
    
    
    playersin = pd.DataFrame(starting_lineup.loc[(starting_lineup['Period'] == 1),['Team_id','Person_id']])
    subs_correct = substitution_correction(subs,starting_lineup)
    pbp_singlegame[subsmask] =  subs_correct #fixes substitutions, and cofnirms taem names are correct. 
    subs = pbp_singlegame[subsmask] 
    pbp_singlegame = pbp_singlegame.sort_values(['Period','PC_Time','WC_Time','Event_Num'],
        ascending=[True,False,True,True])
    
    pbp_singlegame = possession_flagger(pbp_singlegame)
    pbp_singlegame = score_aggregator(pbp_singlegame)
    
    #Initialize point differential both game and players for the dataset. 
    playersin['diffin'] = playersin['pm'] = playersin['plusin'] = playersin['opts'] = 0
    playersin['minusin'] = playersin['dpts'] = playersin['offensive_nposs'] = playersin['off_possin'] =0
    playersin['defensive_nposs'] = playersin['def_possin'] = 0
    bench = pd.DataFrame(columns = ['Team_id', 'Person_id', 'diffin', 'pm','plusin','opts','minusin','dpts','off_possin','offensive_nposs','def_possin','defensive_nposs'])
    #
    for index, row in pbp_singlegame.iterrows():
        if (row['Event_Msg_Type'] == 8):
            playersin, bench = sub(playersin, bench, row)  #calculate +/- of subout.
        elif (row['Event_Msg_Type'] == 13):
            playersin, bench = endperiod(playersin, bench, row)  #calculate +/- at end of period,
        elif (row['Event_Msg_Type'] == 12):
            playersin, bench = startperiod(playersin, bench, row) #update lineups

pm = pd.concat([playersin,bench],axis=0)#[['Person_id','Team_id','pm','opts','dpts','offensive_nposs','defensive_nposs']]


box_score_ratings = pd.DataFrame()
box_score_ratings['Person_id'] = pm['Person_id']
box_score_ratings['Team_id'] = pm['Team_id']

box_score_ratings['ORTG'] = 100 * pm['opts'] / pm['offensive_nposs']
box_score_ratings['DRTG'] = 100 * pm['dpts'] / pm['defensive_nposs']

#%%