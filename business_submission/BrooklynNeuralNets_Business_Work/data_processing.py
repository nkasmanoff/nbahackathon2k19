"""

This script contains the functions used to clean and prepare the instagram datasets for modelling. 




"""

import numpy as np
import pandas as pd

def apply_profile_clusters_to_training(z,profiles):
    """Apply the clusters to the dataset, now in a form for prediction aligned with the other data. 
   
   """
    
    import re
    from numpy import zeros
    post_clusters = zeros(profiles.shape[1] - 1)
    tags_in_z =  list( dict.fromkeys(re.findall('@[a-z_0-9]*',z)) ) 
    
    if len(tags_in_z) == 0:
        return post_clusters
    for tag_in_z in tags_in_z:
        try:
            post_clusters = post_clusters + profiles[profiles['profile'] == tag_in_z].values[0][1:] 
        except: 
            pass
    return post_clusters


def cluster_profiles(instas,k):
    """
    """
    
    from sklearn.cluster import KMeans
    from sklearn import preprocessing
    from instagram_scraper import profile_df
    
    

    profiledf = profile_df.copy(deep=True)
    
    profiledf.dropna(inplace=True)
    profiledf['followers'] = profiledf['followers + post_count'].apply(lambda z: float(z.split(',')[0].replace('(','')))
    profiledf['post_count'] = profiledf['followers + post_count'].apply(lambda z: float(z.split(',')[1].replace(')','')))

    profiledf.drop('followers + post_count',axis=1,inplace=True)
    profiledf.drop('n_posts',axis=1,inplace=True)
    profiledf['followers'] = np.log10(profiledf['followers']+1)
    profiledf['post_count'] = np.log10(profiledf['post_count']+1)

    x = profiledf.drop('profile',axis=1).values #returns a numpy array #removes missing followers (broken accounts)

    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    df = pd.DataFrame(x_scaled)
    kmeanModel = KMeans(n_clusters=k).fit(df)

    profiledf['Cluster'] = kmeanModel.labels_


    profiles = profiledf[['profile','Cluster']].copy()
    profiles = pd.get_dummies(profiles,columns=['Cluster'])

    instas['Clusters'] = instas['Description'].str.lower().apply(lambda z: apply_profile_clusters_to_training(z,profiles))

    clusters = pd.DataFrame(instas.Clusters.tolist(), columns=['profClus'+str(x) for x in np.arange(profiles.shape[1] - 1)])
    instas = instas.merge(clusters,left_index=True,right_index=True).drop('Clusters',axis=1)

    return instas

def apply_hashtag_clusters_to_training(z,hashtags):
    """Apply the clusters to the dataset, now in a form for prediction aligned with the other data. 
   
   """
    
    import re
    from numpy import zeros
    post_clusters = zeros(hashtags.shape[1] - 1)
    tags_in_z =  list( dict.fromkeys(re.findall('#[a-z_0-9]*',z)) ) 
    
    if len(tags_in_z) == 0:
        return post_clusters
    for tag_in_z in tags_in_z:
        #try:
        post_clusters = post_clusters + hashtags[hashtags['hashtags'] == tag_in_z].values[0][-(hashtags.shape[1] - 1):] 
       # except: 
       #     pass
    return post_clusters


def cluster_hashtags(instas,k):
    """Use k means clustering to partition hashtags in the descriptions into groups. 
    
    """

    from instagram_scraper import hashtag_df

    

    
    hashtagdf = hashtag_df.copy(deep=True)
    hashtagdf.drop('n_posts',axis=1,inplace=True)
    hashtagdf['# of posts'] = np.log10(hashtagdf['# of posts']+1)

    from sklearn.cluster import KMeans
    from sklearn import preprocessing

    x = hashtagdf.drop('hashtags',axis=1).values #returns a numpy array #removes missing followers (broken accounts)

    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    df = pd.DataFrame(x_scaled)

    kmeanModel = KMeans(n_clusters=k).fit(df)
    hashtagdf['Cluster'] = kmeanModel.labels_

    hashtags = hashtagdf[['hashtags','Cluster']].copy()
    hashtags = pd.get_dummies(hashtags,columns=['Cluster'])


    instas['Clusters'] = instas['Description'].str.lower().apply(lambda z: apply_hashtag_clusters_to_training(z,hashtags))
    clusters = pd.DataFrame(instas.Clusters.tolist(), columns=['hashClus'+str(x) for x in np.arange(hashtags.shape[1] - 1)])
    instas = instas.merge(clusters,left_index=True,right_index=True).drop('Clusters',axis=1)
    return instas


#utilitiy functions before data processing. 
def find_blocks(z):
    dunk_words = ['swat','rejected','block','denies','denied']
    for dw in dunk_words:
        if dw in z.lower(): 
            return 1
    return 0


def find_dunks(z):
    dunk_words = ['slam','jam','dunk','putback','windmill','flush','oop','lob']
    for dw in dunk_words:
        if dw in z.lower(): 
            return 1
    return 0

