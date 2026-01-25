import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN PREMIUM
st.set_page_config(page_title="LE FAUX SOIR - Admin", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* Masquer les éléments techniques anglais */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] button { display: none !important; }
    
    /* Bouton Parcourir personnalisé */
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "📁 Parcourir les fichiers";
        display: inline-block;
        background-color: #FF4B4B;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        position: absolute; right: 20px; top: 20px;
        font-weight: bold;
    }

    /* Texte de la zone de dépôt */
    div[data-testid="stFileUploaderDropzone"] section > div > div > span { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "🎬 Déposez les éléments de production ici";
        display: block; font-size: 1.2rem; font-weight: bold; color: #FAFAFA;
    }
    
    /* Sous-titre zone de dépôt */
    div[data-testid="stFileUploaderDropzone"] section > div > div > small { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] section > div > div::after {
        content: "Documents PDF uniquement • Max 200 Mo";
        display: block; font-size: 0.85rem; color: #808495; margin-top: 5px;
    }

    /* Style des onglets */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation de la session
if 'prepret' not in st.session_state: st.session_state.prepret = False

def reset_app():
    for key in ['pdf_data', 'pdf_name', 'prepret']:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

# --- HEADER ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire de Production</p>", unsafe_allow_html=True)

@st.dialog("Action requise ✍🏻")
def popup_signature(pdf_data, pdf_name):
    st.markdown(f"### 📄 Document prêt")
    st.write(f"Nom : `{pdf_name}`")
    st.warning("Étape suivante : Envoyer le document via **Dropbox Sign**")
    st.download_button(label="⬇️ Télécharger maintenant", data=pdf_data, file_name=pdf_name, mime="application/pdf", use_container_width=True)

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.subheader("1. Préparer le pdf global pour signature.")
    st.markdown("<p style='color: gray;'>Fichiers sources : dossier <b>\"OK Laurie\"</b></p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        
        # Statistiques visuelles
        st.markdown("---")
        m1, m2 = st.columns(2)
        total_p = 0
        for f in fichiers_tries:
            try: total_p += len(PdfReader(f).pages)
            except: pass
        
        m1.metric("Documents", len(files))
        m2.metric("Total Pages", total_p)

        # Liste rétractable
        with st.expander("👁️ Voir le détail des fichiers chargés", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 GÉNÉRER LA FUSION", use_container_width=True, type="primary"):
                with st.spinner("Traitement en cours..."):
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
                    st.success("Fusion terminée avec succès !")
        
        with col_btn2:
            if st.button("🗑️ VIDER LA LISTE", use_container_width=True):
                reset_app()

    if st.session_state.prepret:
        st.divider()
        if st.button("📥 RÉCUPÉRER LE PDF FINAL", use_container_width=True):
            popup_signature(st.session_state.pdf_data, st.session_state.pdf_name)

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraction des pdfs.")
    st.markdown("""
        <p style='color: gray; font-size: 0.95em;'>
        Déposez le PDF global signé par la direction de production/post-production.<br>
        Les fichiers seront séparés et prêts pour l'encodage.
        </p>
        """, unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        st.success(f"📄 Fichier signé détecté : {pdf_signe.name}")
        
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                with st.spinner("Découpage en cours..."):
                    reader = PdfReader(pdf_signe)
                    if "/StructureProd" not in reader.metadata:
                        st.error("Structure manquante dans le PDF.")
                    else:
                        carte = json.loads(reader.metadata["/StructureProd"])
                        last_page = reader.pages[-1]
                        zip_out = io.BytesIO()
                        ts_now = datetime.now().strftime("%d-%m-%Y - %Hh%M")
                        
                        current_page = 0
                        with zipfile.ZipFile(zip_out, "w") as zf:
                            for item in carte:
                                sw = PdfWriter()
                                for p in range(current_page, current_page + item["p"]):
                                    sw.add_page(reader.pages[p])
                                sw.add_page(last_page)
                                current_page += item["p"]
                                buf = io.BytesIO()
                                sw.write(buf)
                                zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                        
                        st.balloons()
                        st.download_button(label="⬇️ TÉLÉCHARGER LE PACK ZIP (Signé)", 
                                         data=zip_out.getvalue(), 
                                         file_name=f"LFS - à encoder - {ts_now}.zip",
                                         use_container_width=True)
            except Exception as e:
                st.error(f"Erreur technique : {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em; font-weight: bold;'>"
            "🎬 LE FAUX SOIR - PRODUCTION<br>"
            "© Tous droits réservés - Corentin Pilarczyk</div>", unsafe_allow_html=True)
