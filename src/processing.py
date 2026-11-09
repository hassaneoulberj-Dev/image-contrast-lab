"""Contrast experiments on 8-bit grayscale images; no trained model."""
import csv
import io
import json
import zipfile

import cv2
import numpy as np
from matplotlib.figure import Figure
from skimage.metrics import structural_similarity


def validate(image):
    if image is None or image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError('Une image en niveaux de gris 8 bits est nécessaire.')
    if min(image.shape) < 3 or image.size > 12_000_000:
        raise ValueError('Dimensions acceptées : au moins 3 × 3 et au plus 12 millions de pixels.')


def decode(data):
    if not data or len(data) > 20 * 1024 * 1024:
        raise ValueError('Fichier vide ou supérieur à 20 Mo.')
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError('Le fichier ne peut pas être lu comme une image.')
    if image.dtype != np.uint8:
        raise ValueError('Les images 16 bits ne sont pas prises en charge. Fournissez un aperçu 8 bits.')
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY)
    validate(image)
    return image


def demo_image():
    y, x = np.mgrid[:256, :256]
    image = 75 + 35 * x / 255 + 15 * np.sin(y / 15)
    image[(x - 130)**2 + (y - 130)**2 < 65**2] += 25
    image[50:95, 30:110] -= 20
    return np.clip(image, 0, 255).astype(np.uint8)


def suggest(image):
    contrast = np.std(image)
    return (4.0, 12) if contrast < 30 else ((2.0, 8) if contrast < 50 else (1.2, 4))


def process(image, clip=2.0, grid=8, gamma=1.0):
    validate(image)
    if not 0.1 <= clip <= 10 or not 2 <= grid <= 32 or not 0.1 <= gamma <= 5:
        raise ValueError('Paramètres hors limites.')
    low, high = np.percentile(image, [2, 98])
    stretched = image.copy() if high <= low else np.clip((image.astype(float)-low)*255/(high-low), 0, 255).astype(np.uint8)
    lut = np.rint(255 * (np.arange(256) / 255)**gamma).astype(np.uint8)
    return {'Original': image, 'HE': cv2.equalizeHist(image),
            'CLAHE': cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid)).apply(image),
            'Gamma': cv2.LUT(image, lut), 'Etirement': stretched}


def metrics(reference, image):
    validate(reference)
    validate(image)
    if reference.shape != image.shape:
        raise ValueError('Les dimensions doivent être identiques.')
    mse = float(np.mean((reference.astype(np.float64)-image.astype(np.float64))**2))
    win = min(7, *image.shape)
    win -= 1 if win % 2 == 0 else 0
    p = np.bincount(image.ravel(), minlength=256) / image.size
    p = p[p > 0]
    return {'MSE': mse, 'PSNR_dB': float(10*np.log10(255**2/mse)) if mse else float('inf'),
            'SSIM': float(structural_similarity(reference, image, data_range=255, win_size=win)),
            'Ecart_type': float(np.std(image)), 'Entropie_bits': float(-np.sum(p*np.log2(p)))}


def comparison(images):
    fig = Figure(figsize=(15, 4), layout='constrained')
    for ax, (name, image) in zip(fig.subplots(1, len(images)), images.items()):
        ax.imshow(image, cmap='gray', vmin=0, vmax=255)
        ax.set_title(name)
        ax.axis('off')
    return fig


def histogram(images):
    fig = Figure(figsize=(10, 4), layout='constrained')
    ax = fig.subplots()
    for name, image in images.items():
        ax.plot(np.bincount(image.ravel(), minlength=256)/image.size, label=name)
    ax.set(xlabel='Intensité (0–255)', ylabel='Fréquence', xlim=(0, 255))
    ax.legend()
    return fig


def figure_bytes(fig):
    output = io.BytesIO()
    fig.savefig(output, format='png', dpi=140)
    return output.getvalue()


def export(images, parameters):
    output = io.BytesIO()
    rows = [{'Methode': name, **metrics(images['Original'], image)} for name, image in images.items()]
    csv_buffer = io.StringIO(newline='')
    writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, image in images.items():
            success, encoded = cv2.imencode('.png', image)
            if not success:
                raise ValueError("Échec de l'export PNG.")
            archive.writestr(f'{name}.png', encoded.tobytes())
        archive.writestr('comparaison.png', figure_bytes(comparison(images)))
        archive.writestr('histogrammes.png', figure_bytes(histogram(images)))
        archive.writestr('metriques.csv', csv_buffer.getvalue().encode('utf-8-sig'))
        archive.writestr('parametres.json', json.dumps(parameters, indent=2, ensure_ascii=False))
    return output.getvalue()
