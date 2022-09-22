from sklearn.cluster import KMeans
import numpy as np
import csv

X = []
with open("data/stats_deoutavg_only.csv", newline="") as csvfile:
    statreader = csv.reader(csvfile, delimiter=",", quotechar="|")
    for row in statreader:
        if row[0] != "name":
            X.append([float(element) for element in row[1:]])

X = np.array(X)

X_max = X.max(axis=0)
X_normed = X / X_max

kmeans_abs = KMeans(n_clusters=2, random_state=0).fit(X)
print("Absolute: ", kmeans_abs.labels_)

kmeans_norm = KMeans(n_clusters=2, random_state=0).fit(X_normed)
print("Normalized: ", kmeans_norm.labels_)
