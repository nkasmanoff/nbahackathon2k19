#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


Created on Mon Jun 10 20:33:48 2019

@author: noahkasmanoff



Contained in each training and holdout data entry is the caption of the instagram post, which contains
even more information to track, such as the users tagged in the post, and the hashtag is used. 


Logically, the motivation is to expect a @kingjames post to be more popular than a @redclawhoops post, and 
additionally we expect an #nbafinals hashtag to correspond to a more popular post than an #nbapreseason hashtag. 


By first scraping the hashtags and profiles attached, we can then derive further information such as 
average engagment rate of a post containing this profile or hashtag (tag), number of posts to contain it, 
and by interacting with instagram.com, the number of followers of a given account, or number of users to post a picture 
with a given hashtag. 

All of this information combined, we can begin partitioning the tags into separate clusters via the k-means 
clustering algorithm, and attach the frequency of a cluster designation of a given profile/hashtag, therefore encoding
in the dataset whether or not a popular profile is in the photo, and if it has to do with a meaningful event.


Obviously this is an imperfect approach, but it's somewhere to start!



"""
#%% preliminary data load

import os
import pandas as pd

instas = pd.read_csv('Business Analytics/training_set.csv',encoding = 'unicode_escape')
instas.fillna('',inplace=True)

#%%


def make_num(z):
    """
    
    Helper function for  the scraping tool. The result of a follower pull is 
    
    "35m followers", which this function will convert into 35 
    
    Parameters
    ----------
    
    z : str
        The follower count, given as "46m followers"
        
    Returns
    -------
    
    num : float
        The converted number, or 4.6e6. 
        
        Note this may occasionally return NaN, which means the account tagged was not actually found. 
    
    """
    
    import re
    from numpy import nan
    if type(z) == type(nan):
        return #not a number, this account didn't load.  
    z = z.split()[0] #not the followers part
    z = z.replace(',','')
    num = re.split(r'[a-z]*',z)[0]
    order = "".join(re.findall(r'[a-z]*',z))
    if order == 'm':
        num = float(num) * 1e6
    if order == 'k':
        num = float(num) * 1e3
    else:
        num = float(num)
   
    return num

def get_followers(z,driver):
    """
    Obtains follower count for profile in profile df. 
    
    Parameters
    ----------
    
    z : str
        The account name, done via an apply statement. 
        
    driver : WebDriver
        Selenium webdriver object, used to naviagate to the URL of each account, and then grab the corresponding
        followers. 
        
    Returns 
    -------
    
    followers : float
        The number of followers of that particular user. 

    """
    
    from time import sleep
    from random import randint
    z = z.replace('@','')
    driver.get("https://www.instagram.com/"+ z + "/?hl=en")
    sleep(randint(1,3))
    hrefs_in_view = driver.find_elements_by_tag_name('a')
    
    #this gives the link that has the attached follower number. 
    for elem in hrefs_in_view:
        if elem.get_attribute('href') ==  "https://www.instagram.com/accounts/login/?next=%2F"+z+"%2Ffollowers%2F&source=followed_by_list": #'https://www.instagram.com/'+z+'/followers/':
            
            followers = make_num(elem.text)
            
            return followers
              
def load_tagged_profiles(instas):
    """
    
    Creates a dataset summarizing the instagram accounts tagged in the post. 
    The columns used are a temporary list, and this line will be finalized once it is. 
    
    
    Parameters
    ----------
    
    instas : df
        Dataframe of the instagram posts, their associated information + output of engagements
        
        
    Returns
    -------
    
    
    profile_df : df
    
        Dataframe of the profiles tagged in any or multiple posts. 
        
    """
    
    #use regular expression to obtain any time a name is used, find all
    import re
    from pandas import DataFrame
    posts = " ".join(instas['Description'].unique()).lower() #combine into a corpus, isolating each tag. 
    tagged_profiles = list( dict.fromkeys(re.findall('@[a-z_0-9]*\.?[a-z_0-9]*?',posts)) ) 
    tagged_profiles = [s.replace('.','') if s[-1] == '.' else s for s in tagged_profiles]
    d = []
    instas['Description'] = instas['Description'].str.lower()
    for account in tagged_profiles:
        if account[-1] == '.':
            account = account[:-1] #remove the period accidentally taken at the end. 
        posts_w_account = instas.loc[instas['Description'].str.contains(account)]
        n_posts = posts_w_account.Engagements.count()
        d.append({'profile': account,
                 'n_posts' : n_posts})
   
    profile_df = DataFrame(d)
    profile_df.drop_duplicates(inplace=True)

    #but we're not done yet, can also encode how popular these accounts are, doing it based on follower count. 
    from selenium import webdriver
    driver = webdriver.Chrome('/Users/noahkasmanoff/Desktop/chromedriver') #open up chrome/spotify
    profile_df['followers']  = profile_df['profile'].apply(lambda z: get_followers(z,driver))
    driver.close()
    return profile_df


if 'tagged_profiles.csv' in os.listdir('Business Analytics'):
    print("Already created profile_df, loading now.")
    
    profile_df = pd.read_csv('Business Analytics/tagged_profiles.csv')
else:
    profile_df = load_tagged_profiles(instas)

    profile_df.to_csv('Business Analytics/tagged_profiles.csv',index=False)



#%% Now the hashtag scraper. 


def get_postscount(z,driver):
    """
    
    Obtains total number of posts to use a given hashtag, found in hashtag df. 
    
    Parameters
    ----------
    
    z : str
        The hashtag name, done via an apply statement. 
        
    driver : WebDriver
        Selenium webdriver object, used to naviagate to the URL of each account, and then grab the corresponding
        followers. 
        
    Returns 
    -------
    
    nposts : float
        The number of posts of that particular hashtag. 

    """
    
    from time import sleep
    from random import randint
    z = z.replace('#','')
    url = "https://www.instagram.com/explore/tags/" + z +"/?hl=en"
    driver.get(url)
    sleep(randint(1,3))
    try:
        nposts = driver.find_elements_by_class_name('g47SY')[0].text #total number of posts to use this hastag. 
    except:
        nposts = 1 #this was a type or something
        print(z , 'is a typo')
    return nposts


def load_hashtags(instas):
    """
    
    Creates a dataset summarizing the instagram hashtags used in the post. 
    The columns used are a temporary list, and this line will be finalized once it is. 
    
    
    Parameters
    ----------
    
    instas : df
        Dataframe of the instagram posts, their associated information + output of engagements
        
        
    Returns
    -------
    
    
    hastags_df : df
    
        Dataframe of the hashtagss tagged in any or multiple posts. 
        
    """
    #use regular expression to obtain any time a name is used, find all
    import re
    from pandas import DataFrame
    instas['Description'] = instas['Description'].str.lower()

    posts = " ".join(instas['Description'].unique())
    hashtags = list( dict.fromkeys(re.findall('#[a-z_0-9]*',posts)) ) 
    #iterate through these accounts, obtain info regarding how they are engaged. 
    d = []
    for hashtag in hashtags:
        posts_w_hashtag = instas.loc[instas['Description'].str.contains(hashtag)]
        n_posts = posts_w_hashtag.Engagements.count()
        d.append({'hashtags': hashtag,
                 'n_posts' : n_posts})

    hashtags_df = DataFrame(d)
    #but we're not done, can also establish how popular these accounts are, doing it based on follower count. 
    from selenium import webdriver
    driver = webdriver.Chrome('/Users/noahkasmanoff/Desktop/chromedriver')

    hashtags_df['# of posts']  = hashtags_df['hashtags'].apply(lambda z: get_postscount(z,driver))
    driver.close()
    hashtag_df['# of posts'] = hashtag_df['# of posts'].str.replace(',','').astype(float).fillna(1)

    
    return hashtags_df


if 'used_hashtags.csv' in os.listdir('Business Analytics'):
    print("Already created hashtag_df, loading now.")
    hashtag_df = pd.read_csv('Business Analytics/used_hashtags.csv')
else:
    hashtag_df = load_hashtags(instas)

    hashtag_df.to_csv('Business Analytics/used_hashtags.csv',index=False)
    
    
print("Scraping complete. Now have dataframes containing information regarding the tagged accounts and hashtags used in each instagram post of the training set. Make sure to generalize for holdout too!")


