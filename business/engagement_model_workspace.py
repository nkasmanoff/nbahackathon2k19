"""
Machine learning model used to train and predict the # of engagements a given instagram post will receive, based on an array of over 50 features, 
exploring information ranging from the # of followers gained since the last post, popularity of the profiles and hashtags used, day of the week, hour, year, month, 
and many more. 




"""


from data_processing import process_data
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

def mean_absolute_percentage_error(y_true, y_pred):
    import numpy as np
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100



ks = [300,300,300] #every other
#%%

MAPES = []
for k_prof in ks:
    for k_hash in ks:
        
        X, y = process_data('Business Analytics/training_set.csv',k_prof = k_prof,k_hash = k_hash,training=True)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        model = XGBRegressor(colsample_bytree =0.5, gamma = 0.05, max_depth = 4, min_child_weight = 4, n_estimators = 1000, subsample = 0.6) 

        model.fit(X_train, y_train)
        print("MAPE Train Score ")
        print(mean_absolute_percentage_error(y_train, model.predict(X_train)))
    
    
        print("MAPE Test Score ")
        print(mean_absolute_percentage_error(y_test, model.predict(X_test)))
        MAPES.append(mean_absolute_percentage_error(y_test, model.predict(X_test)))
    
      #  print("Best parameters ")
      #  print(grid.best_params_)
        
#%%
print(np.mean(MAPES), '+/-', 2*np.std(MAPES))
#%%


#%%
X, y = process_data('Business Analytics/training_set.csv',k_prof = 300,k_hash = 300,training=True)

from xgboost import XGBRegressor


# Initialize XGB and GridSearch
model = XGBRegressor(colsample_bytree =0.5, gamma = 0.05, max_depth = 4, min_child_weight = 4, n_estimators = 1000, subsample = 0.6) 
model.fit(X, y)



#%%

y_true = y.values
y_pred = model.predict(X)
X['APE'] = 100*abs(y_true - y_pred)/ y_true
X['Good Job?'] = X['APE'].apply(lambda z: 1 if z < 3 else 0)
X_holdout = process_data('Business Analytics/holdout_set.csv',k_prof = 300,k_hash = 300,training=False)
X_holdout['Holdout?'] = 2*np.ones(len(X_holdout))

#%%
from sklearn.manifold import TSNE

X_tsne = pd.concat([X.drop(columns=['APE','Good Job?']),X_holdout.drop('Holdout?',axis=1)],axis=0)

def normalize(df):
    result = df.copy()
    for feature_name in df.columns:
        max_value = df[feature_name].max()
        min_value = df[feature_name].min()
        result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
    return result

#%%





X_tsne = normalize(X_tsne)
X_tsne.fillna(0,inplace=True)  #in some cases no members of this group exist. 

#%%
X_embedded = TSNE(n_components=2).fit_transform(X_tsne)
labels = pd.concat([X['Good Job?'],X_holdout['Holdout?']])


badfits = X_embedded[labels.values== 0] # bad fit on training data

goodfits = X_embedded[labels== 1] # good fit on training data


holdouts = X_embedded[labels== 2] # was a part of the holdout set

X_embedded_df = pd.DataFrame(X_embedded)
X_embedded_df['labels'] = labels.values

#%%

import matplotlib.pyplot as plt
plt.figure(figsize=(20,20))
plt.plot(X_embedded_df.loc[X_embedded_df.labels == 0][0],
         X_embedded_df.loc[X_embedded_df.labels == 0][1],'bo',label = 'bad fit',alpha=.2,markersize=16)
plt.plot(X_embedded_df.loc[X_embedded_df.labels == 1][0],
         X_embedded_df.loc[X_embedded_df.labels == 1][1],'ro',label = 'good fit',alpha=.2,markersize=16)


plt.plot(X_embedded_df.loc[X_embedded_df.labels == 2][0],
         X_embedded_df.loc[X_embedded_df.labels == 2][1],'ko',label = 'holdout data',alpha=1,markersize=5)
plt.legend()

plt.show()
#%%
holdout = pd.read_csv('Business Analytics/holdout_set.csv',encoding = 'unicode_escape')

X_holdout = process_data('Business Analytics/holdout_set.csv',k_prof = 300,k_hash = 300,training=False)
holdout_predictions = model.predict(X_holdout)
holdout_predictions = np.array([int(round(y)) for y in holdout_predictions])
holdout['Engagements'] = holdout_predictions

#holdout.to_csv('holdout_predictionsTEAMNAME.csv',index=False)