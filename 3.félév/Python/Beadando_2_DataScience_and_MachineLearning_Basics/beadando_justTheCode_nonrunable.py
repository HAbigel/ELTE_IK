# 1. feladat
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data.csv')

df.head()


# 2. feladat
df.info()


# 3. feladat
df['Sampling Date'] = pd.to_datetime(df['Sampling Date'], errors='coerce')
df.isnull().sum()


# 4. feladat
# 4.a
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
sns.histplot(df['Nitrogen (mg/L)'], kde=True, color='blue', bins=10)
plt.title('Distribution of Nitrogen Levels')
plt.xlabel('Nitrogen (mg/L)')
plt.ylabel('Count')

plt.subplot(1, 2, 2)
sns.histplot(df['Phosphorus (mg/L)'], kde=True, color='green', bins=10)
plt.title('Distribution of Phosphorus Levels')
plt.xlabel('Phosphorus (mg/L)')
plt.ylabel('Count')

plt.tight_layout()
plt.show()


# 4.b
plt.figure(figsize=(8, 4))

sns.scatterplot(
    data=df,
    x='Geographical Location (Longitude)',
    y='Geographical Location (Latitude)',
    hue='Nitrogen (mg/L)',
    palette='coolwarm',
)
plt.title('Geographical Distribution of Nitrogen Levels')

plt.show()


# 4.c
plt.figure(figsize=(8, 4))

sns.scatterplot(
    data=df,
    x='Geographical Location (Longitude)',
    y='Geographical Location (Latitude)',
    hue='Phosphorus (mg/L)',
    palette='coolwarm',
)
plt.title('Geographical Distribution of Phosphorous Levels')

plt.show()


# 5. feladat
from matplotlib import colors
import folium

max_N = round(df['Nitrogen (mg/L)'].max())
print(max_N)
levels = range(max_N+1)
color_dict = dict(zip(levels, list(colors.cnames.values())[0:-1:10]))
color_dict

map_center = [df['Geographical Location (Latitude)'].mean(), df['Geographical Location (Longitude)'].mean()]
m = folium.Map(location=map_center, zoom_start=4, tiles='OpenStreetMap')

for ind, row in df.iterrows():
    N_level = int(round(row['Nitrogen (mg/L)']))
    folium.CircleMarker(
        location=[row['Geographical Location (Latitude)'], row['Geographical Location (Longitude)']],
        color=color_dict.get(N_level), 
        fill=True,
    ).add_to(m)

m


# 6. feladat
plt.figure(figsize=(6,6))

sns.histplot(
    data=df,
    x='State of Sewage System',
    color='blue'
)

plt.title('A szennyvízrendszer állapota')
plt.xlabel('State of Sewage System')
plt.ylabel('Count')

plt.show()


# 7. feladat
# 7.a
df['N+P'] = df['Nitrogen (mg/L)'] + df['Phosphorus (mg/L)']
df[['Geographical Location (Latitude)', 'Geographical Location (Longitude)', 'Sampling Date', 'N+P']].head()


# 7.b
from sklearn.preprocessing import LabelEncoder

le = LabelEncoder()
df['State of Sewage System'] = le.fit_transform(df['State of Sewage System'])

df['State of Sewage System'].head()


# 7.c
numerical_df = df.select_dtypes(include='number')

corr_matrix = numerical_df.corr(method='pearson')

corr_matrix


# 7.d
plt.figure(figsize=(8, 6))

sns.heatmap(
    corr_matrix,
    annot=True,
    fmt='.2f',
    cmap='coolwarm',
)

plt.title('Correlation Heatmap')
plt.show()


# 8. feladat
df = df.rename(columns={
    'Geographical Location (Latitude)': 'Lati',
    'Geographical Location (Longitude)': 'Long',
    'Sampling Date': 'SDate',
    'Nitrogen (mg/L)': 'N',
    'Phosphorus (mg/L)': 'P',
    'State of Sewage System': 'SWS'
})

df.info()


# 9. feladat
df.describe()


# 10. feladat
def q(np):
    if np < 4:
        return 1
    elif np > 10:
        return 3
    else:
        return 2

df['Q'] = df['N+P'].apply(q)
df[['N+P', 'Q']].head(15)


# 11. feladat
df.groupby('Q').size()


# 12. feladat
plt.figure(figsize=(10, 6))

sns.scatterplot(
    data=df,
    x='Long',
    y='Lati',
    hue='Q',
    palette='coolwarm',
)
plt.title('Geographical Distribution of Q Levels')

plt.show()


# 13. feladat
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

df2 = df.drop(columns=['SDate'])
df2.info()

x=df2.drop(columns=['SWS'])
y=df2['SWS']


# 14. feladat
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8, test_size=0.2)

model = DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(x_train, y_train)

plt.figure(figsize=(12, 8))
plot_tree(model, filled=True, feature_names=x.columns, class_names=['Poor', 'Moderate', 'Good'])
plt.show()


# 15. feladat
y_pred = model.predict(x_test)

accuracy_score(y_test, y_pred)

display(classification_report(y_test, y_pred))
display(confusion_matrix(y_test, y_pred))


# 16. feladat
from sklearn.linear_model import LinearRegression

x = df[['Population']]
y = df['N+P']

x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8, test_size=0.2)

lr = LinearRegression()
lr.fit(x_train, y_train)

plt.figure(figsize=(8, 6))
plt.scatter(x, y, color='red')
plt.plot(x, lr.predict(x), color='blue')
plt.xlabel('Population (teszt halmaz)')
plt.ylabel('N+P (teszt halmaz)')
plt.title('Linear Regression a teszt adatokra')
plt.show()


# 17. feladat
y_pred = lr.predict(x_test)

display(y_pred[:5])
display(y_test.values[:5])

display(lr.score(x_test, y_test))
