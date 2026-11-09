# Vérification du 8 novembre 2026

- Cinq tests automatiques réussis : différence maximale entre pixels (MSE 65025), identité et SSIM sur image 3 × 3, image constante et gamma neutre, rejet d’entrée invalide/16 bits, lecture des PNG exportés et contenu du ZIP.
- Interface vérifiée avec Streamlit AppTest : démonstration initiale, passage aux réglages manuels, changement gamma et import sans fichier.
- Comparaison PNG générée et inspectée visuellement.
- Les tests d’interface sont simulés ; aucune validation dans un navigateur réel ni validation clinique n’a été effectuée.
- Les PDF et images d’origine sont archivés séparément, sans modification. Leur contenu n’a pas été examiné.
- Aucun modèle d’IA n’est entraîné : les méthodes sont déterministes et le réglage automatique de CLAHE est heuristique.
- Un environnement vierge avec toutes les combinaisons des versions autorisées n’a pas été testé.
