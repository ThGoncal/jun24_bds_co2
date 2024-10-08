import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from PIL import Image

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder

from joblib import load
import streamlit as st

#################################
# Création de la page Streamlit #
#################################

st.title("Emission de CO2 par les véhicules")
st.sidebar.title("Sommaire")
pages=["Présentation du projet", "Exploration", "Data Visualisation",
    "Modélisations", "Votre prédiction", "Quelques exemples types", "Conclusions"]
page=st.sidebar.radio("Aller vers", pages)

### Page de présentation
if page == pages[0] : 
    st.header("Présentation du projet")
    image = Image.open('Emission_CO2.png')
    st.image(image)
    st.write("Le transport routier contribue à environ un cinquième des émissions totales de l'Union européenne (UE) de dioxyde de carbone (CO2), le principal gaz à effet de serre (GES), dont 75 % proviennent des voitures particulières.")
    st.write('Notre objectif est d’identifier les différents facteurs et caractéristiques techniques jouant un rôle dans la pollution émise par les véhicules. Prédire à l’avance la pollution de certains types de véhicules est une information cruciale pour opérer une décarbonation de l’industrie automobile.')
    st.write(f"Nous disposons de données mises à disposition par l'[European Environment Agency](https://www.eea.europa.eu/en/datahub/datahubitem-view/fa8b1229-3db6-495d-b18e-9c9b3267c02b), pour les véhicules enregistrés au sein de l'UE, et par l'[Agence de l'environnement et de la maîtrise de l'énergie](https://www.data.gouv.fr/fr/datasets/emissions-de-co2-et-de-polluants-des-vehicules-commercialises-en-france/#_), pour les véhicules français.")
    st.write('La volumétrie ainsi que l’absence notable de la variable associée à la consommation de carburant dans le jeu de données européen, nous conduit à privilégier la source données de l’ADEME. Le jeu de données retenu est constitué par les données disponibles en France entre 2012 et 2015, représentant 160 826 observations.')
    
### Exploration des données
file = 'data_2012-2015.csv'
df = pd.read_csv(file, on_bad_lines="skip", sep= ',', low_memory=False)
if page == pages[1] :
    st.header("Exploration des données")
    st.write('Nous nous intéressons aux données des véhicules enregistrés France entre 2012 et 2015.')
    st.subheader("Aperçu du jeu de données")
    st.dataframe(df.head(5))
    st.write("Il y a", df.shape[0], "observations dans notre dataset et", df.shape[1], "colonnes les caractérisant.")
    st.subheader("Informations principales sur le jeu de données")
    st.dataframe(df.describe())
    st.subheader("Valeurs manquantes")
    st.write("On observe assez peu de valeurs manquantes dans le dataset.")
    st.write("Deux variables en particulier présentent un grand nombre de valeurs manquantes (16 : HC (g/km) et 23 : Date de mise à jour). Ces variables seront donc supprimées. La présence d’un quantité non négligeable de valeurs manquantes dans les variables Carrosserie et gamme est provoquée par l’inclusion du jeu de données de 2015 (ces variables y sont absentes).")
    if st.checkbox("Afficher les NA") :
        st.dataframe(df.isna().sum())

