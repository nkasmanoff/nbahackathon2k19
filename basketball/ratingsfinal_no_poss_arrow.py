#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created by Sarang Yeola and Noah Kasmanoff


Calculates the offensive and defensive (and net) ratings of each player in each game from the 2018 NBA Playoffs



The script below performs this by first loading in the play by play for every game in this set, along with the rosters of each team and associated starting lineup
for each period including overtimes (if any), and then event codes.txt in order to translate the events to occur in a game to readable values such as 
made shot, rebound, substitution, etc. 





There are flaws in the play by play dataset, such as incorrect assignments to teams during substitutions, as well as ambiguous rebounding conventions to correspond to offensive and defensive boards. 

First these issues are fixed during the game being tested over, and then the corresponding score, 



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
      #      g['Poss Change Rebound'] = False 
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

#Here I just loop over 1 game, but then replace it to a game of interest. In this case,
# I did it for game 2 of the Warriors Pelicans Series. The first game in the loop is the 92-102 Raptors Wizards game talked about in the top most part of the code. 

box_score_ratings = pd.DataFrame()
i = 0
for game in pbp['Game_id'].unique()[0:1]:#[14:15]: 
    print("game id: ", game)
    teams = lineup.loc[lineup['Game_id'] == game]['Team_id'].unique() #locate the two teams in the game. 
    
    
    #sort according to this, it may end up changing . 
    pbp_singlegame = pbp.loc[pbp['Game_id'] == game] 
    ejection_df = pbp_singlegame.loc[(pbp_singlegame['Event_Msg_Type'] == 11)]# & (pbp_singlegame['Action_Type'] == 16)]
    team_0_type =pbp_singlegame.loc[pbp_singlegame['Team_id'] == teams[0]]['Team_id_type'].value_counts().index[0]
    team_1_type = pbp_singlegame.loc[pbp_singlegame['Team_id'] == teams[1]]['Team_id_type'].value_counts().index[0]

    #translate using codes
    pbp_singlegame = pbp_singlegame.merge( codes,
        on = ['Event_Msg_Type', 'Action_Type'], how = 'left')

   # pbp_singlegame = pbp_singlegame.loc[pbp_singlegame['Period'] == 2]

    #obtain starting lineups
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
            pc_group_codes = pc_group_codes[pc_group_codes != 6]

            print(pc_group_codes)
            print(pc_group.index)
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



pid_dict = {'Jordan Clarkson'	:'e49b2cc3f9aacd500b11a35b1c57112d',

'Larry Nance'	:'942a84f05f4ab956125f68ec0963481f',
'Kyle Korver'	:'32c044aa84d75ccd78c3c9f2aeb33bd9',
'Kevin Love'	:'95920e4bf5b6c15ba8dffbf959b38ba5',
'George Hill'	:'722a380c9b59ef42226e8d392824dcb9',
'JR Smith'	:'7f438c18058290903c46dfe9d71bd68a',
'Lebron James'	:'fb64ca4b8beaf4c4c6e4575fe2f3abd7',
'Jeff Green'	:'1dabb767e07d0aa702ee58d41c15eab1',
'Tristan Thompson'	:'ef8b068ab7ac9d387b256404acd24cd5',
	
'Patrick McCaw'	:'821887f9a002be16b5f79729fae59e01',
'Kevon Looney'	:'6f6a807d57aae8f651222523dc82dc35',
'Jordan Bell'	:'3d75035d20b173a867d4bf32c8a58f0b',
'Nick Young'	:'0b978fcfa7f2ec839c563a755e345ff8',
'Quinn Cook'	:'fbcda0bcb861e4726ca8871b8965ede4',
'Javale McGee': 'bfef77a3e57907855444410d490e7bfd',
'David West'	:'255fe2a8be0ed5c06dd99969ab4fea55',
'Klay Thompson':'31598ba01a3fff03ed0a87d7dea11dfe',
'Draymond Green'	:'a1591595c04d12e88e3cb427fb667618',
'Steph Curry'	:'1a6703883f8f47bb4daf09c03be3bda2',
'Shaun Livingston'	:'52c6125836c465f4ac5232121dacb49d',
'Kevin Durant'	:'3626b893fc73a5cbd67d1ea48a5c7039',
"Klay Thompson"	:"31598ba01a3fff03ed0a87d7dea11dfe",
"Draymond Green"	:"a1591595c04d12e88e3cb427fb667618",
"Kevin Durant":	"3626b893fc73a5cbd67d1ea48a5c7039",
"Andre Iguodola":	"ff59dc439c6c323320bc355afe884fcb",
"Steph Curry"	:"1a6703883f8f47bb4daf09c03be3bda2",

"Nick Young"	:"0b978fcfa7f2ec839c563a755e345ff8",
"David West"	:"255fe2a8be0ed5c06dd99969ab4fea55",
"Shaun Livingston":	"52c6125836c465f4ac5232121dacb49d",
"Kevon Looney":	"6f6a807d57aae8f651222523dc82dc35",

"Jrue Holiday": 	"ff52c317e26534ae1679da3c917e9fec",
"Anthony Davis"	:"7dfbb5980c066844384ba7424aceae47",
"Rajon Rondo":	"83c15c0962941640faab838a8f6f151d",
"ETwaun Moore":	"6ad10958a1d4920dccb1daec39bebd6b",
"Nikola Mirotic": "a3bac86ad549b2f128a62399d73d6299",
"Ian Clark":	"90ba0d1de241290df2e124a5e02d68ef",
"Solomon Hill":	"41c0674725d4cddab004649e9db5a3ce",
"Cheick Diallo":	"1f568a2342e4c375873d49a15e2d4448",
"Darius Miller":	"11beb0ae23e6425510297a31fa21881e"}

pid_dict = {v: k for k, v in pid_dict.items()}

box_score_ratings['ORTG'] = 100 * box_score_ratings['opts'] / box_score_ratings['offensive_nposs']
box_score_ratings['DRTG'] = 100 * box_score_ratings['dpts'] / box_score_ratings['defensive_nposs']
box_score_ratings['Net_RTG'] =box_score_ratings['ORTG'] - box_score_ratings['DRTG']
box_score_ratings['Person_id'] = box_score_ratings['Person_id'].apply(lambda z: pid_dict[z] if z in pid_dict.keys() else z)

box_score_ratings = box_score_ratings[['Game_id','Team_id','Person_id','pm','ORTG','DRTG']]



box_score_ratings['Person_id'] = box_score_ratings['Person_id'].apply(lambda z: pid_dict[z] if z in pid_dict.keys() else z)
pbp_singlegame['Person1'] = pbp_singlegame['Person1'].apply(lambda z: pid_dict[z] if z in pid_dict.keys() else z)
pbp_singlegame['Person2'] = pbp_singlegame['Person2'].apply(lambda z: pid_dict[z] if z in pid_dict.keys() else z)