
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Suivi des livraisons",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Application de suivi et d’analyse des livraisons")
st.caption("Importation, traitement et visualisation des données de livraison")

uploaded_file = st.sidebar.file_uploader(
    "Importer le fichier des livraisons",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is None:
    st.info("Importez votre fichier Excel ou CSV pour commencer l’analyse.")
    st.stop()

try:
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

except Exception as e:
    st.error(f"Impossible de lire le fichier : {e}")
    st.stop()

# Nettoyage des noms de colonnes
df.columns = df.columns.astype(str).str.strip().str.upper()

required = [
    "ID",
    "VILLE",
    "DATE LIVRAISON REELLE",
    "DATE LIVRAISON PREVUE",
    "RETARD"
]

missing = [c for c in required if c not in df.columns]

if missing:
    st.error("Colonnes manquantes : " + ", ".join(missing))
    st.write("Colonnes trouvées :", list(df.columns))
    st.stop()

# Conversion des dates
colonnes_dates = [
    "DATE LIVRAISON REELLE",
    "DATE LIVRAISON PREVUE"
]

for col in colonnes_dates:
    if col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_datetime(
                df[col],
                unit="D",
                origin="1899-12-30",
                errors="coerce"
            )
        else:
            df[col] = pd.to_datetime(
                df[col],
                dayfirst=True,
                errors="coerce"
            )

# Utiliser la colonne RETARD originale
df["RETARD"] = (
    df["RETARD"].astype(str).str.strip().str.upper()
)

df["STATUT"] = df["RETARD"].map({
    "OUI": "En retard",
    "NON": "Livré à temps"
})

# Calcul des jours de retard

if "JOURS DE RETARD" in df.columns:
    df["JOURS DE RETARD"] = pd.to_numeric(
        df["JOURS DE RETARD"], errors="coerce"
    )
else:
    df["JOURS DE RETARD"] = (
        df["DATE LIVRAISON REELLE"] -
        df["DATE LIVRAISON PREVUE"]
    ).dt.days.clip(lower=0)

df["JOURS DE RETARD"] = df["JOURS DE RETARD"].fillna(0)
st.subheader("Test des données")
st.write("Valeurs RETARD :", df["RETARD"].value_counts())
st.write("Dates réelles reconnues :", df["DATE LIVRAISON REELLE"].notna().sum())
st.write("Dates prévues reconnues :", df["DATE LIVRAISON PREVUE"].notna().sum())
st.write("Jours de retard :", df["JOURS DE RETARD"].describe())
st.write("Répartition par ville :")
st.write(df.groupby("VILLE")["JOURS DE RETARD"].agg(["count", "mean", "max"]))

st.write("Exemple des retards :")
st.write(df[["VILLE", "RETARD", "JOURS DE RETARD"]].head(10))

# Filtres
st.sidebar.header("Filtres")

cities = sorted(df["VILLE"].dropna().astype(str).unique())

selected_cities = st.sidebar.multiselect(
    "Ville", cities, default=cities
)

statuses = ["Livré à temps", "En retard"]

selected_status = st.sidebar.multiselect(
    "Statut", statuses, default=statuses
)

filtered = df[
    df["VILLE"].astype(str).isin(selected_cities)
    & df["STATUT"].isin(selected_status)
]

# Indicateurs
n_total = len(filtered)
n_late = int((filtered["STATUT"] == "En retard").sum())
n_ontime = int((filtered["STATUT"] == "Livré à temps").sum())

late_rate = (n_late / n_total * 100) if n_total else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total des livraisons", n_total)
c2.metric("Livraisons à temps", n_ontime)
c3.metric("Livraisons en retard", n_late)
c4.metric("Taux de retard", f"{late_rate:.1f}%")

# Graphiques
st.subheader("📊 Visualisation des livraisons")

left, right = st.columns(2)

with left:
    counts = filtered["STATUT"].value_counts().reindex(
        statuses, fill_value=0
    )

    fig, ax = plt.subplots()
    counts.plot(kind="bar", ax=ax)
    ax.set_xlabel("Statut")
    ax.set_ylabel("Nombre de livraisons")
    ax.set_title("Livraisons selon le statut")
    ax.tick_params(axis="x", rotation=0)

    st.pyplot(fig)
    plt.close(fig)

with right:
    by_city = filtered.groupby("VILLE")["JOURS DE RETARD"].mean()

    fig, ax = plt.subplots()
    by_city.plot(kind="bar", ax=ax)
    ax.set_xlabel("Ville")
    ax.set_ylabel("Moyenne des jours de retard")
    ax.set_title("Retard moyen par ville")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

# Tableau
st.subheader("📋 Détail des livraisons")
st.dataframe(filtered, use_container_width=True, hide_index=True)

# Exportation
csv = filtered.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "⬇️ Télécharger les données analysées (CSV)",
    csv,
    "livraisons_analysees.csv",
    "text/csv"
)

st.caption(
    "Le statut du retard est basé sur la colonne RETARD du fichier original."
)