### Visualisation
if page == pages[2] : 
    st.header("Data Vizualization")

    # Heatmap
    st.subheader('Heatmap')
    st.write("Afin de pouvoir déterminer plus facilement les variables numériques à cibler, il est possible de créer une heatmap. Un intérêt particulier sera donné aux variables ayant un fort degré de corrélation (le plus éloigné de 0) avec la variable cible : CO2 (g/km).")
    variables_num = df.select_dtypes(include = ['int64', 'float64'])
    cor = variables_num.corr()
    fig_heatmap = px.imshow(cor)
    st.plotly_chart(fig_heatmap) 
    st.write("Plusieurs variables sont corrélées avec la variable cible, notamment une, avec un degré de corrélation très élevé (0.97) : la Consommation mixte (l/100km), qui, comme son nom l’indique, donne la consommation en carburant du véhicule en litre pour 100 km (urbaine et extra-urbaine).") 
    st.write("Observons plus en détail la relation entre consommation mixte et émissions de CO2.")

    # Nuage de points conso mixte et CO2
    dictionnaire_carburant = {"GO":"Gazole",
             "ES":"Essence",
             "EH":"Essence",
             "GH":"Gazole",
             "ES/GN":"Essence",
             "GN/ES":"Gaz Naturel Vehicule (GNV)",
             "ES/GP":"Essence",
             "GP/ES":"Gaz de Petrole Liquefie (GPL)",
             "EL":"Electrique",
             "GN":"Gaz Naturel Vehicule (GNV)",
             "EE":"Essence",
             "FE":"SuperEthanol-E85",
             "GL":"Gazole"}
    st.subheader('Nuage de points - émissions de CO2 (g/km) en fonction de la consommation mixte (l/100km) selon le carburant utilisé')
    df['Carburant'] = df['Carburant'].replace(dictionnaire_carburant)
    fig_scatter = px.scatter(df, x="Consommation mixte (l/100km)", y="CO2 (g/km)", color = 'Carburant',
                 title='CO2 émis selon la consommation de carburant mixte et le type de carburant utilisé')
    st.plotly_chart(fig_scatter) 
    st.write("Comme attendu, les points se regroupent de façon linéaire, ce qui signifie que cette variable nous sera utile pour prédire les émissions.")
    st.write("Toutefois, plusieurs droites semblent se dessiner. Cela indique donc qu'une variable supplémentaire affecte les résultats, certainement une variable catégorielle : le carburant.")
    st.write("La faible présence sur le graphique de véhicules utilisant un carburant autre que l’essence ou le gazole indique un potentiel déséquilibre dans le jeu de données. Observons cela de plus près.")

    # Répartition des carburants
    st.subheader("Proportion de chaque type de motorisation")
    # Pie Chart
    occurence = []
    l = df['Carburant'].unique()
    for i in range (len(l)) :
        occurence.append(df.loc[df['Carburant'] == l[i]].count()[0])
    from plotly.subplots import make_subplots
    fig = make_subplots(rows = 1,
                    cols = 2,
                    specs=[[{'type':'domain'}, {'type':'domain'}]],
                    subplot_titles = ['Répartition globale', 'Zoom'],
                    )

    colors = ['lightblue','green','lightseagreen','antiquewhite','cadetblue','darkorange','goldenrod']
    fig.add_trace(go.Pie(labels = l,
                     values = occurence,
                     marker_line = dict(color = 'black', width = 1.5), # Couleur et épaisseur de la ligne
                     marker_colors = colors,  # Couleur de chaque partie du camembert
                     pull = [0,0.1,0,0,0,0],
                      name = 'Global'),
                      row = 1, col = 1)

    l_1 = np.delete(l, [0,1])
    occurence_sans_maj = []
    for i in range (len(l_1)) :
        occurence_sans_maj.append(df.loc[df['Carburant'] == l_1[i]].count()[0])

    fig.add_trace(go.Pie(labels = l_1,
                      values = occurence_sans_maj,
                    name = 'Zoom'),
                    row = 1, col = 2)

    fig.update_layout(title="Types de carburants des véhicules enregistrés en France entre 2012 et 2015",showlegend=True, legend_title = 'Légende')
    st.plotly_chart(fig) 
    st.write("Il y a une très forte représentation de véhicules utilisant du gazole comme carburant (84,2%), et dans une bien moindre mesure, les véhicules essence (15.3%). Les quatre autres motorisations ne représentent au final qu'un total de 0.5% du jeu de données restant. Ce déséquilibre entre les types de carburants présents peut entraîner un biais qui peut fausser les prédictions d’émission des véhicules utilisant ces types de carburants sous-représentés.")

    # Boîte à moustache
    st.subheader("Boîte à moustaches (Box plot) de l'émission de CO2 (g/km) en fonction du type de carburant")
    st.write("Le graphique ci-dessous doit nous permettre de vérifier la distribution des valeurs d’émissions des véhicules selon le type de carburant utilisé, afin, entre autre, de faire apparaître d’éventuelles valeurs aberrantes.")
    fig_boxplot = px.box(df, x = 'Carburant', y = 'CO2 (g/km)')
    st.plotly_chart(fig_boxplot)
    st.write("La présence de points hors des boîtes (notamment dans la catégorie gazole) indique la présence de valeurs éloignées du reste des autres valeurs. Toutefois, leurs écarts ne semblent pas significatifs, ce qui signifie que ces valeurs, bien que extrêmes, restent valables et peuvent donc être gardées dans le jeu de données.")

