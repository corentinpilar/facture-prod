import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET TRADUCTION FORCEE
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

st.markdown("""
    <style>
    /* Masquer la liste native pour éviter la pagination */
    [data-testid="stFileUploaderFileList"] {
        display: none !important;
    }
    
    /* Ciblage large pour traduire le bouton et le texte de dépôt */
    div[data-testid="stFileUploaderDropzone"] button {
        display: none !important;
    }
    
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "Parcourir les fichiers";
        display: inline-block;
        background-color: #262730;
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: absolute;
        right: 20px;
        top: 25px;
    }

    div[data-testid="stFileUploaderDropzone"] section > div > div > span {
        display: none !important;
    }

    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "Glissez et déposez vos fichiers ici";
        display: block;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 5px;
    }
    
    div[data-testid="stFileUploaderDropzone"] section > div > div > small {
        display: none !important;
    }

    div[data-testid="stFileUploaderDropzone"] section > div > div::after {
        content: "Limite de 200 Mo par fichier • PDF";
        display: block;
        font-size: 0.8rem;
        color: #808495;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("### 🎬 LE FAUX SOIR - Pdf manager")

@st.dialog("Action requise ✍🏻")
def popup_signature(pdf_data, pdf_name):
    st.write(f"Le fichier **{pdf_name}** est prêt.")
    st.warning("Envoyer le document à signer via Dropbox Sign")
    st.download_button(label="⬇️ Télécharger le document", data=pdf_data, file_name=pdf_name, mime="application/pdf")

if 'prepret' not in st.session_state:
    st.session_state.prepret = False

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("1. Préparer le PDF unique pour signature")
    st.markdown("<p style='font-size: 0.9em; color: gray; margin-top: -13px;'>Ajouter les pdfs qui sont placés dans \"OK Laurie\"</p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.write(f"**Documents chargés ({len(files)}) :**")
        
        with st.container(border=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
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
    st.markdown("""
        <p style='font-size: 0.9em; color: gray; margin-top: -15px;'>
        Déposer le pdf global signé par le.la directeur.rice de production ou post-production.
        </p>
        <p style='font-size: 0.9em; color: gray; margin-top: 5px;'>
        Les pdfs signés seront prêts à être encodés.
        </p>
        """, unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        st.markdown(f"✅ **Fichier prêt :** {pdf_signe.name}")
        
        if st.button("⚡ Extraire les factures"):
            try:
                reader = PdfReader(pdf_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Ce PDF ne contient pas les données de structure.")
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
