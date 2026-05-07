
import cv2
import numpy as np
from scipy.fftpack import dct, idct
import matplotlib.pyplot as plt
from skimage.metrics import peak_signal_noise_ratio as psnr
import os

# ============================================================================
# 1. TRANSFORMATION FRÉQUENTIELLE (DCT 2D)
# ============================================================================

def dct2(image):
    """
    Transformation DCT 2D sur l'image
    Utilisée pour passer dans le domaine fréquentiel
    """
    return dct(dct(image.T, norm='ortho').T, norm='ortho')

def idct2(image_dct):
    """
    Transformation DCT inverse 2D
    Retour dans le domaine spatial
    """
    return idct(idct(image_dct.T, norm='ortho').T, norm='ortho')

# ============================================================================
# 2.Generation du watermark binaire 
# ============================================================================

def generer_watermark(taille, graine=42):

    np.random.seed(graine)
    watermark = np.random.randint(0, 2, taille)
    return watermark

# ============================================================================
# 3. Insertion du watermark par QIM
# ============================================================================

def inserer_watermark_qim(image_dct, watermark, delta=10, cle_secrete=123):

    image_watermark = image_dct.copy()
    hauteur, largeur = image_watermark.shape
    
    # Sélection pseudo-aléatoire des coefficients via clé secrète
    np.random.seed(cle_secrete)
    indices = []
    
    # sélectionner les coefficients de moyenne fréquence
    # Éviter les basses fréquences (zone 0-5) et les très hautes fréquences
    debut = 5
    fin_hauteur = hauteur // 2
    fin_largeur = largeur // 2
    
    for i in range(debut, fin_hauteur):
        for j in range(debut, fin_largeur):
            indices.append((i, j))
    
    np.random.shuffle(indices)
    
    # Insertion de chaque bit du watermark par quantification
    for k, bit in enumerate(watermark):
        if k >= len(indices):
            break
        
        i, j = indices[k]
        coefficient = image_watermark[i, j]
        
        # Quantification selon la méthode QIM
        if bit == 0:
            # Quantifier sur un multiple entier de delta
            image_watermark[i, j] = delta * round(coefficient / delta)
        else:
            # Quantifier sur un demi-multiple de delta
            image_watermark[i, j] = delta * (round(coefficient / delta) + 0.5)
    
    return image_watermark

# ============================================================================
# 4. Extraction du watermark
# ============================================================================

def extraire_watermark_qim(image_dct, taille_watermark, delta=10, cle_secrete=123):

    hauteur, largeur = image_dct.shape
    watermark_extrait = []
    
    # Sélection pseudo-aléatoire des coefficients (identique à l'insertion)
    np.random.seed(cle_secrete)
    indices = []
    
    debut = 5
    fin_hauteur = hauteur // 2
    fin_largeur = largeur // 2
    
    for i in range(debut, fin_hauteur):
        for j in range(debut, fin_largeur):
            indices.append((i, j))
    
    np.random.shuffle(indices)
    
    # Extraction des bits par démodulation QIM
    for k in range(taille_watermark):
        i, j = indices[k]
        coefficient = image_dct[i, j]
        
        # Détermination du bit en fonction du reste modulo delta
        reste = coefficient % delta
        if reste < delta / 2:
            watermark_extrait.append(0)
        else:
            watermark_extrait.append(1)
    
    return watermark_extrait

# ============================================================================
# 5. ATTAQUES (BRUIT ET JPEG)
# ============================================================================

def attaque_bruit_gaussien(image, force=5):
    """
    Attaque : Ajout de bruit gaussien
    Simule les dégradations naturelles ou malveillantes
    """
    bruit = np.random.normal(0, force, image.shape)
    image_bruitee = image + bruit
    return np.clip(image_bruitee, 0, 255)

def attaque_compression_jpeg(image, qualite=70):
    """
    Attaque : Compression JPEG
    Teste la robustesse face à la compression courante
    """
    image_uint8 = np.uint8(np.clip(image, 0, 255))
    _, image_encodee = cv2.imencode('.jpg', image_uint8, 
                                     [cv2.IMWRITE_JPEG_QUALITY, qualite])
    image_decodee = cv2.imdecode(image_encodee, 0)
    return np.float32(image_decodee)

# ============================================================================
# 6.  Metriques d'évaluation
# ============================================================================

