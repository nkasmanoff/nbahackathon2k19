"""
Machine learning model used to train and predict the # of engagements a given instagram post will receive, based on an array of over 50 features, 
exploring information ranging from the # of followers gained since the last post, popularity of the profiles and hashtags used, day of the week, hour, year, month, 
and many more. 


Going to predict 10 models, and use the median as final submission

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
while prediction_run  < 10:
	X, y = process_data('Business Analytics/training_set.csv',k_prof = 300,k_hash = 300,training=True)
	model.fit(X, y)

	holdout = pd.read_csv('Business Analytics/holdout_set.csv',encoding = 'unicode_escape')
	X_holdout = process_data('Business Analytics/holdout_set.csv',k_prof = 300,k_hash = 300,training=False)
	holdout_predictions = model.predict(X_holdout)
	holdout_predictions = np.array([int(round(y)) for y in holdout_predictions])
	holdout_prediction_population.append(holdout_predictions)
	prediction_run +=1
	print("Prediction run ")


holdout_prediction_population = np.array(holdout_prediction_population).reshape(10,1000) #confirm right format and shape

eng_pred_med = []
eng_pred_std = []
eng_pred_avg = []

for i in range(holdout_prediction_population.shape[1]): #iterate over each test point
	print(i)
	eng_pred_med.append(np.median(holdout_prediction_population[:,i]))
	eng_pred_std.append(np.std(holdout_prediction_population[:,i]))
	eng_pred_avg.append(np.mean(holdout_prediction_population[:,i]))


	#get the median, and make that the new prediction 
holdout['Engagements'] = eng_pred_med
#holdout['Engagements Std'] = eng_pred_std
#holdout['Engagements Avg'] = eng_pred_avg



holdout.to_csv('holdout_set_FunGuys.csv',index=False)