################
# Modélisation #
################

class CustomRegression():
    def __init__(self):
            
        self.w_c1 = tf.Variable(tf.random.normal([1]), name='weight_carb_1')
        self.w_c2 = tf.Variable(tf.random.normal([1]), name='weight_carb_2')
        self.w_c3 = tf.Variable(tf.random.normal([1]), name='weight_carb_3')
        self.w_c4 = tf.Variable(tf.random.normal([1]), name='weight_carb_4')
        self.w_c5 = tf.Variable(tf.random.normal([1]), name='weight_carb_5')

        self.b_c1 = tf.Variable(tf.random.normal([1]), name='bias_carb_1')
        self.b_c2 = tf.Variable(tf.random.normal([1]), name='bias_carb_2')
        self.b_c3 = tf.Variable(tf.random.normal([1]), name='bias_carb_3')
        self.b_c4 = tf.Variable(tf.random.normal([1]), name='bias_carb_4')
        self.b_c5 = tf.Variable(tf.random.normal([1]), name='bias_carb_5')

    def __call__(self, conso, carb1, carb2, carb3, carb4, carb5):

        conso = tf.convert_to_tensor(conso, dtype=tf.float32)

        carb1 = tf.convert_to_tensor(carb1, dtype=tf.float32)
        carb2 = tf.convert_to_tensor(carb2, dtype=tf.float32)
        carb3 = tf.convert_to_tensor(carb3, dtype=tf.float32)
        carb4 = tf.convert_to_tensor(carb4, dtype=tf.float32)
        carb5 = tf.convert_to_tensor(carb5, dtype=tf.float32)
            
        return carb1 * (conso * self.w_c1 + self.b_c1) + carb2 * (conso * self.w_c2 + self.b_c2) + carb3 * (conso * self.w_c3 + self.b_c3) + carb4 * (conso * self.w_c4 + self.b_c4) + carb5 * (conso * self.w_c5 + self.b_c5)

def affichage_metrics(residus, y_pred, y_test):
    st.write("MSQE : {:.2f}".format(mean_squared_error(y_test, y_pred)))
    st.write("MAE : {:.2f}".format(mean_absolute_error(y_test, y_pred)))

    st.write("\nProportion < 1% d'ecart  : {:.2f}%".format((len(residus[residus<1]) / len(residus)) * 100))
    st.write("Proportion < 5% d'ecart  : {:.2f}%".format((len(residus[residus<5]) / len(residus)) * 100))
    st.write("Proportion < 10% d'ecart : {:.2f}%".format((len(residus[residus<10]) / len(residus)) * 100))

def calcul_residus(y_pred, y_test):
    residus = []
    for i in range(len(y_test)):
        residus.append(((y_pred[i] - y_test.values[i]) / y_test.values[i]) * 100)

    return np.absolute(residus)

###############################################
# Chargement et préparation du jeu de données #
###############################################

@st.cache_data
def chargement_dataset():
    #scaler = StandardScaler()
    encoder_le =  LabelEncoder()

    file = 'data_2012-2015.csv'
    df_original = pd.read_csv(file, on_bad_lines="skip", sep= ',', low_memory=False)

    liste_cbr = {"GO":"Gazole",
                "ES":"Essence",
                "EH":"Essence",
                "GH":"Gazole",
                "ES/GN":"Essence",
                "GN/ES":"Gaz Naturel Vehicule (GNV)",
                "ES/GP":"Essence",
                "GP/ES":"Gaz de Petrole Liquefié (GPL)",
                "EL":"Electrique",
                "GN":"Gaz Naturel Vehicule (GNV)",
                "EE":"Essence",
                "FE":"SuperEthanol-E85",
                "GL":"Gazole"}

    df_original["Carburant"] = df_original["Carburant"].replace(liste_cbr)

    df = df_original[["Consommation mixte (l/100km)", "Carburant", "CO2 (g/km)", "Puissance administrative","masse vide euro min (kg)"]]
    df = df.dropna(how="any")

    df_carb = pd.get_dummies(df["Carburant"])
    df_carb = df_carb.replace({True:1, False:0})

    df["Carburant"] = encoder_le.fit_transform(df["Carburant"])

    X_dt = df.drop(columns="CO2 (g/km)")
    X_dl = pd.concat([df[["Consommation mixte (l/100km)", "Puissance administrative","masse vide euro min (kg)"]], df_carb], axis=1)
    X_ts = pd.concat([df["Consommation mixte (l/100km)"], df_carb], axis=1)

    y_dt = df["CO2 (g/km)"]
    y_dl = df["CO2 (g/km)"]
    y_ts = df["CO2 (g/km)"]

    return df_original, X_dt, y_dt, X_dl, y_dl, X_ts, y_ts