def find_buzzer_beaters(z):
    buzzer_beater_words = ['buzz','beat','clock','winner']
    for bbw in buzzer_beater_words:
        if bbw in z.lower():
            return 1
    return 0


def normalize(df):
    result = df.copy()
    for feature_name in df.columns:
        max_value = df[feature_name].max()
        min_value = df[feature_name].min()
        result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
    return result



def process_data(file,training=False,k_prof = 11, k_hash = 8 ):
    """Loads in file, either the training or holdout set, and transforms it into the dataframe we want using the variable 
    changes based solely on that particular dataframe, as well as based on exogenous features such as profiles tagged, and hashtags used. 
    
    Parameters
    ----------
    
    file : csv 
        Csv file of the instagram posts. 
        
    training : bool
        Whether or not the inputfile is the training set. If true, this will also have attached a y output, in addition to X. 
        
    
    Returns
    --------
    
    X : dataframe
        ML ready dataframe of the associated features used to capture engagmeent rates. 
        
        Further documentation of each feature provided below. 
        
    y : optional return Dataframe
        For training purposes only, the output values of engagment to train ML model(s) on. 
        
    """
    
    import pandas as pd
    
    instas = pd.read_csv(file,encoding = 'unicode_escape')
    instas.fillna('',inplace=True)
    
    instas['Description_Len'] = instas['Description'].apply(len)
    instas['num@s'] = instas['Description'].apply(lambda z: z.count('@'))
    instas['num#s'] = instas['Description'].apply(lambda z: z.count('#'))
    instas['num?s'] = instas['Description'].apply(lambda z: z.count('?')) 
    instas['numwords'] = instas['Description'].apply(lambda z: z.count(' ')) 
    import re
    instas['numCAPs'] = instas['Description'].apply(lambda z: len(re.findall(r'[A-Z]',z)))

    instas['Buzzer Beater?'] = instas['Description'].apply(lambda z: find_buzzer_beaters(z)) #shitty proxy for buzzer beaters
    instas['Dunk?'] = instas['Description'].apply(lambda z:  find_dunks(z)) #shitty proxy for buzzer beaters
    instas['Block?'] = instas['Description'].apply(lambda z:  find_blocks(z)) #shitty proxy for buzzer beaters


    import datetime

    instas['Timezone'] = instas['Created'].str.split(' ',expand =True)[2]
    instas['Date'] = instas['Created'].str.split(' ',expand = True)[0]
    instas['Month'] = instas['Date'].str.split('-',expand = True)[1]

    instas['Time'] = instas['Created'].str.split(' ',expand = True)[1]
    instas['Hour'] = instas['Time'].str.split(':',expand=True)[0]

    instas['Date'] = pd.to_datetime(instas['Date']).astype(datetime.datetime)

    instas['Weekday'] = instas['Date'].apply(lambda z: str(z.weekday()))
    instas['Year'] = instas['Created'].apply(lambda z: z.split('-')[0])
    
    
    instas = cluster_profiles(instas,k=k_prof)#make k unique clusters of profiles, and apply that to dataset. 
    instas = cluster_hashtags(instas,k=k_hash)#make k unique clusters of profiles, and apply that to dataset. 

    instas['Followers Gained Since Last Post'] = -instas['Followers at Posting'].diff(1).shift(-1).fillna(0)
    if training:
        X = instas.drop(columns=['Engagements','Description','Created','Followers at Posting','Date','Time']).copy()
        y = instas['Engagements']
    else:   
        X = instas.drop(columns=['Engagements','Description','Created','Followers at Posting','Date','Time']).copy()
        
    X = pd.get_dummies(X)
    if training:
        return X,y
    #otherwise, 
    return X
    


if __name__ == '__main__':
    X,y = process_data('training_set.csv',training=True)

    import matplotlib.pyplot as plt
    from sklearn.datasets import make_classification
    from sklearn.ensemble import ExtraTreesRegressor

    # Build a classification task using 3 informative features

    # Build a forest and compute the feature importances
    forest = ExtraTreesRegressor(n_estimators=250,
                                  random_state=0)
     
    forest.fit(X, y)
    importances = forest.feature_importances_
    std = np.std([tree.feature_importances_ for tree in forest.estimators_],
                 axis=0)
    indices = np.argsort(importances)[::-1]

    # Print the feature ranking
    #print("Feature ranking:")
    col_names = []
    for f in range(X.shape[1]):
     #   print("%d. feature %d (%f)" % (f + 1, indices[f], importances[indices[f]]))
     #   print(X.columns[indices[f]])
        col_names.append(X.columns[indices[f]])

    # Plot the feature importances of the forest
    plt.figure(figsize=(25,10))
    plt.title("Feature importances")
    plt.bar(range(X.shape[1]), importances[indices],
           color="r", yerr=std[indices], align="center")
    plt.xticks(range(X.shape[1]), col_names,rotation=90)
    plt.xlim([-1, X.shape[1]])
    plt.show()
