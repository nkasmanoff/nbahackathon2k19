#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 10:54:50 2019

@author: noahkasmanoff


Contained in this script is the collection of total # of offensive points scored while a player is on the court. 

The next step is to generalize this for defensive points allowed while on the court, and make an additional counter for 
possessions to have occured. 

"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
#%%

# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 500)



def substitution_correction(subs,lineup):
    """Go through a game dataframe. Correct and confirm that the
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
    nanfirst.dropna(axis=1,inplace=True) #remove columns to be added back soon
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



def sub(playersin, bench, substitution):
    """Function to calculate plus/minus for individuals when they subout
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
    if teamid == teams[0]:
        diff = score1 - score2
        opts = score1
        dpts = score2
    else:
        diff = score2 - score1
        opts = score2
        dpts = score1
        
    suboutindex = (playersin['Person_id'] == suboutID)

    # calculates plus minus of the player at the subout index. 
    playersin.loc[suboutindex,'pm'] = playersin.loc[suboutindex,'pm']     + diff - playersin.loc[suboutindex,'diffin']
    #maybe an if statement for this being the first time being subbed out? 
    playersin.loc[suboutindex,'opts'] = playersin.loc[suboutindex,'opts']     + opts -  playersin.loc[suboutindex,'plusin']
    playersin.loc[suboutindex,'dpts'] = playersin.loc[suboutindex,'dpts']     + dpts -  playersin.loc[suboutindex,'minusin']

   # return playersin, suboutindex,score
    if ~bench['Person_id'].str.contains(subinID).any(): # if the player isn't in the "bench" df, which is means the player was subbed out. 
                                                        
            playersin = playersin.append(
            {'Team_id': teamid, 'Person_id':subinID, 'diffin':diff, 'pm':0,'plusin':0,'opts':0,'minusin':0,'dpts':0},
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
                 'dpts':0},
                ignore_index = True)

    # set the score difference for all players at the start of the period
    playersin.loc[playersin['Team_id'] == teams[0],'diffin'] = diff
    playersin.loc[playersin['Team_id'] == teams[1],'diffin'] = -diff
    
    playersin.loc[playersin['Team_id'] == teams[0],'plusin'] = score1
    playersin.loc[playersin['Team_id'] == teams[1],'plusin'] = score2
    
    playersin.loc[playersin['Team_id'] == teams[0],'minusin'] = score2
    playersin.loc[playersin['Team_id'] == teams[1],'minusin'] = score1

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
    diff = score1 - score2
    
    # calculate plus minus for everyone at the end of the period
    playersin.loc[playersin['Team_id'] == teams[0], 'pm']  = playersin.loc[playersin['Team_id'] == teams[0],'pm']  + diff - playersin.loc[playersin['Team_id'] == teams[0],'diffin']
    playersin.loc[playersin['Team_id'] == teams[1], 'pm']  = playersin.loc[playersin['Team_id'] == teams[1],'pm']  - diff - playersin.loc[playersin['Team_id'] == teams[1],'diffin']
       # 
    playersin.loc[playersin['Team_id'] == teams[0], 'opts']  = playersin.loc[playersin['Team_id'] == teams[0],'opts']  +score1 - playersin.loc[playersin['Team_id'] == teams[0],'plusin']
    playersin.loc[playersin['Team_id'] == teams[0], 'dpts']  = playersin.loc[playersin['Team_id'] == teams[0],'dpts']  +score2 - playersin.loc[playersin['Team_id'] == teams[0],'minusin']

    playersin.loc[playersin['Team_id'] == teams[1], 'opts']  = playersin.loc[playersin['Team_id'] == teams[1],'opts']  +score2- playersin.loc[playersin['Team_id'] == teams[1],'plusin']
    playersin.loc[playersin['Team_id'] == teams[1], 'dpts']  = playersin.loc[playersin['Team_id'] == teams[1],'dpts']  +score1 - playersin.loc[playersin['Team_id'] == teams[1],'minusin']

   # playersin.loc[playersin['Team_id'] == teams[0],'opts'] = playersin.loc[playersin['Team_id'] == teams[0],'opts'] # + score1 - playersin.loc[playersin['Team_id'] == teams[0],'opts']
   # playersin.loc[playersin['Team_id'] == teams[1],'opts'] = playersin.loc[playersin['Team_id'] == teams[1],'opts'] + score2  - playersin.loc[playersin['Team_id'] == teams[1],'opts']
    #return playersin,
    return playersin, bench





#load in data. 
pbp = pd.read_csv('Basketball Analytics/Play_by_Play.txt',delimiter='\t')
lineup = pd.read_csv('Basketball Analytics/Game_Lineup.txt',delimiter='\t')
codes = pd.read_csv('Basketball Analytics/Event_Codes.txt',delimiter = '\t')

sample_games = pbp['Game_id'].unique()
######Loop and test sub function here ######
i = 0

