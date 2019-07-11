"""
Machine learning model used to train and predict the # of engagements a given instagram post will receive, based on an array of over 50 features, 
exploring information ranging from the # of followers gained since the last post, popularity of the profiles and hashtags used, day of the week, hour, year, month, 
and many more. 




"""


from data_processing import process_data
import numpy as np
import pandas as pd

from xgboost import XGBRegressor

def mean_absolute_percentage_error(y_true, y_pred):
    import numpy as np
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


model = XGBRegressor(colsample_bytree =0.5, gamma = 0.05, max_depth = 4, min_child_weight = 4, n_estimators = 1000, subsample = 0.6) 


# Initialize XGB
holdout_prediction_population = []
prediction_run = 0
while prediction_run  < 5:
	X, y = process_data('Business Analytics/training_set.csv',k_prof = 300,k_hash = 300,training=True)
	model.fit(X, y)

	holdout = pd.read_csv('Business Analytics/holdout_set.csv',encoding = 'unicode_escape')
	X_holdout = process_data('Business Analytics/holdout_set.csv',k_prof = 300,k_hash = 300,training=False)
	holdout_predictions = model.predict(X_holdout)
	holdout_predictions = np.array([int(round(y)) for y in holdout_predictions])
	holdout_prediction_population.append(holdout_predictions)


for i,_ in enumerate(holdout_predictions): #iterate over each test point
	ith_values_predictions = holdout_prediction_population[:,i]
	#get the median, and make that the new prediction 
holdout['Engagements'] = holdout_predictions




#holdout.to_csv('holdout_set_TEAM_NAME.csv',index=False)