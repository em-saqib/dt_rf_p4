# load packeges
import pandas as pd
import numpy as np
import pickle
import pydotplus
import matplotlib.pyplot as plt
from sklearn.utils import shuffle
from sklearn import preprocessing
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn.feature_selection import SelectKBest, chi2, mutual_info_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, KFold, train_test_split, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score,classification_report
import argparse

parser = argparse.ArgumentParser()

# Add argument
parser.add_argument('-i', required=True, help='path to dataset')

args = parser.parse_args()

# extract argument
input = args.i

df = pd.read_csv(input)


# Apply sampling
# Now take 10% samples only
df = df.sample(n=None, frac=0.05, replace=False, weights=None, random_state=None, axis=0)
df = df.sort_index()

# Preprocessing
X = df.iloc[:, df.columns != 'Label']
y = df[['Label']].to_numpy()
# label encoding
le = preprocessing.LabelEncoder().fit(y)
y = le.transform(y)
# train test split
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size = 0.7, test_size = 0.3, random_state=0, shuffle=True)

# RFC CLassifier
num_trees = 3  # the number of trees in the classifer
rfc = RandomForestClassifier(max_depth=10, n_estimators=num_trees)
rfc.fit(X_train, y_train)
print("Accuracy on training set: {:.3f}".format(rfc.score(X_train, y_train)))
print("Accuracy on test set:     {:.3f}".format(rfc.score(X_test, y_test)))

# Classification Report
y_pred = rfc.predict(X_test)
print('Prediction Accuracy:      %s' % accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, labels=range(2)))

"""**Save the RFC model**"""

# same the model
import pickle

# # Assume rf_model is your trained Random Forest model
with open('rfc.pkl', 'wb') as f:
    pickle.dump(rfc, f)
