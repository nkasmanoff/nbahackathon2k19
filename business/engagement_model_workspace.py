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

holdout = pd.read_csv('Business Analytics/holdout_set.csv',encoding = 'unicode_escape')

X_holdout = process_data('Business Analytics/holdout_set.csv',k_prof = 300,k_hash = 300,training=False)
holdout_predictions = model.predict(X_holdout)
holdout_predictions = np.array([int(round(y)) for y in holdout_predictions])
holdout['Engagements'] = holdout_predictions

holdout.to_csv('holdout_predictionsTEAMNAME.csv',index=False)