##########################
# Chargement des modèles #
##########################

@st.cache_data
def chargement_models():

    # Chargement du modèle DecisionTree
    model_dt = load("decision_tree")

    # Chargement du réseau de neurones
    model_dl = load("model_dl2")

    # Chargement du modèle custom TensorFlow
    model_tf = load("model_tf_france")

    return model_dt, model_dl, model_tf

df_original, X_dt, y_dt, X_dl, y_dl, X_ts, y_ts = chargement_dataset()

scaler = StandardScaler()
X_dt = scaler.fit_transform(X_dt)
scaler2 = StandardScaler()
X_dl = scaler2.fit_transform(X_dl)

X_dt_train, X_dt_test, y_dt_train, y_dt_test = train_test_split(X_dt, y_dt, test_size=0.2, random_state=9001)
X_dl_train, X_dl_test, y_dl_train, y_dl_test = train_test_split(X_dl, y_dl, test_size=0.2, random_state=9001)
X_ts_train, X_ts_test, y_ts_train, y_ts_test = train_test_split(X_ts, y_ts, test_size=0.2, random_state=9001)

model_dt, model_dl, model_tf = chargement_models()

if page == pages[3] : 
    st.header("Modélisations")
    st.write("Pour ce projet, nous avons essayé plusieurs modèles de Machine Learning et Deep Learning. Vous retrouverez ici les résultats de trois de nos modèles les plus performants.")
    choix = ['DecisionTree', 'Réseau de neurones'
             , 'Modèle custom TensorFlow']
    option = st.selectbox('Choix du modèle', choix)
    st.subheader(f"Le modèle choisi est : {option}")

    # Prédiction avec le modèle DecisionTree
    if option == 'DecisionTree':
        st.subheader("Métriques d'évaluations")
        y_pred = model_dt.predict(X_dt_test) 
        residus = calcul_residus(y_pred, y_dt_test)
        affichage_metrics(residus, y_pred, y_dt_test)
        
        st.subheader("Prédictions du modèle vs Valeurs réelles")
        fig = plt.figure()
        plt.scatter(y_pred, y_dt_test, s=5,  c="g")
        plt.plot((0, 600), (0, 600))
        plt.xlabel('Prédictions')
        plt.ylabel('Valeurs réelles')
        st.pyplot(fig)

        st.subheader('Description de notre modèle de Machine Learning')
        st.write("En effectuant une recherche par GridSearchCV, on se rend compte que le paramètre 'max_depth' optimal s’établit à ‘None'. ")
        st.write("Nous utilisons en entrée nos quatre variables explicatives (puissance administrative, consommation mixte, masse vide min, carburant)")
        st.write("En Machine Learning, nos modèles donnaient rapidement d'excellents résultats, comparables entre eux, ce qui nous a poussé à préférer le modèle DecisionTreeRegressor qui est a priori plus facilement interprétable.")

    # Prédiction avec le réseau de neurones
    if option == 'Réseau de neurones':
      st.subheader("Métriques d'évaluations")
      y_pred = model_dl.predict(X_dl_test)
      residus = calcul_residus(y_pred, y_dl_test)
      affichage_metrics(residus, y_pred, y_dl_test)
      
      st.subheader("Prédictions du modèle vs Valeurs réelles")
      fig = plt.figure()
      plt.scatter(y_pred, y_dl_test, s=5,  c="g")
      plt.plot((0, 600), (0, 600))
      plt.xlabel('Prédictions')
      plt.ylabel('Valeurs réelles')
      st.pyplot(fig)

      st.subheader('Description de notre modèle de Deep Learning')
      st.write('En entrée, nous utilisons ici nos 4 variables (puissance administrative, consommation mixte, masse vide min, carburant). Pour des raisons de performance, la variable Carburant est transformée en cinq variables indicatrices.') 
      st.write('Caractéristiques :')
      st.write("- Une première couche dense de 16 neurones avec la fonction d’activation ‘relu’,")
      st.write("- Une seconde couche de sortie à 1 neurone,")
      st.write("- Une fonction de perte ‘mean square error’ et l’optimizer ‘adam’,")
      st.write("- 100 epochs ainsi qu’un batch_size de 32.")

    # Prédiction avec le modèle custom TensorFlow
    if option == 'Modèle custom TensorFlow':
      st.subheader("Métriques d'évaluations")
      y_pred = model_tf(X_ts_test[X_ts_test.columns[0]], X_ts_test[X_ts_test.columns[1]], X_ts_test[X_ts_test.columns[2]], X_ts_test[X_ts_test.columns[3]], X_ts_test[X_ts_test.columns[4]], X_ts_test[X_ts_test.columns[5]])
      residus = calcul_residus(y_pred, y_ts_test)
      affichage_metrics(residus, y_pred, y_ts_test)
      
      st.subheader("Prédictions du modèle vs Valeurs réelles")
      fig = plt.figure()
      plt.scatter(y_pred, y_ts_test, s=5, c="g")
      plt.plot((0, 600), (0, 600))
      plt.xlabel('Prédictions')
      plt.ylabel('Valeurs réelles')
      st.pyplot(fig)

      st.subheader('Description de notre modèle personnalisé')
      st.write("En entrée, nous utilisons ici 6 variables (consommation mixte et, comme pour le modèle précédent, les 5 variables d'état correspondant à chaque type de carburant).")
      st.write('Caractéristiques :')
      st.write("Nous avons utilisé la bibliothèque tensorflow pour entraîner un modèle contraint à 5 régressions linéaires, une pour chacune des 5 catégories de carburant.")
      st.write("Nous avons ainsi créé une class CustomRegression pour définir ce modèle à 10 variables (la pente et l’ordonnée à l’origine des 5 régressions linéaires) ainsi qu’une fonction d’entraînement de ce modèle utilisant la méthode du gradient avec les éléments disponibles de tensorflow.")
      st.write("Ce modèle est finalement celui que l’on retient à l’issue de notre travail.")

