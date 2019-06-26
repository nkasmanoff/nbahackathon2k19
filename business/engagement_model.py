"""
Machine learning model used to train and predict the # of engagements a given instagram post will receive, based on an array of over 50 features, 
exploring information ranging from the # of followers gained since the last post, popularity of the profiles and hashtags used, day of the week, hour, year, month, 
and many more. 




"""


from data_processing import process_data
import numpy as np

X, y = process_data('Business Analytics/training_set.csv',training=True)


def mean_absolute_percentage_error(y_true, y_pred):
    import numpy as np
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


from xgboost import XGBRegressor
model = XGBRegressor(booster='dart',colsample_bytree= 0.5,
 gamma= 0.1,
 max_depth=4,
 min_child_weight= 4,
 n_estimators=525,
 subsample= 0.5)#choice(models)

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)
model.fit(X_train,y_train)
print("Model used: ", model)
print("Training score: ", model.score(X_train,y_train))
print("Test Score", model.score(X_test,y_test))

def mean_absolute_percentage_error(y_true, y_pred):
    import numpy as np
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

y_true = y_test
y_pred = model.predict(X_test) 

#y_pred = np.array([round(y) for y in y_pred])

print("MAPE Test Score ", mean_absolute_percentage_error(y_true, y_pred))


print("Holdout Engagements")
X_holdout = process_data('Business Analytics/holdout_set.csv')

holdout_predictions = model.predict(X_holdout)
holdout_predictions = np.array([round(y) for y in holdout_predictions])
print(holdout_predictions)