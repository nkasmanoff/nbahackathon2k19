#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created by Sarang Yeola and Noah Kasmanoff


Calculates the offensive and defensive (and net) ratings of each player in each game from the 2018 NBA Playoffs



The script below performs this by first loading in the play by play for every game in this set, along with the rosters of each team and associated starting lineup
for each period including overtimes (if any), and then event codes.txt in order to translate the events to occur in a game to readable values such as 
made shot, rebound, substitution, etc. 



There are flaws in the play by play dataset, such as incorrect assignments to teams during substitutions, as well as ambiguous rebounding conventions to correspond to offensive and defensive boards. 



These issues are fixed during the game being tested over, 
and then the corresponding score and possessoins are calculated, and player
ratings are assigned.




Currently spot checking game 1 of the NBA finals, and here are the associaated links
https://www.basketball-reference.com/boxscores/201805310GSW.html
https://stats.nba.com/players/advanced/?sort=TEAM_ABBREVIATION&dir=1&Season=2017-18&SeasonType=Playoffs&DateFrom=05%2F31%2F2018&DateTo=05%2F31%2F2018&PORound=4


"""
#%%


import pandas as pd
import warnings
warnings.filterwarnings("ignore")


pbp = pd.read_csv('Basketball Analytics/Play_by_Play.txt',delimiter='\t')
lineup = pd.read_csv('Basketball Analytics/Game_Lineup.txt',delimiter='\t')
codes = pd.read_csv('Basketball Analytics/Event_Codes.txt',delimiter = '\t')


def sub_correction(z,team_assignments):
    player1steam = team_assignments.loc[team_assignments['Person_id'] == z['Person1']]['Team_id'].values[0] #correctly assigned player. 
    player2steam = team_assignments.loc[team_assignments['Person_id'] == z['Person2']]['Team_id'].values[0] #correctly assigned player. 
   # if player
    if player1steam == player2steam:
        return player1steam
    
    else:
        return player2steam 
    
    
def technical_FT_correction(z,team_assignments):
    player1steam = team_assignments.loc[team_assignments['Person_id'] == z['Person1']]['Team_id'].values[0] #correctly assigned player. 
    return player1steam


def rebound_correction(z,team_assignments):
    player1steam = team_assignments.loc[team_assignments['Person_id'] == z['Person1']]['Team_id']
    
    try :
        if player1steam.values[0] == z['Team_id']:
            return "Offensive Rebound"
        else:
            return "Defensive Rebound"
    except:
        if z['Team_id_type'] == z['Person1_type']:
            return "Offensive Rebound-TEAM" #offensive
        else:
            return "Defensive Rebound-TEAM" #defensive


def freethrowexceptions(z):
    """
    
    Apply statement to encode end of a possession for free throws. 
    The tricky case here is confirm this is the final free throw attempt, and if it did not go in. 
    
    In other cases the other possession change flags will capture the end of the possession, 
    but this does.
    
    """
    
    if z['Event_Msg_Type'] == 3:
        if z['Action_Type_Description'].split(' ')[-1] == z['Action_Type_Description'].split(' ')[-3]:
            if z['Action_Type_Description'].split(' ')[-4] not in 'Flagrant Technical': #if final free throw
                if z['Option1'] == 1:    
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
    pbp_singlegame['Event_Msg_Type'] = pbp_singlegame['Event_Msg_Type'].astype(int)
    #first, sort according to event num, have to do this for possessions, but not other stuff. 
    pbp_singlegame.sort_values(['Event_Num'],
        ascending=[True],inplace=True)
        
    
    #create new column for each type of possession change, combine at the end. 
    pbp_singlegame['Poss Change 1'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 1 else False)
    pbp_singlegame['Poss Change Rebound'] = pbp_singlegame['Action_Type_Description'].apply(lambda z: True if 'Defensive' in z else False)
    
    #((pbp_singlegame['Team_id'] != pbp_singlegame['Team_id'].shift(-1)) & (pbp_singlegame['Event_Msg_Type_Description'].str.contains('Rebound')))   
    pbp_singlegame['Poss Change 5'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 5 else False)
    pbp_singlegame['Poss Change 13'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 13 else False)
    
    #merge all those possession change types together. 

   # return pbp_singlegame
    pbp_singlegame.sort_values(['Period','PC_Time','Option1','WC_Time','Event_Num'],
            ascending=[True,False,True,True,True],inplace=True)
    
    pbp_temp = pd.DataFrame()
    
    for _,g in pbp_singlegame.groupby(['PC_Time','Period'],sort = False):
       # print(g)
        if 'Free Throw 1 of 1' in g['Action_Type_Description'].unique():
            print("This was an and 1!")
            g['Poss Change 1'] = False
    
        pbp_temp = pbp_temp.append(g)
        
    
    pbp_singlegame = pbp_temp.copy(deep = True)
    pbp_singlegame['Poss Change 6'] = pbp_singlegame.apply(lambda z: freethrowexceptions(z),axis=1)

    pbp_singlegame.sort_values(['Period','PC_Time','Option1','WC_Time','Event_Num'],
            ascending=[True,False,True,True,True],inplace=True)
    print(pbp_singlegame.columns)
    pbp_singlegame['Poss Change'] = pbp_singlegame[pbp_singlegame.columns[-5:]].sum(axis=1)
    print(pbp_singlegame.columns)

    pbp_singlegame.drop(columns = pbp_singlegame.columns[-6:-1],inplace=True)
    print(pbp_singlegame.columns)
    pbp_singlegame.loc[pbp_singlegame['Action_Type_Description'].str.contains('Goaltending'), 'Poss Change'] = 0

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


def sub(playersin, bench, substitution,dead_ball_exception=False):
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

    fte : bool
        Boolean for whether or not to include free throw exception, and not add an additional poss in sub. 
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
    
    offensive_nposs1 = substitution['npossessions_x']
    offensive_nposs2 = substitution['npossessions_y'] 
    
    if teamid == teams[0]:
        
        diff = score1 - score2
        opts = score1 
        dpts = score2
        offensive_nposs = offensive_nposs1 
        defensive_nposs = offensive_nposs2
        print("offensive and defensive nposs: ", offensive_nposs, defensive_nposs )

        if not dead_ball_exception: 
            if substitution['Team_id_type'] == team_0_type:
                print("This was an offensive sub for team 0")
                offensive_nposs = offensive_nposs + 1
            else:
                print("This was a defensive sub for team 0")
                defensive_nposs = defensive_nposs + 1
    if teamid == teams[1]:
        diff = score2 - score1
        opts = score2
        dpts = score1
        offensive_nposs = offensive_nposs2 
        defensive_nposs = offensive_nposs1 
        print("offensive and defensive nposs: ", offensive_nposs, defensive_nposs )

        if not dead_ball_exception: 
            if substitution['Team_id_type'] == team_1_type:
               print("This was an offensive sub for team 1")
               offensive_nposs = offensive_nposs + 1
            else:
               print("This was a defensive sub for team 1")
               defensive_nposs = defensive_nposs + 1

    print("offensive and defensive nposs AFTER : ", offensive_nposs, defensive_nposs )

    suboutindex = (playersin['Person_id'] == suboutID)
  #  subinindex = (bench['Person_id'] == subinID)

    # calculates plus minus of the player at the subout index. 
    playersin.loc[suboutindex,'pm'] = playersin.loc[suboutindex,'pm']     + diff - playersin.loc[suboutindex,'diffin']

    playersin.loc[suboutindex,'opts'] = playersin.loc[suboutindex,'opts']     + opts -  playersin.loc[suboutindex,'plusin']
    playersin.loc[suboutindex,'dpts'] = playersin.loc[suboutindex,'dpts']     + dpts -  playersin.loc[suboutindex,'minusin']
    playersin.loc[suboutindex,'offensive_nposs'] = playersin.loc[suboutindex,'offensive_nposs']     + offensive_nposs -  playersin.loc[suboutindex,'off_possin']
    playersin.loc[suboutindex,'defensive_nposs'] = playersin.loc[suboutindex,'defensive_nposs']     + defensive_nposs -  playersin.loc[suboutindex,'def_possin']

    if teamid == teams[1]:
        if not dead_ball_exception:
            if substitution['Team_id_type'] == team_1_type:
               offensive_nposs = offensive_nposs - 1
            else:
               defensive_nposs = defensive_nposs - 1
           
    if teamid == teams[0]:
        if not dead_ball_exception:
            if substitution['Team_id_type'] == team_0_type:
               offensive_nposs = offensive_nposs - 1
            else:
               defensive_nposs = defensive_nposs - 1
           
    print("Players in shape before: ", playersin.shape)     
    playersin = playersin.append(bench.loc[bench['Person_id'] == subinID])
    print("Players in shape after: ", playersin.shape)     

    bench = bench.loc[~(bench['Person_id'] == subinID)]
        
    bench = bench.append(playersin.loc[playersin['Person_id'] == suboutID]) #now bench is appended with this player and his updated stuff, and likewise removed from players in df. 
    playersin = playersin.loc[~(playersin['Person_id'] == suboutID)]
    print("Players in shape after again: ", playersin.shape)     

    # set the score difference for new player
    playersin.loc[playersin['Person_id'] == subinID, 'diffin'] = diff
    playersin.loc[playersin['Person_id'] == subinID, 'plusin'] = opts #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 
    playersin.loc[playersin['Person_id'] == subinID, 'minusin'] = dpts #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 
    
    playersin.loc[playersin['Person_id'] == subinID, 'off_possin'] = offensive_nposs  #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 
    playersin.loc[playersin['Person_id'] == subinID, 'def_possin'] = defensive_nposs  #whatever the score is at that time, in order to remove points scored when the player wasn't on the court. 


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
    print("Period: ", period)
    # identify who is coming in at the start of the period
    periodstarters = lineup.loc[(lineup['Game_id'] == game) & (lineup['Period'] == period)]
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
    
    diff1 = score1 - score2
    diff2 = score2 - score1
    
    # calculate plus minus for everyone at the end of the period
    playersin.loc[playersin['Team_id'] == teams[0], 'pm']  = playersin.loc[playersin['Team_id'] == teams[0],'pm']  + diff1 - playersin.loc[playersin['Team_id'] == teams[0],'diffin']
    playersin.loc[playersin['Team_id'] == teams[1], 'pm']  = playersin.loc[playersin['Team_id'] == teams[1],'pm']  + diff2 - playersin.loc[playersin['Team_id'] == teams[1],'diffin']
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
box_score_ratings = pd.DataFrame()
 
for game,pbp_singlegame in pbp.groupby('Game_id',sort = False):
    teams = lineup.loc[lineup['Game_id'] == game]['Team_id'].unique() #locate the two teams in the game. 
    print("game id: ", game)

    ejection_df = pbp_singlegame.loc[(pbp_singlegame['Event_Msg_Type'] == 11)]# & (pbp_singlegame['Action_Type'] == 16)]
    team_0_type =pbp_singlegame.loc[pbp_singlegame['Team_id'] == teams[0]]['Team_id_type'].value_counts().index[0]
    team_1_type = pbp_singlegame.loc[pbp_singlegame['Team_id'] == teams[1]]['Team_id_type'].value_counts().index[0]

    #translate using codes
    pbp_singlegame = pbp_singlegame.merge( codes,
        on = ['Event_Msg_Type', 'Action_Type'], how = 'left')

    pbp_singlegame = pbp_singlegame.loc[pbp_singlegame['Period'] == 2]
   # #obtain starting lineups
    starting_lineup = lineup.loc[(lineup['Game_id'] == game) & (lineup['status'] == 'A')] #starting lineup of the game
    team_assignments = lineup.loc[(lineup['Game_id'] == game) & (lineup['Period'] == 0)] #starting lineup of the game
    
    subs = pbp_singlegame.loc[pbp_singlegame['Event_Msg_Type'] == 8]
    subs['Team_id'] = subs.apply(lambda z: sub_correction(z,team_assignments),axis=1)
    pbp_singlegame[pbp_singlegame['Event_Msg_Type'] == 8] = subs
    
        
    #fix technical free throws, must make 
    try:
        techfts =  pbp_singlegame.loc[pbp_singlegame['Action_Type_Description'].str.contains('Free Throw Technical')]
        techfts['Team_id'] = techfts.apply(lambda z: technical_FT_correction(z,team_assignments),axis=1)
        pbp_singlegame.loc[pbp_singlegame['Action_Type_Description'].str.contains('Free Throw Technical')] = techfts
        print('Found technical fouls!')

    except: #if no techs, good. 
        pass
    
    
    rebounds = pbp_singlegame.loc[pbp_singlegame['Event_Msg_Type'] == 4]
    rebounds['Action_Type_Description'] = rebounds.apply(lambda z: rebound_correction(z,team_assignments),axis=1)
    pbp_singlegame[pbp_singlegame['Event_Msg_Type'] == 4] = rebounds

    pbp_singlegame = pbp_singlegame.sort_values(['Period','PC_Time','Event_Msg_Type','WC_Time','Event_Num'],
        ascending=[True,False,True,True,True])
    pbp_singlegame = score_aggregator(pbp_singlegame)
    pbp_singlegame['Option1'] = pbp_singlegame.apply(lambda z: 10 if z['Event_Msg_Type'] == 8 else z['Option1'],axis=1)
    pbp_singlegame['Option1'] = pbp_singlegame.apply(lambda z: 10 if z['Event_Msg_Type'] == 9 else z['Option1'],axis=1)

    pbp_singlegame = possession_flagger(pbp_singlegame)
    
    
    playersin = pd.DataFrame(starting_lineup.loc[(starting_lineup['Period'] == 1),['Team_id','Person_id']])
    
    bench = pd.DataFrame(starting_lineup.loc[(starting_lineup['Period'] == 0) ,['Team_id','Person_id']])  #all players associated with a game. 
    bench = bench[~bench['Person_id'].isin(playersin['Person_id'])]
    
    #Initialize point differential both game and players for the dataset. 
    playersin['diffin'] = playersin['pm'] = playersin['plusin'] = playersin['opts'] = 0
    playersin['minusin'] = playersin['dpts'] = playersin['offensive_nposs'] = playersin['off_possin'] =0
    playersin['defensive_nposs'] = playersin['def_possin'] = 0
    bench['diffin'] = bench['pm'] = bench['plusin'] = bench['opts'] = 0
    bench['minusin'] = bench['dpts'] = bench['offensive_nposs'] = bench['off_possin'] = 0
    bench['defensive_nposs'] = bench['def_possin'] = 0 
    pbp_singlegame['Event_Msg_Type'] = pbp_singlegame.apply(lambda z: 4.5 if 'Defensive Rebound' in z['Action_Type_Description'] else z['Event_Msg_Type'],axis = 1)
    i = 0
    for index, row in pbp_singlegame.iterrows():

        if (row['Event_Msg_Type'] == 8):
            print(index)
            print("SUB!")
            
            #attempted code for dead ball exception. This will handle subs at the end of FTs, 
            #and after turnovers. 
            
            
            period = row['Period']
            print("PERIOD", period)
            pc_time = row['PC_Time']
            
            pc_group = pbp_singlegame.loc[(pbp_singlegame['PC_Time'] == pc_time) & (pbp_singlegame['Period'] == period)]
            pc_group_codes = pc_group['Event_Msg_Type'].unique()[pc_group['Event_Msg_Type'].unique() != 20]

            print(pc_group_codes)
            print(pc_group.index)
            
            if 6 in pc_group_codes and 3 in pc_group_codes:
                print("Foul!")
                row['Team_id_type'] = pc_group.loc[pc_group['Event_Msg_Type'] == 6]['Team_id_type'].values[0]
       #     if len(pc_group_codes) > 1:
           
           
           
            if 3 in pc_group_codes: #mid free throw
                ft_pcs = pc_group.loc[pc_group['Event_Msg_Type'] == 3]
                ft_pcs.sort_values('Action_Type_Description',inplace=True)
                print("Max action type of FT:")
                print( ft_pcs['Action_Type'].max() )
                if ft_pcs['Action_Type'].max() < 16: # not a tech or flagrant, or clear path
                    
                    if ft_pcs['Option1'].values[-1]  != 1:
                        print("Dead ball not in effect, that last FT missed!")

                        dead_ball_exception = False
                    
                    if ft_pcs['Option1'].values[-1] == 1:
                        print("Dead ball in effect, that last FT went in")

                        dead_ball_exception = True
                else:
                    print("Flagrant or tech!" )
                    dead_ball_exception=  False
            elif 5 in pc_group_codes: #mid turnover
                print("Dead ball in effect.")
                dead_ball_exception = True
                
            elif 1 in pc_group_codes and 9 in pc_group_codes: #made shot, timeout!
                print("Dead ball in effect. MADE SHOT TO")
                dead_ball_exception = True
            elif 4.5 in pc_group_codes and 9 in pc_group_codes: #defensive rebound, timeout!
                dead_ball_exception = True

            else:
                dead_ball_exception = False
                
            print("Dead ball? ", dead_ball_exception)
            playersin, bench = sub(playersin, bench, row,dead_ball_exception)  #calculate +/- of subout.

          #  print(row['Team_id'])           # if i == 10:
        
        elif (row['Event_Msg_Type'] == 13):
            playersin, bench = endperiod(playersin, bench, row)  #calculate +/- at end of period,
            i +=1
        #    if i ==2:
        #        break
        elif (row['Event_Msg_Type'] == 12):
            playersin, bench = startperiod(playersin, bench, row) #update lineups
            

    pm = pd.concat([playersin,bench],axis=0)#[['Person_id','Team_id','pm','opts','dpts','offensive_nposs','defensive_nposs']]
    pm['Game_id'] = game


    box_score_ratings = box_score_ratings.append(pm)
pbp_viewer = pbp_singlegame[['Period','Team_id','Team_id_type','Event_Msg_Type_Description','Action_Type_Description','score_x','Poss Change','score_y','npossessions_x','npossessions_y']].copy()

#%%

box_score_ratings['OffRtg'] = 100 * box_score_ratings['opts'] / box_score_ratings['offensive_nposs']
box_score_ratings['DefRtg'] = 100 * box_score_ratings['dpts'] / box_score_ratings['defensive_nposs']
#%%
box_score_ratings = box_score_ratings[['Game_id','Person_id','OffRtg','DefRtg']]
box_score_ratings.rename(columns = {'Game_id':'Game_ID',"Person_id":"Player_ID"},inplace=True)
box_score_ratings.fillna(0,inplace=True)
#%%

box_score_ratings.to_csv('FunGuys_Q1_BBALL.csv',index=False)