#######################
# Faire sa prédiction #
#######################

def user_input_features():
    Consommation_mixte = st.slider('Consommation mixte (l/100km)', float(df['Consommation mixte (l/100km)'].min()),
                                            float(df['Consommation mixte (l/100km)'].max()),  df['Consommation mixte (l/100km)'].mean())
    Carburant = st.select_slider(label = 'Choisissez votre type de carburant',options = ['Essence', 'Gaz Naturel Vehicule (GNV)', 'Gaz de Petrole Liquefié (GPL)', 'Gazole', 'SuperEthanol-E85'])
    Puissance_administrative = st.slider('Puissance administrative', float(df['Puissance administrative'].min()),
                                            float(df['Puissance administrative'].max()),  df['Puissance administrative'].mean())
    masse_vide_euro_min = st.slider('masse vide euro min (kg)', float(df['masse vide euro min (kg)'].min()),
                                            float(df['masse vide euro min (kg)'].max()),  df['masse vide euro min (kg)'].mean())
    DATA = {'Consommation mixte (l/100km)' :  Consommation_mixte,
            "Carburant" : Carburant,
        'Puissance administrative' : Puissance_administrative,
        'masse vide euro min (kg)' : masse_vide_euro_min}
    features = pd.DataFrame(DATA, index = [0])
    return features

def labelisation_carburant(feature) :
    dict = {'Essence' : 0, 
            'Gaz Naturel Vehicule (GNV)' : 1, 
            'Gaz de Petrole Liquefié (GPL)' : 2,
            'Gazole' : 3,
            'SuperEthanol-E85' : 4}
    feature.Carburant = feature.Carburant.replace(dict)
    return feature

def construction_col_car(df):
    # Boucle sur chaque type de carburant
    for carb in ['Essence', 'Gaz Naturel Vehicule (GNV)', 'Gaz de Petrole Liquefié (GPL)', 'Gazole', 'SuperEthanol-E85']:
        # Créer une nouvelle colonne pour chaque type de carburant et y attribuer 1 ou 0
        df[carb] = df['Carburant'].apply(lambda x: 1 if x == carb else 0)
    return df

