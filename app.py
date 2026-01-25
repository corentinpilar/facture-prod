import streamlit as st
import json
import io
import zipfile
import time
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET TRADUCTION CSS
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] button { display: none !important; }
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "Parcourir les fichiers";
        display: inline-block;
        background-color: #262730; color: white;
        padding: 8px 16px; border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        position: absolute; right: 20px; top: 25px;
    }
    div[data-testid="stFileUploaderDropzone"] section > div > div > span { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "Glissez et déposez vos fichiers ici";
        display: block; font-size: 1.1rem; margin-bottom: 5px;
    }
    div[data-testid="stFileUploaderDropzone"] section > div > div > small { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] section > div > div::after {
        content: "Limite de 200 Mo par fichier • PDF";
        display: block; font-size: 0.8rem; color: #808495;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation de la session
if 'prepret' not in st.session_state: st.session_state.prepret = False

# Fonction pour vider la session
def reset_app():
    for key in ['pdf_data', 'pdf_name', 'prepret']:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

st.markdown("### 🎬 LE FAUX SOIR - Pdf manager")

@st.dialog("Action requise ✍🏻")
def popup_signature(pdf_data, pdf_name):
    st.write(f"Le fichier **{pdf_name}** est prêt.")
    st.warning("Envoyer le document à signer via Dropbox Sign")
    st.download_button(label="⬇️ Télécharger le document", data=pdf_data, file_name=pdf_name, mime="application/pdf")

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("1. Préparer le PDF unique")
    st.markdown("<p style='font-size: 0.9em; color: gray; margin-top: -15px;'>Ajouter les pdfs qui sont placés dans \"OK Laurie\"</p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        
        col_info, col_reset = st.columns([3, 1])
        with col_info:
            st.write(f"**Documents chargés ({len(files)}) :**")
        with col_reset:
            if st.button("🗑️ Vider la liste"): reset_app()
        
        total_pages = 0
        with st.container(border=True):
            for idx, f in enumerate(fichiers_tries, 1):
                try:
                    reader = PdfReader(f)
                    p_count = len(reader.pages)
                    total_pages += p_count
                    st.markdown(f"✅ **{idx}.** {f.name} <span style='color:gray; font-size:0.8em;'>({p_count} p.)</span>", unsafe_allow_html=True)
                except:
                    st.error(f"❌ {f.name} n'est pas un PDF valide.")
        
        st.info(f"📊 Total estimé : **{total_pages} pages**")
        
        if st.button("🚀 Générer la fusion"):
            progress_bar = st.progress(0, text="Lecture des fichiers...")
            writer = PdfWriter()
            carte = []
            
            for i, f in enumerate(fichiers_tries):
                reader = PdfReader(f)
                writer.append(f)
                carte.append({"n": f.name, "p": len(reader.pages)})
                progress_bar.progress((i + 1) / len(fichiers_tries), text=f"Fusion de {f.name}...")
            
            metadata = {"/StructureProd": json.dumps(carte)}
            writer.add_metadata(metadata)
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            
            ts = datetime.now().strftime("%d-%m-%Y - %Hh%M")
            st.session_state.pdf_name = f"LFS - à signer - {ts}.pdf"
            st.session_state.pdf_data = pdf_out.getvalue()
            st.session_state.prepret = True
            progress_bar.empty()
            st.success("Fusion réussie !")

    if st.session_state.prepret:
        if st.button("✅ Terminer et télécharger"):
            popup_signature(st.session_state.pdf_data, st.session_state.pdf_name)

# --- ONGLET 2 : DECOUPAGE ---
with tab2:
    st.header("2. Extraire les pièces signées")
    st.markdown("<p style='font-size: 0.9em; color: gray; margin-top: -15px;'>Déposer le pdf global signé. <br>Les pdfs signés seront prêts à être encodés.</p>", unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        st.markdown(f"✅ **Fichier prêt :** {pdf_signe.name}")
        
        if st.button("⚡ Extraire les factures"):
            try:
                bar_extract = st.progress(0, text="Analyse du fichier signé...")
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
                        for i, item in enumerate(carte):
                            sw = PdfWriter()
                            for p in range(current_page, current_page + item["p"]):
                                sw.add_page(reader.pages[p])
                            sw.add_page(last_page)
                            current_page += item["p"]
                            buf = io.BytesIO()
                            sw.write(buf)
                            zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                            bar_extract.progress((i + 1) / len(carte), text=f"Extraction de {item['n']}...")
                    
                    bar_extract.empty()
                    st.success("✅ Extraction terminée ✍🏻")
                    st.download_button(label="⬇️ Télécharger l'archive ZIP", data=zip_out.getvalue(), file_name=f"LFS - à encoder - {ts_now}.zip")
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 0.8em;'>© Tous droits réservés - Corentin Pilarczyk</div>", unsafe_allow_html=True)