def calculer_psnr(image_originale, image_modifiee):
    """
    Calcul du PSNR (Peak Signal-to-Noise Ratio)
    Mesure la qualité visuelle / l'invisibilité du watermark
    """
    return psnr(image_originale, image_modifiee, data_range=255)

def calculer_ber(watermark_original, watermark_extrait):
    """
    Calcul du BER (Bit Error Rate)
    Mesure la robustesse du watermark
    """
    if len(watermark_original) != len(watermark_extrait):
        return 1.0
    
    erreurs = sum(o != e for o, e in zip(watermark_original, watermark_extrait))
    return erreurs / len(watermark_original)

# ============================================================================
# 7. Changement et sauvengarde des images 
# ============================================================================

def charger_image(chemin):
    """
    Charge une image en niveaux de gris
    """
    image = cv2.imread(chemin, 0)
    if image is None:
        return None
    return np.float32(image)

def sauvegarder_image(chemin, image):
    """
    Sauvegarde une image
    """
    cv2.imwrite(chemin, np.uint8(np.clip(image, 0, 255)))

# ============================================================================
# 8. PROGRAMME PRINCIPAL
# ============================================================================

def main():
    print("=" * 70)
    print("MINI-PROJET : SÉCURISATION DES IMAGES 2D PAR TATOUAGE NUMÉRIQUE")
    print("Méthode : Quantification Index Modulation (QIM) + DCT 2D")
    print("=" * 70)
    
    # ------------------------------------------------------------------------
    # ÉTAPE 1 : Chargement de l'image hôte
    # ------------------------------------------------------------------------
    print("\n[1] Chargement de l'image hôte")
    chemin_image = input("Entrez le nom du fichier image (ex: image.jpg) : ")
    
    if not os.path.exists(chemin_image):
        print(f"ERREUR : L'image '{chemin_image}' est introuvable !")
        return
    
    image_hote = charger_image(chemin_image)
    print(f" Image chargée : {image_hote.shape[1]}x{image_hote.shape[0]} pixels")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 2 : Génération du watermark binaire
    # ------------------------------------------------------------------------
    print("\n[2] Génération du watermark binaire")
    taille_watermark = 100
    watermark_original = generer_watermark(taille_watermark)
    print(f" Watermark généré : {taille_watermark} bits")
    print(f"  Premiers bits : {watermark_original[:20]}")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 3 : Transformation fréquentielle (DCT 2D)
    # ------------------------------------------------------------------------
    print("\n[3] Transformation DCT 2D")
    image_dct = dct2(image_hote)
    print(" Passage dans le domaine fréquentiel DCT")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 4 : Insertion du watermark par QIM
    # ------------------------------------------------------------------------
    print("\n[4] Insertion du watermark par QIM")
    delta = 10          # Pas de quantification
    cle_secrete = 123   # Clé pour sélection pseudo-aléatoire
    
    image_dct_watermark = inserer_watermark_qim(image_dct, watermark_original, 
                                                 delta, cle_secrete)
    print(" Watermark inséré dans les coefficients de moyenne fréquence")
    print(f"  Pas de quantification (Δ) = {delta}")
    print(f"  Clé secrète = {cle_secrete}")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 5 : Reconstruction de l'image tatouée
    # ------------------------------------------------------------------------
    print("\n[5] Reconstruction de l'image tatouée")
    image_tatouee = idct2(image_dct_watermark)
    image_tatouee = np.clip(image_tatouee, 0, 255)
    sauvegarder_image("image_tatouee.jpg", image_tatouee)
    print(" Image tatouée sauvegardée : image_tatouee.jpg")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 6 : Évaluation de la qualité (PSNR)
    # ------------------------------------------------------------------------
    print("\n[6] Évaluation de la qualité visuelle")
    valeur_psnr = calculer_psnr(image_hote, image_tatouee)
    print(f" PSNR = {valeur_psnr:.2f} dB")
    
    if valeur_psnr > 40:
        print("  → Qualité excellente (watermark invisible)")
    elif valeur_psnr > 35:
        print("  → Très bonne qualité")
    else:
        print("  → Qualité acceptable")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 7 : Simulation d'attaques et extraction
    # ------------------------------------------------------------------------
    print("\n[7] Test de robustesse - Simulation d'attaques")
    
    # Test 1 : Bruit gaussien
    print("\n  → Attaque 1 : Ajout de bruit gaussien (force=5)")
    image_bruitee = attaque_bruit_gaussien(image_tatouee, force=5)
    sauvegarder_image("image_bruitee.jpg", image_bruitee)
    
    image_bruitee_dct = dct2(image_bruitee)
    watermark_bruit = extraire_watermark_qim(image_bruitee_dct, taille_watermark, 
                                              delta, cle_secrete)
    ber_bruit = calculer_ber(watermark_original, watermark_bruit)
    print(f"    BER = {ber_bruit:.3f} ({ber_bruit*100:.1f}% d'erreurs)")
    
    # Test 2 : Compression JPEG
    print("\n  → Attaque 2 : Compression JPEG (qualité=70%)")
    image_jpeg = attaque_compression_jpeg(image_tatouee, qualite=70)
    sauvegarder_image("image_jpeg.jpg", image_jpeg)
    
    image_jpeg_dct = dct2(image_jpeg)
    watermark_jpeg = extraire_watermark_qim(image_jpeg_dct, taille_watermark, 
                                             delta, cle_secrete)
    ber_jpeg = calculer_ber(watermark_original, watermark_jpeg)
    print(f"    BER = {ber_jpeg:.3f} ({ber_jpeg*100:.1f}% d'erreurs)")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 8 : Affichage des résultats finaux
    # ------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("RÉSULTATS FINAUX")
    print("=" * 70)
    print(f"Qualité visuelle (PSNR) : {valeur_psnr:.2f} dB")
    print(f"Robustesse bruit (BER)  : {ber_bruit:.3f}")
    print(f"Robustesse JPEG (BER)   : {ber_jpeg:.3f}")
    
    # Interprétation des résultats
    print("\n→ Analyse de robustesse :")
    if ber_jpeg < 0.1:
        print("   Watermark TRÈS ROBUSTE")
    elif ber_jpeg < 0.2:
        print("  ◯ Watermark MOYENNEMENT ROBUSTE")
    else:
        print("  ✗ Watermark FAIBLEMENT ROBUSTE")
    
    # ------------------------------------------------------------------------
    # ÉTAPE 9 : Visualisation des résultats
    # ------------------------------------------------------------------------
    print("\n[9] Affichage des résultats graphiques")
    
    plt.figure(figsize=(14, 8))
    
    # Image originale
    plt.subplot(2, 3, 1)
    plt.imshow(image_hote, cmap='gray')
    plt.title('Image originale', fontsize=12)
    plt.axis('off')
    
    # Image tatouée
    plt.subplot(2, 3, 2)
    plt.imshow(image_tatouee, cmap='gray')
    plt.title(f'Image tatouée\nPSNR = {valeur_psnr:.1f} dB', fontsize=12)
    plt.axis('off')
    
    # Différence (amplifiée)
    difference = np.abs(image_hote - image_tatouee) * 10
    plt.subplot(2, 3, 3)
    plt.imshow(difference, cmap='hot')
    plt.title('Différence (amplifiée x10)', fontsize=12)
    plt.axis('off')
    
    # Image avec bruit
    plt.subplot(2, 3, 4)
    plt.imshow(image_bruitee, cmap='gray')
    plt.title(f'Attaque : Bruit gaussien\nBER = {ber_bruit:.3f}', fontsize=12)
    plt.axis('off')
    
    # Image JPEG
    plt.subplot(2, 3, 5)
    plt.imshow(image_jpeg, cmap='gray')
    plt.title(f'Attaque : JPEG 70%\nBER = {ber_jpeg:.3f}', fontsize=12)
    plt.axis('off')
    
    # Graphique BER
    plt.subplot(2, 3, 6)
    attaques = ['Bruit\ngaussien', 'JPEG\n70%']
    ber_values = [ber_bruit, ber_jpeg]
    couleurs = ['orange', 'red']
    bars = plt.bar(attaques, ber_values, color=couleurs, edgecolor='black')
    plt.ylim(0, max(0.5, max(ber_values) + 0.1))
    plt.ylabel('Taux d\'erreur binaire (BER)', fontsize=10)
    plt.title('Robustesse du watermark', fontsize=12)
    
    # Ajouter les valeurs sur les barres
    for bar, val in zip(bars, ber_values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('resultats_tatouage.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\n Résultats sauvegardés dans : resultats_tatouage.png")
    print("\n" + "=" * 70)
    
 

# ============================================================================
# LANCEMENT DU PROGRAMME
# ============================================================================

if __name__ == "__main__":
    main()