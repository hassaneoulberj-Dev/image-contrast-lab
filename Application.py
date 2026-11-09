from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import pandas as pd
import streamlit as st
from src.processing import demo_image, decode, suggest, process, metrics, comparison, histogram, export

st.set_page_config(page_title='Image Contrast Lab', page_icon='🔬', layout='wide')
st.title('Image Contrast Lab')
st.caption('Comparer, mesurer et exporter cinq vues d’une même image.')
st.info('Projet pédagogique de traitement d’image. Les métriques mesurent les différences avec l’original ; elles ne constituent pas une validation diagnostique.')
source = st.sidebar.radio('Image à analyser', ['Démonstration synthétique', 'Importer une image'])
if source == 'Importer une image':
    uploaded = st.sidebar.file_uploader('Image PNG ou JPEG (8 bits)', type=['png', 'jpg', 'jpeg'])
    if uploaded is None:
        st.info('Choisissez une image dans le panneau à gauche.')
        st.stop()
    try:
        original = decode(uploaded.getvalue())
    except ValueError as error:
        st.error(str(error))
        st.stop()
else:
    original = demo_image()

auto_clip, auto_grid = suggest(original)
automatic = st.sidebar.checkbox('Réglage CLAHE automatique', value=True)
st.sidebar.caption('Heuristique fondée sur l’écart-type, sans apprentissage automatique.')
clip = st.sidebar.slider('Limite de contraste CLAHE', 0.5, 5.0, 2.0, 0.1, disabled=automatic)
grid = st.sidebar.slider('Grille CLAHE', 2, 16, 8, disabled=automatic)
if automatic:
    clip, grid = auto_clip, auto_grid
st.sidebar.caption(f'CLAHE appliqué : limite {clip}, grille {grid} × {grid}')
gamma = st.sidebar.slider('Gamma', 0.2, 3.0, 0.8, 0.1)
st.sidebar.caption('Gamma < 1 éclaircit ; gamma > 1 assombrit.')
images = process(original, clip, grid, gamma)
parameters = dict(clip=clip, grid=grid, gamma=gamma, mode='automatique' if automatic else 'manuel', dimensions=list(original.shape))

tab_images, tab_metrics, tab_export = st.tabs(['Comparaison', 'Métriques et histogrammes', 'Téléchargements'])
with tab_images:
    st.pyplot(comparison(images))
    selected = st.selectbox('Afficher en grand', list(images), index=2)
    left, right = st.columns(2)
    left.image(original, caption='Original', width='stretch')
    right.image(images[selected], caption=selected, width='stretch')
with tab_metrics:
    st.dataframe(pd.DataFrame([{'Méthode': name, **metrics(original, image)} for name, image in images.items()]).set_index('Méthode'), width='stretch')
    st.caption('MSE, PSNR et SSIM : similarité avec l’original, pas classement de qualité. PSNR infini pour des images identiques. Écart-type et entropie décrivent la distribution des intensités.')
    st.pyplot(histogram(images))
with tab_export:
    success, encoded = cv2.imencode('.png', images[selected])
    if success:
        st.download_button('Télécharger l’image sélectionnée', encoded.tobytes(), f'{selected}.png', 'image/png')
    st.download_button('Télécharger tous les résultats (ZIP)', export(images, parameters), 'resultats-image-lab.zip', 'application/zip')
    st.caption('Le ZIP contient les 5 images, 2 graphiques, les métriques CSV et les paramètres JSON.')
