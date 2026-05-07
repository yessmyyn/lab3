# ===============================
# MINI-PROJET : SÉCURISATION DES IMAGES PAR TATOUAGE NUMÉRIQUE (QIM)
# Étapes : DCT 2D, insertion watermark, extraction, test robustesse
# ===============================

import cv2
import numpy as np
from scipy.fftpack import dct, idct
import matplotlib.pyplot as plt
from skimage.metrics import peak_signal_noise_ratio as psnr

# ===============================
# 1. FONCTIONS DCT 2D
# ===============================
def dct2(img):
    """DCT 2D"""
    return dct(dct(img.T, norm='ortho').T, norm='ortho')

def idct2(img):
    """Inverse DCT 2D"""
    return idct(idct(img.T, norm='ortho').T, norm='ortho')

# ===============================
# 2. INSÉRER WATERMARK
# ===============================
def inserer_watermark(dct_img, watermark, delta=10, cle=123):
    """Insertion watermark binaire via QIM"""
    copie = dct_img.copy()
    h, w = copie.shape

    # Création indices pseudo-aléatoires
    np.random.seed(cle)
    indices = []
    for i in range(5, h//2):
        for j in range(5, w//2):
            indices.append((i,j))
    np.random.shuffle(indices)

    # Ajouter les bits du watermark
    for k in range(len(watermark)):
        i, j = indices[k]
        val = copie[i,j]
        if watermark[k] == 0:
            copie[i,j] = delta * round(val / delta)
        else:
            copie[i,j] = delta * (round(val / delta) + 0.5)
    return copie

# ===============================
# 3. EXTRAIRE WATERMARK
# ===============================
def extraire_watermark(dct_img, taille=100, delta=10, cle=123):
    """Extraction watermark depuis DCT"""
    h, w = dct_img.shape
    bits = []

    # Création indices pseudo-aléatoires
    np.random.seed(cle)
    indices = []
    for i in range(5, h//2):
        for j in range(5, w//2):
            indices.append((i,j))
    np.random.shuffle(indices)

    # Extraire les bits
    for k in range(taille):
        i, j = indices[k]
        reste = dct_img[i, j] % delta
        if reste < delta/2:
            bits.append(0)
        else:
            bits.append(1)
    return bits

# ===============================
# 4. ATTAQUES (BRUIT ET JPEG)
# ===============================
def ajouter_bruit(img, force=5):
    """Ajouter bruit gaussien"""
    bruit = np.random.normal(0, force, img.shape)
    return np.clip(img + bruit, 0, 255)

def compresser_jpeg(img, qualite=70):
    """Compression JPEG"""
    # Convertir en uint8 pour la compression JPEG
    img_uint8 = np.uint8(np.clip(img, 0, 255))
    _, enc = cv2.imencode('.jpg', img_uint8, [cv2.IMWRITE_JPEG_QUALITY, qualite])
    return np.float32(cv2.imdecode(enc, 0))

# ===============================
# 5. CALCULER BER
# ===============================
def calculer_ber(original, extrait):
    """Taux d'erreur binaire"""
    erreurs = 0
    i = 0
    while i < len(original):
        if original[i] != extrait[i]:
            erreurs = erreurs + 1
        i = i + 1
    return erreurs / len(original)

# ===============================
# 6. PROGRAMME PRINCIPAL
# ===============================
def main():
    print("=== MINI-PROJET : TATOUAGE NUMÉRIQUE QIM ===")

    # Charger image
    img_path = input("Nom de l'image (ex: image.jpg) : ")
    img = cv2.imread(img_path, 0)
    if img is None:
        print("Image introuvable !")
        return
    img = np.float32(img)
    print(" Image chargée : " + str(img.shape[0]) + "x" + str(img.shape[1]) + " pixels")

    # Générer watermark binaire
    taille_watermark = 100
    watermark = np.random.randint(0, 2, taille_watermark)
    print(" Watermark généré : " + str(taille_watermark) + " bits")

    # Vérifier que l'image est assez grande pour le watermark
    if img.shape[0] < 10 or img.shape[1] < 10:
        print("Image trop petite pour l'insertion du watermark !")
        return

    # DCT de l'image
    dct_img = dct2(img)

    # Insérer  avec methode QIM (Quantization Index Modulation)
    delta = 10
    cle = 123
    dct_watermark = inserer_watermark(dct_img, watermark, delta, cle)

    # Reconstruire image tatouée
    img_tatouee = idct2(dct_watermark)
    i = 0
    while i < img_tatouee.shape[0]:
        j = 0
        while j < img_tatouee.shape[1]:
            if img_tatouee[i,j] < 0:
                img_tatouee[i,j] = 0
            elif img_tatouee[i,j] > 255:
                img_tatouee[i,j] = 255
            j = j + 1
        i = i + 1

    cv2.imwrite("image_tatouee.jpg", np.uint8(img_tatouee))
    print(" Image tatouée sauvegardée : image_tatouee.jpg")

    # Évaluer PSNR - Correction : spécifier data_range manuellement
    qualite = psnr(img, img_tatouee, data_range=255)
    print("PSNR image tatouée : " + str(round(qualite, 2)) + " dB")

    # Tester robustesse : bruit
    img_bruit = ajouter_bruit(img_tatouee, force=5)
    dct_bruit = dct2(img_bruit)
    extrait_bruit = extraire_watermark(dct_bruit, taille_watermark, delta, cle)
    ber_bruit = calculer_ber(watermark, extrait_bruit)

    # Tester robustesse : JPEG
    img_jpeg = compresser_jpeg(img_tatouee, qualite=70)
    dct_jpeg = dct2(img_jpeg)
    extrait_jpeg = extraire_watermark(dct_jpeg, taille_watermark, delta, cle)
    ber_jpeg = calculer_ber(watermark, extrait_jpeg)

    # Résumé
    print("\n=== RÉSULTATS ===")
    print("BER après bruit (force=5) : " + str(round(ber_bruit, 3)))
    print("BER après JPEG70 : " + str(round(ber_jpeg, 3)))

    if ber_jpeg < 0.1:
        print("Watermark ROBUSTE")
    elif ber_jpeg < 0.2:
        print("Watermark MOYENNEMENT ROBUSTE")
    else:
        print("Watermark PEU ROBUSTE")

    # Affichage images
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 4, 1)
    plt.imshow(img, cmap='gray')
    plt.title("Originale")
    plt.axis('off')
    
    plt.subplot(1, 4, 2)
    plt.imshow(img_tatouee, cmap='gray')
    plt.title("Tatouee\nPSNR=" + str(round(qualite, 1)) + "dB")
    plt.axis('off')
    
    plt.subplot(1, 4, 3)
    plt.imshow(img_bruit, cmap='gray')
    plt.title("Avec bruit\nBER=" + str(round(ber_bruit, 3)))
    plt.axis('off')
    
    plt.subplot(1, 4, 4)
    plt.imshow(img_jpeg, cmap='gray')
    plt.title("JPEG\nBER=" + str(round(ber_jpeg, 3)))
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()

# ===============================
# Lancer le programme
# ===============================
if __name__ == "__main__":
    main()
 