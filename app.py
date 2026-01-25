import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# Configuration de la page
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

# Titre
st.markdown("### 🎬 LE FAUX SOIR - Pdf manager")

# Fonction pour la fenêtre Pop-up (Dialog)
@st.dialog("Action requise ✍🏻")
def popup_signature(pdf_data, pdf_name):
    st.write(f"Le fichier **{pdf_name}** est prêt.")
    st.warning("Envoyer le document à signer via Dropbox Sign")
    
    st.download_button(
        label="⬇️ Télécharger le document",
        data=pdf_data,
        file_name=pdf_name,
        mime="application/pdf"
    )
    st.caption("Une fois le téléchargement lancé, vous pouvez fermer cette fenêtre.")

# Initialisation des variables de session
if 'prepret' not in st.session_state:
    st.session_state.prepret = False

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("1. Préparer le PDF unique")
    
    # On utilise label_visibility pour épurer
    files = st.file_uploader("Glissez les PDF à combiner", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        # On force l'affichage de tous les fichiers dans une zone dédiée sans pagination
        st.write(f"**Documents chargés ({len(files)}) :**")
        
        fichiers_tries = sorted(files, key=lambda x: x.name)
        
        # Création d'une zone délimitée pour la liste
        with st.container(border=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"**{idx}.** {f.name}")
        
        if st.button("🚀 Générer la fusion"):
            writer = PdfWriter()
            carte = []
            
            for f in fichiers_tries:
                reader = PdfReader(f)
                writer.append(f)
                n_pages = len(reader.pages)
                carte.append({"n": f.name, "p": n_pages})
            
            metadata = {"/StructureProd": json.dumps(carte)}
            writer.add_metadata(metadata)
            
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            
            ts = datetime.now().strftime("%d-%m-%Y - %Hh%M")
            st.session_state.pdf_name = f"LFS - à signer - {ts}.pdf"
            st.session_state.pdf_data = pdf_out.getvalue()
            st.session_state.prepret = True
            st.success("Fusion réussie !")

    if st.session_state.prepret:
        if st.button("✅ Terminer et télécharger"):
            popup_signature(st.session_state.pdf_data, st.session_state.pdf_name)

# --- ONGLET 2 : DECOUPAGE ---
with tab2:
    st.header("2. Extraire les pièces signées")
    pdf_signe = st.file_uploader("Déposez le PDF signé ici", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        if st.button("⚡ Extraire les factures"):
            try:
                reader = PdfReader(pdf_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne contient pas les données de structure.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1]
                    
                    zip_out = io.BytesIO()
                    current_page = 0
                    ts_now = datetime.now().strftime("%d-%m-%Y - %Hh%M")
                    
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for item in carte:
                            sw = PdfWriter()
                            nb_pages = item["p"]
                            nom_origine = item["n"]
                            for i in range(current_page, current_page + nb_pages):
                                sw.add_page(reader.pages[i])
                            sw.add_page(last_page)
                            current_page += nb_pages
                            buf = io.BytesIO()
                            sw.write(buf)
                            zf.writestr(nom_origine.replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    st.success("✅ Extraction terminée ✍🏻")
                    st.download_button(
                        label="⬇️ Télécharger l'archive ZIP", 
                        data=zip_out.getvalue(), 
                        file_name=f"LFS - à encoder - {ts_now}.zip"
                    )
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- PIED DE PAGE ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.8em;'>"
    "© Tous droits réservés - Corentin Pilarczyk"
    "</div>", 
    unsafe_allow_html=True
)
