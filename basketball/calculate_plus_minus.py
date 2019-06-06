# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 500)


# In[2]:

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



# In[3]:

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
    suboutID = substitution['Person1']
    subinID = substitution['Person2']
    score1 = substitution['score_x']
    score2 = substitution['score_y']

    if teamid == teams[0]:
        diff = score1 - score2
    else:
        diff = score2 - score1

    suboutindex = (playersin['Person_id'] == suboutID)
    playersin.loc[suboutindex,'pm'] = playersin.loc[suboutindex,'pm']     + diff - playersin.loc[suboutindex,'diffin']

    if ~bench['Person_id'].str.contains(subinID).any(): # if the player isn't in the "bench" df,
                                                        # ie. hasn't already appeared in the game
            playersin = playersin.append(
            {'Team_id': teamid, 'Person_id':subinID, 'diffin':diff, 'pm':0},
            ignore_index = True)
    else: # if he's in the "bench" df already
        playersin = playersin.append(bench.loc[bench['Person_id'] == subinID])
        bench = bench.loc[~(bench['Person_id'] == subinID)]

    bench = bench.append(playersin.loc[playersin['Person_id'] == suboutID])
    playersin = playersin.loc[~(playersin['Person_id'] == suboutID)]

    # set the score difference for new player
    playersin.loc[playersin['Person_id'] == subinID, 'diffin'] = diff

    return playersin, bench


# In[4]:

def startperiod(playersin, bench, startrow):
    """ Function to switch out players at the start of the period
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

    Returns :
    playersin, bench
    -------
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
                 'pm':0},
                ignore_index = True)

    # set the score difference for all players at the start of the period
    playersin.loc[playersin['Team_id'] == teams[0],'diffin'] = diff
    playersin.loc[playersin['Team_id'] == teams[1],'diffin'] = -diff


    return playersin, bench


# In[5]:

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
    playersin.loc[playersin['Team_id'] == teams[0], 'pm']         = playersin.loc[playersin['Team_id'] == teams[0],'pm']         + diff - playersin.loc[playersin['Team_id'] == teams[0],'diffin']
    playersin.loc[playersin['Team_id'] == teams[1], 'pm']         = playersin.loc[playersin['Team_id'] == teams[1],'pm']         - diff - playersin.loc[playersin['Team_id'] == teams[1],'diffin']

    return playersin, bench


# In[6]:

# load in the data
ecname = 'NBA Hackathon - Event Codes.txt'
lineupname = 'NBA Hackathon - Game Lineup Data Sample (50 Games).txt'
pbpname = 'NBA Hackathon - Play by Play Data Sample (50 Games).txt'

codes = pd.read_csv(ecname, sep ='\t')
lineup = pd.read_csv(lineupname, sep = '\t')
pbp = pd.read_csv(pbpname, sep = '\t')


ec =  pd.read_table('NBA Hackathon - Event Codes.txt')
lineup = pd.read_table('NBA Hackathon - Game Lineup Data Sample (50 Games).txt')
pbp = pd.read_table('NBA Hackathon - Play by Play Data Sample (50 Games).txt')

# In[7]:

pms = pd.DataFrame([])

#pt 2. isolate one game instance
# indentify sample games, loop through all
sample_games = pbp['Game_id'].unique()
######Loop and test sub function here ######
# for game in sample_games:
for game_num in range(len(sample_games)):
    game = sample_games[game_num] # for now, not iterative.
    print("game id: ", game)
    print("game num: ",game_num)
# identify teams
    teams = lineup.loc[lineup['Game_id'] == game]['Team_id'].unique()


# sort out play by play for singe game
    pbp1 = pbp.loc[pbp['Game_id'] == sample_games[game_num]]
#Properly sorted format.
   # pbp1 = pbp1.sort_values(['Period','PC_Time','WC_Time','Event_Num'],
   #     ascending=[True,False,True,True])

#New theory for sorting...
    pbp1 = pbp1.sort_values(['Period','PC_Time','Event_Msg_Type','WC_Time','Event_Num'],
        ascending=[True,False,True,True,True])
#Here would be a good place to add FTE
#     pbp1 = pbp1.reset_index(drop=True)

#translate to understand what each play is.
    pbp1 = pd.merge(pbp1, codes,
        on = ['Event_Msg_Type', 'Action_Type'], how = 'left')

# subset out extraneous plays, only need scoring plays, free throws, subsitions
# start and end of period
    pbpx = pbp1.loc[(pbp1['Event_Msg_Type'] == 1) |
        (pbp1['Event_Msg_Type'] == 3) | (pbp1['Event_Msg_Type'] == 8) |
        (pbp1['Event_Msg_Type'] == 12) | (pbp1['Event_Msg_Type'] == 13)]
    del pbpx['Action_Type_Description']
    lineup1 = lineup.loc[(lineup['Game_id'] == game)]
    subsmask = pbpx['Event_Msg_Type'] == 8
    subs = pbpx[subsmask]
    playersin = pd.DataFrame(lineup1.loc[(lineup1['Period'] == 1),['Team_id','Person_id']])
    subs_correct = substitution_correction(subs,lineup1)
  #  print( subs_correct.isna().sum())
    pbpx[subsmask] =  subs_correct.values


    playersin['diffin'] = playersin['pm'] = 0
    bench = pd.DataFrame(columns = ['Team_id', 'Person_id', 'diffin', 'pm'])
    #### Cleaning now complete, now calculating pm for every game.

    pbpx.loc[(pbpx['Event_Msg_Type'] == 3)&(pbpx['Option1'] != 1), 'Option1'] = 0
    pbpx['score'] = pbpx.groupby('Team_id', axis = 0)['Option1'].cumsum()
    team1score = pbpx.loc[pbpx.iloc[:,10] == teams[0]]
    team2score = pbpx.loc[pbpx.iloc[:,10] == teams[1]]
    del pbpx['score']

    pbpx = pd.merge(pbpx, team1score.loc[:,['Event_Num','score']], on = 'Event_Num', how = 'left')
    pbpx = pd.merge(pbpx, team2score.loc[:,['Event_Num','score']], on = 'Event_Num', how = 'left')

    # fill forward for NaNs
    pbpx.loc[:,['score_x', 'score_y']] = pbpx.loc[:,['score_x', 'score_y']].fillna(method = 'ffill')
    pbpx.loc[:,['score_x', 'score_y']] = pbpx.loc[:,['score_x', 'score_y']].fillna(0) # for the start of the game
    del team1score, team2score

    # Loop through play by play
    for index, row in pbpx.iterrows():
        if (row['Event_Msg_Type'] == 8):
            playersin, bench = sub(playersin, bench, row)  #calculate +/- of subout.
        elif (row['Event_Msg_Type'] == 13):
            playersin, bench = endperiod(playersin, bench, row)  #calculate +/- at end of period,
        elif (row['Event_Msg_Type'] == 12):
            playersin, bench = startperiod(playersin, bench, row) #update lineups

    pm = pd.concat([bench,playersin])
    pm = pm.sort_values(['Team_id','pm'])
    pm = pm.reset_index(drop=True)

    pm['game_id'] = game
    pms = pms.append(pm)
    print(pm['pm'].sum())


# In[ ]:

pms = pms[['game_id','Person_id','pm']]
pms = pms.rename(index = str, columns = {'game_id': "Game_ID",'Person_id': 'Player_ID','pm': 'Player_Plus/Minus'})


# In[14]:

pms


# In[15]:

pms.to_csv('Maryland_Physics_Analytics_Team_Q1_BBALL.csv')