for game_num in range(len(sample_games))[11:12]:
    pbp = pd.read_csv('Basketball Analytics/Play_by_Play.txt',delimiter='\t')
    lineup = pd.read_csv('Basketball Analytics/Game_Lineup.txt',delimiter='\t')
    codes = pd.read_csv('Basketball Analytics/Event_Codes.txt',delimiter = '\t')

    game = sample_games[game_num] # for now, not iterative.
    print("game id: ", game)
    print("game num: ",game_num)
    teams = lineup.loc[lineup['Game_id'] == game]['Team_id'].unique() #locate the two teams in the game. 
    
    
    #sort according to this, it may end up changing . 
    pbp_singlegame = pbp.loc[pbp['Game_id'] == sample_games[game_num]] #.sort_values(['Period','PC_Time','WC_Time','Event_Num'],
       # ascending=[True,False,True,True])
    
    #translate using codes
    pbp_singlegame = pbp_singlegame.merge( codes,
        on = ['Event_Msg_Type', 'Action_Type'], how = 'left')
    

    #retain every event that is a made shot
    pbp_relevant = pbp_singlegame.loc[(pbp_singlegame['Event_Msg_Type'] == 1) |
        (pbp_singlegame['Event_Msg_Type'] == 3) | (pbp_singlegame['Event_Msg_Type'] == 8) |
        (pbp_singlegame['Event_Msg_Type'] == 12) | (pbp_singlegame['Event_Msg_Type'] == 13)]
    

    #delete this extraneous col
   # del pbp_relevant['Action_Type_Description']
    

    #obtain starting lineups
    starting_lineup = lineup.loc[(lineup['Game_id'] == game)] #starting lineup of the game
    
    subsmask = pbp_relevant['Event_Msg_Type'] == 8
    subs = pbp_relevant[subsmask] #dataframe of all substitutions. 
    
    
    playersin = pd.DataFrame(starting_lineup.loc[(starting_lineup['Period'] == 1),['Team_id','Person_id']])
    subs_correct = substitution_correction(subs,starting_lineup)
    pbp_relevant[subsmask] =  subs_correct #fixes substitutions, and cofnirms taem names are correct. 
    subs = pbp_relevant[subsmask] 
    pbp_relevant = pbp_relevant.sort_values(['Period','PC_Time','WC_Time','Event_Num'],
        ascending=[True,False,True,True])
    

    #Initialize point differential both game and players for the dataset. 
    playersin['diffin'] = playersin['pm'] = playersin['plusin'] = playersin['opts'] = 0
    playersin['minusin'] = playersin['dpts'] =0
    bench = pd.DataFrame(columns = ['Team_id', 'Person_id', 'diffin', 'pm','plusin','opts','minusin','dpts'])

    pbp_relevant.loc[(pbp_relevant['Event_Msg_Type'] == 3)&(pbp_relevant['Option1'] != 1), 'Option1'] = 0
    pbp_relevant['score'] = pbp_relevant.groupby('Team_id', axis = 0,sort=False)['Option1'].cumsum()
    team1score = pbp_relevant.loc[pbp_relevant.iloc[:,10] == teams[0]]
    team2score = pbp_relevant.loc[pbp_relevant.iloc[:,10] == teams[1]]
    del pbp_relevant['score'] #this is because it copies, don't do this. 
    
    pbp_relevant = pd.merge(pbp_relevant, team1score.loc[:,['Event_Num','score']], on = 'Event_Num', how = 'left')
    pbp_relevant = pd.merge(pbp_relevant, team2score.loc[:,['Event_Num','score']], on = 'Event_Num', how = 'left')

    # fill forward for NaNs
    pbp_relevant.loc[:,['score_x', 'score_y']] = pbp_relevant.loc[:,['score_x', 'score_y']].fillna(method = 'ffill')
    pbp_relevant.loc[:,['score_x', 'score_y']] = pbp_relevant.loc[:,['score_x', 'score_y']].fillna(0) # for the start of the game
    del team1score, team2score
    
    for index, row in pbp_relevant.iterrows():
       # print()
       # print(index,row)
        if (row['Event_Msg_Type'] == 8):
            playersin, bench = sub(playersin, bench, row)  #calculate +/- of subout.
        #    playersin, suboutindex,score = sub(playersin, bench, row)  #calculate +/- of subout.
        elif (row['Event_Msg_Type'] == 13):
           # i+=1
    
            playersin, bench = endperiod(playersin, bench, row)  #calculate +/- at end of period,


        elif (row['Event_Msg_Type'] == 12):
            playersin, bench = startperiod(playersin, bench, row) #update lineups

#%%

subs = pbp_relevant.loc[pbp_relevant['Event_Msg_Type'] == 8]
#now lets see what the operations
#%%

#%%
pbp_relevant.groupby('Team_id')


# in play by play, expand based on players in? 


#%%
def possession_flag(z):
    """
    
    Creates a flag as to whether or not this is the end of a possession. 
    
    Continue to clean this according  to their rules. 
    
    """
    
    if z['Event_Msg_Type'] == 3:
        if z['Action_Type_Description'].split(' ')[-1] == z['Action_Type_Description'].split(' ')[-3]:
            return 1
    if z['Event_Msg_Type'] == 1:
        return 1

    if z['Event_Msg_Type'] == 5:
        return 1
    if z['Event_Msg_Type'] == 4:
        return 1
    return 0

pbp_singlegame['End of Possession?'] = pbp_singlegame.apply(lambda z: possession_flag(z),axis=1)
    

#%%

#So what ends a possession? 
#event message type 1 made shot

# 3  - made free throw, if x of x. 

# any 5  turnover

# 8 - substitution, but for that player only, others are still part of that possesion. 
    