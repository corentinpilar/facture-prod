import streamlit as st
import json
import io
import os
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# Configuration de la page
st.set_page_config(page_title="Gestion PDF Production", page_icon="🎬")

st.title("🎬 PDF Manager - Administration")
st.markdown("---")

# Création des onglets en français
tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("Fusionner les factures pour signature")
    st.info("Utilisez cet onglet pour créer le gros PDF unique à envoyer au DP.")
    
    files = st.file_uploader("Glissez ici vos fichiers PDF à combiner", type="pdf", accept_multiple_files=True)
    
    if files:
        if st.button("🚀 Lancer la fusion"):
            writer = PdfWriter()
            carte = []
            page_cursor = 1
            
            # Tri alphabétique pour garder l'ordre des noms de fichiers
            fichiers_tries = sorted(files, key=lambda x: x.name)
            
            for f in fichiers_tries:
                reader = PdfReader(f)
                writer.append(f)
                n_pages = len(reader.pages)
                carte.append({
                    "nom": f.name, 
                    "debut": page_cursor, 
                    "fin": page_cursor + n_pages - 1
                })
                page_cursor += n_pages
            
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            timestamp = datetime.now().strftime("%d-%m-%Y_%Hh%M")
            
            st.success("✅ Fusion réussie !")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Télécharger le PDF pour signature",
                    data=pdf_out.getvalue(),
                    file_name=f"DOC_A_SIGNER_{timestamp}.pdf",
                    mime="application/pdf"
                )
            with col2:
                st.download_button(
                    label="⬇️ Télécharger le fichier CARTE (JSON)",
                    data=json.dumps(carte, ensure_ascii=False, indent=2),
                    file_name=f"CARTE_{timestamp}.json",
                    mime="application/json"
                )
            st.warning("⚠️ Gardez bien le fichier JSON, il sera indispensable pour le découpage après signature.")

# --- ONGLET 2 : DÉCOUPAGE ---
with tab2:
    st.header("Récupérer les pièces signées")
    st.info("Importez le PDF qui revient de signature et son fichier CARTE associé.")

    col_a, col_b = st.columns(2)
    with col_a:
        pdf_signe = st.file_uploader("Le PDF signé", type="pdf")
    with col_b:
        fichier_json = st.file_uploader("Le fichier CARTE (JSON)", type="json")

    if pdf_signe and fichier_json:
        if st.button("⚡ Extraire et Certifier les pièces"):
            try:
                carte = json.load(fichier_json)
                reader = PdfReader(pdf_signe)
                # On récupère la toute dernière page (Certificat de signature)
                derniere_page = reader.pages[-1]
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for element in carte:
                        sw = PdfWriter()
                        # Extraction des pages de la facture
                        for i in range(element["debut"] - 1, element["fin"]):
                            sw.add_page(reader.pages[i])
                        
                        # Ajout du certificat à la fin de chaque facture
                        sw.add_page(derniere_page)
                        
                        nom_final = element["nom"].replace(".pdf", " (signé).pdf")
                        piece_io = io.BytesIO()
                        sw.write(piece_io)
                        zf.writestr(nom_final, piece_io.getvalue())
                
                st.success("✅ Extraction terminée avec succès !")
                st.download_button(
                    label="⬇️ Télécharger toutes les factures (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="FACTURES_SIGNEES.zip",
                    mime="application/zip"
                )
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")

st.markdown("---")
st.caption("Outil développé pour l'administration de production cinéma.")
