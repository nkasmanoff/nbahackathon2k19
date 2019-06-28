"""
Machine learning model used to train and predict the # of engagements a given instagram post will receive, based on an array of over 50 features, 
exploring information ranging from the # of followers gained since the last post, popularity of the profiles and hashtags used, day of the week, hour, year, month, 
and many more. 




"""


from data_processing import process_data
import numpy as np
import pandas as pd
X, y = process_data('Business Analytics/training_set.csv',training=True)


def mean_absolute_percentage_error(y_true, y_pred):
    import numpy as np
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01)



# A parameter grid for XGBoost
params = {'min_child_weight':[3,4], 'gamma':[i/10.0 for i in [.5,1,1.5]],  'subsample':[i/10.0 for i in range(5,7)],
'colsample_bytree':[i/10.0 for i in range(5,6)], 'max_depth': [4],'n_estimators':[525,550]}


# Initialize XGB and GridSearch
model = XGBRegressor(nthread=-1) 

grid = GridSearchCV(model, params)
grid.fit(X, y)

print("MAPE Test Score ")
print(mean_absolute_percentage_error(y, grid.best_estimator_.predict(X)))

print("Best parameters ")
print(grid.best_params_)


holdout = pd.read_csv('Business Analytics/holdout_set.csv',encoding = 'unicode_escape')

X_holdout = process_data('Business Analytics/holdout_set.csv',training=False)
holdout_predictions = grid.best_estimator_.predict(X_holdout)
holdout_predictions = np.array([int(round(y)) for y in holdout_predictions])
holdout['Engagements'] = holdout_predictions

holdout.to_csv('holdout_predictionsTEAMNAME.csv',index=False)