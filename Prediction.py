import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm
import pandas as pd
from matplotlib import style

def Build_Data_Set(features = ["Debt Equity Ratio", "Price"]):
    data_df = pd.read_csv("test.csv")

    X = np.array(data_df[features].values.tolist())

    y = (data_df["status"].replace("underperform",0).replace("outperform",1).values.tolist())


    return X,y


def Analysis():
    X, y = Build_Data_Set()

    clf = svm.SVC()

    clf.fit(X,y)

    w = clf.coef_[0]

    a = -w[0] / w[1]

    xx = np.linspace(min(X[:,0]), max(X[:, 0]))

    yy = a * xx - clf.intercept_[0] / w[1]

    h0 = plt.plot(xx,yy, "k-", label = "non-weighted")

    plt.scatter(X[:, 0], X[:, 1])
    plt.legend()
    plt.show()

Analysis()