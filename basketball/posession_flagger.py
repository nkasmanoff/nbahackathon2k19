#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 11:30:01 2019

@author: noahkasmanoff


The goal of this script is to locate the end of possession of identifiers throughout a game, 
and use this in order to create a running total of possessions a player is in a game for. 



. A possession is ended by (1) made field goal attempts, (2) made final free throw attempt, (3) missed final free throw attempt that results in a defensive rebound, (4) missed field goal attempt that results in a defensive rebound, (5) turnover, or (6) end of time period.



Note. Putback rebounds (offensive ones) are currently not sorted. 
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")



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


#load in data. 
pbp = pd.read_csv('Basketball Analytics/Play_by_Play.txt',delimiter='\t')
lineup = pd.read_csv('Basketball Analytics/Game_Lineup.txt',delimiter='\t')
codes = pd.read_csv('Basketball Analytics/Event_Codes.txt',delimiter = '\t')



sample_games = pbp['Game_id'].unique()
######Loop and test sub function here ######
i = 0

for game_num in range(len(sample_games))[0:1]:
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
    pbp_relevant = pbp_relevant.sort_values(['Period','PC_Time','Option1','WC_Time','Event_Num'],
        ascending=[True,False,True,True,True])
  #  pbp_singlegame = pbp_singlegame.sort_values(['Period','PC_Time','Option1','WC_Time','Event_Num'],
   #     ascending=[True,False,True,True,True])
  
    pbp_singlegame= pbp_singlegame.sort_values(['Event_Num'],
        ascending=[True])
        
    
#%%

#pbp_relevant['score'] = pbp_relevant.groupby('Team_id', axis = 0,sort=False)['Option1'].cumsum()
pbp_singlegame['Poss Change 1'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 1 else False)
pbp_singlegame['Poss Change 2'] =     
pbp_singlegame['Poss Change 4'] = ((pbp_singlegame['Team_id'] != pbp_singlegame['Team_id'].shift(-1)) & (pbp_singlegame['Event_Msg_Type_Description'].str.contains('Rebound')))

pbp_singlegame['Poss Change 5'] = pbp_singlegame['Event_Msg_Type'].apply(lambda z: True if z == 5 else False)



def freethrowexceptions(z):
        if z['Event_Msg_Type'] == 3:
            if z['Action_Type_Description'].split(' ')[-1] == z['Action_Type_Description'].split(' ')[-3]: #if final free throw
                if z['Option1'] == 1  #made final free throw. 
                    return True
                
                # if option 1 not equal to 1, it was missed. 
                #so the posssession continues, in which case the rules in place already capture this. 
                    #otherwise, it's in, and return. 
                    
                    #now
#pbp_singlegame['New Possession?'] = ((pbp_singlegame['Team_id'] != pbp_singlegame['Team_id'].shift(-1)) & (pbp_singlegame['Event_Msg_Type_Description'] == 'Rebound'))

#pbp_singlegame['Possession ID'] = (pbp_singlegame['Team_id'] != pbp_singlegame['Team_id'].shift(1)).cumsum() 

#pbp_singlegame['New Possession?'] = pbp_singlegame['New Possession?'].apply(lambda z: 1 if z else 0)
#if the team changes. 

#pbp_singlegame.drop_duplicates(subset = ['Possession #'],keep='last',inplace=True)
#pbp_singlegame['teampossessionss'] = pbp_singlegame.groupby('Team_id', axis = 0,sort=False)['New Possession?'].cumsum()


pbp_viewer = pbp_singlegame.drop(columns =['Game_id','Person1','Person2','Person3',
                                           'Person1_type','Person2_type','Person3_type'])

#%% 