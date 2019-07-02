"""
Machine learning model used to train and predict the # of engagements a given instagram post will receive, based on an array of over 50 features, 
exploring information ranging from the # of followers gained since the last post, popularity of the profiles and hashtags used, day of the week, hour, year, month, 
and many more. 




"""


from data_processing import process_data
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV, train_test_split

def mean_absolute_percentage_error(y_true, y_pred):
    import numpy as np
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100



ks = [40,40,40] #every other

params = {'colsample_bytree': [0.5], 'gamma': [0.05], 'max_depth': [4], 'min_child_weight': [4], 'n_estimators': [600], 'subsample': [0.6]}
#%%

for k_prof in ks:
    for k_hash in ks:
        
        
        print("# of profile clusters: ", k_prof)
        print("# of hashtag clusters: ", k_hash)
        
        X, y = process_data('Business Analytics/training_set.csv',k_prof = k_prof,k_hash = k_hash,training=True)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)
        model = XGBRegressor(nthread=-1) 

        grid = GridSearchCV(model, params)
        grid.fit(X_train, y_train)
        print("MAPE Train Score ")
        print(mean_absolute_percentage_error(y_train, grid.best_estimator_.predict(X_train)))
    
    
        print("MAPE Test Score ")
        print(mean_absolute_percentage_error(y_test, grid.best_estimator_.predict(X_test)))
    
      #  print("Best parameters ")
      #  print(grid.best_params_)
        
#%%
X, y = process_data('Business Analytics/training_set.csv',k_prof = 40,k_hash = 40,training=True)




from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV, train_test_split


# A parameter grid for XGBoost

# Initialize XGB and GridSearch
model = XGBRegressor(nthread=-1) 
params = {'colsample_bytree': [0.5], 'gamma': [0.05], 'max_depth': [4], 'min_child_weight': [4], 'n_estimators': [600], 'subsample': [0.6]}

grid = GridSearchCV(model, params)
grid.fit(X, y)


holdout = pd.read_csv('Business Analytics/holdout_set.csv',encoding = 'unicode_escape')

X_holdout = process_data('Business Analytics/holdout_set.csv',k_prof = 40,k_hash = 40,training=False)
holdout_predictions = grid.best_estimator_.predict(X_holdout)
holdout_predictions = np.array([int(round(y)) for y in holdout_predictions])
holdout['Engagements'] = holdout_predictions

holdout.to_csv('holdout_predictionsTEAMNAME.csv',index=False)