if page == pages[4] : 
    st.header("Votre prédiction")
    choix = ['DecisionTree', 'Réseau de neurones'
             , 'Modèle custom TensorFlow']
    option = st.selectbox('Choix du modèle', choix)
    st.write('Le modèle choisi est :', option)

    if option == 'DecisionTree':
        st.subheader("Prédiction avec le décision tree")
        df_user = user_input_features()
        st.dataframe(df_user)
        # modification de X_pred pour correspondre au format attendu par le modèle
        X_pred_dt = labelisation_carburant(df_user)
        #scaler = StandardScaler()
        #a = scaler.fit(X)
        X_pred_dt = scaler.transform(X_pred_dt)
        # prédiciton avec le décision tree
        y_pred_dt = model_dt.predict(X_pred_dt)
        st.write(f"Les émissions de CO2 prédites par le décision tree pour ce modèle de voiture est {y_pred_dt[0]} grammes par kilomètre.") 

    if option == 'Réseau de neurones':
        st.subheader("Les fonctionnalités de votre voiture")
        # sidebar
        st.sidebar.header('Entrez vos paramètres')
        # affichage des paramètres choisis
        df_user = user_input_features()
        st.dataframe(df_user)

        st.subheader("Prédiction avec notre custom model")
        df_user_carb = construction_col_car(df_user)
        X_pred_dl = df_user_carb[['Consommation mixte (l/100km)', 'Puissance administrative', 'masse vide euro min (kg)', 'Essence', 'Gaz Naturel Vehicule (GNV)', 'Gaz de Petrole Liquefié (GPL)', 'Gazole', 'SuperEthanol-E85']]
        X_pred_dl = scaler2.transform(X_pred_dl)
        # prédiciton avec le décision tree
        y_pred_dl = model_dl.predict(X_pred_dl)
        st.write(f"Les émissions de CO2 prédites par le réseau de neurones pour ce modèle de voiture est {y_pred_dl[0][0]} grammes par kilomètre.") 


    if option == 'Modèle custom TensorFlow':
        st.subheader("Les fonctionnalités de votre voiture")
        # sidebar
        st.sidebar.header('Entrez vos paramètres')
        # affichage des paramètres choisis
        df_user = user_input_features()
        st.dataframe(df_user)

        st.subheader("Prédiction avec notre custom model")
        # préparation à la modélisation
        df_user_carb = construction_col_car(df_user)
        X_pred_tf = df_user_carb[['Consommation mixte (l/100km)', 'Essence', 'Gaz Naturel Vehicule (GNV)', 'Gaz de Petrole Liquefié (GPL)', 'Gazole', 'SuperEthanol-E85']]

        # prédiction avec notre custom modèle
        y_pred_tf = model_tf(X_pred_tf[X_pred_tf.columns[0]], X_pred_tf[X_pred_tf.columns[1]], X_pred_tf[X_pred_tf.columns[2]], X_pred_tf[X_pred_tf.columns[3]], X_pred_tf[X_pred_tf.columns[4]], X_pred_tf[X_pred_tf.columns[5]])
        st.write(f"Les émissions de CO2 prédites pour ce modèle de voiture est {y_pred_tf[0]} grammes par kilomètre.") 

if page == pages[5] : 
    st.header("Quelques prédictions pour des voitures que l'on connaît tous")
    choix = ['Renault Megane', 'Renault Espace']
    option = st.selectbox('Choix du modèle de voiture', choix)
    st.write('La voiture choisie est :', option)

    if option == 'Renault Megane':
        # ajout des valeurs de conso mixte et de type de carburant
        X_megane = [1.4, 1, 0, 0, 0, 0]
        y_megane =  model_tf(X_megane[0], X_megane[1], X_megane[2], X_megane[3], X_megane[4], X_megane[5])
        st.write(f"Les émissions de CO2 prédites pour ce modèle de voiture est {y_megane[0]} grammes par kilomètre.") 

    if option == 'Renault Espace':
        # ajout des valeurs de conso mixte et de type de carburant
        X_espace = [4.7, 1, 0, 0, 0, 0]
        y_espace =  model_tf(X_espace[0], X_espace[1], X_espace[2], X_espace[3], X_espace[4], X_espace[5])
        st.write(f"Les émissions de CO2 prédites pour ce modèle de voiture est {y_espace[0]} grammes par kilomètre.") 

