import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# Configuration de la page
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

# Style CSS pour masquer la liste native de Streamlit qui crée la pagination
st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# Titre
st.markdown("### 🎬 LE FAUX SOIR - Pdf manager")

# Fenêtre Pop-up
@st.dialog("Action requise ✍🏻")
def popup_signature(pdf_data, pdf_name):
    st.write(f"Le fichier **{pdf_name}** est prêt.")
    st.warning("Envoyer le document à signer via Dropbox Sign")
    st.download_button(label="⬇️ Télécharger le document", data=pdf_data, file_name=pdf_name, mime="application/pdf")
    st.caption("Une fois le téléchargement lancé, vous pouvez fermer cette fenêtre.")

if 'prepret' not in st.session_state:
    st.session_state.prepret = False

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("1. Préparer le PDF unique")
    
    # Uploader sans label pour gagner de la place
    files = st.file_uploader("Upload", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        
        # Affichage de TA liste complète sans aucune pagination
        st.write(f"**Documents prêts pour la fusion ({len(files)}) :**")
        
        # On utilise un container avec bordure pour bien voir la liste
        with st.container(border=True):
            for idx, f in enumerate(fichiers_tries, 1):
                # Calcul de la taille en KB pour l'info
                taille = f.size / 1024
                st.markdown(f"**{idx}.** {f.name} <span style='color:gray; font-size:0.8em;'>({taille:.1f} KB)</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button("🚀 Générer la fusion"):
            writer = PdfWriter()
            carte = []
            for f in fichiers_tries:
                reader = PdfReader(f)
                writer.append(f)
                carte.append({"n": f.name, "p": len(reader.pages)})
            
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
    pdf_signe = st.file_uploader("Signé", type="pdf", label_visibility="collapsed")
    
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
                    ts_now = datetime.now().strftime("%d-%m-%Y - %Hh%M")
                    
                    current_page = 0
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for item in carte:
                            sw = PdfWriter()
                            for i in range(current_page, current_page + item["p"]):
                                sw.add_page(reader.pages[i])
                            sw.add_page(last_page)
                            current_page += item["p"]
                            buf = io.BytesIO()
                            sw.write(buf)
                            zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    st.success("✅ Extraction terminée ✍🏻")
                    st.download_button(label="⬇️ Télécharger l'archive ZIP", data=zip_out.getvalue(), file_name=f"LFS - à encoder - {ts_now}.zip")
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 0.8em;'>© Tous droits réservés - Corentin Pilarczyk</div>", unsafe_allow_html=True)
