import streamlit as st
import json
import io
import zipfile
import time
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="© Le Faux Soir - PDF Manager", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* Masquer la liste de fichiers par défaut */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    
    /* Bouton personnalisé zone de dépôt */
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "📁 Parcourir les fichiers";
        display: inline-block; background-color: #FF4B4B; color: white;
        padding: 10px 20px; border-radius: 8px; cursor: pointer;
        position: absolute; right: 20px; top: 20px; font-weight: bold;
    }
    
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "🎬 Déposez les documents ici";
        display: block; font-size: 1.2rem; font-weight: bold; color: #FAFAFA;
    }

    /* FIX COULEUR TEXTE SIDEBAR (Compatibilité Thème Clair/Sombre) */
    [data-testid="stSidebar"] .stMarkdown p {
        color: #31333F !important; /* Couleur par défaut lisible */
    }
    
    /* Si l'utilisateur est en thème sombre, on adapte */
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"] .stMarkdown p {
            color: #FAFAFA !important;
        }
    }

    /* Réduction des marges entre les blocs du guide */
    [data-testid="stVerticalBlock"] > div {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation
if 'PDF_data' not in st.session_state: st.session_state.PDF_data = None

# --- BARRE LATÉRALE : GUIDE D'UTILISATION (LISIBILITÉ FORCÉE) ---
with st.sidebar:
    st.title("📖 Guide")
    
    # Étape 1
    with st.container(border=True):
        st.markdown("**🚀 Étape 1 : Préparation**")
        st.markdown("<small>Dossier 'OK Laurie'. Déposez les PDFs, générez et téléchargez le fichier unique.</small>", unsafe_allow_html=True)
    
    # Étape 2
    with st.container(border=True):
        st.markdown("**✍️ Étape 2 : Signature**")
        st.markdown("<small>Utilisez Dropbox Sign Frakas pour faire signer le PDF unique.</small>", unsafe_allow_html=True)
    
    # Étape 3
    with st.container(border=True):
        st.markdown("**📦 Étape 3 : Split & BOB**")
        st.markdown("<small>Onglet EXTRAIRE. Déposez le PDF signé. Le système sépare les factures pour BOB.</small>", unsafe_allow_html=True)
    
    st.markdown(" ")
    st.markdown("<p style='font-size: 0.8em; opacity: 0.7;'>LE FAUX SOIR - FRAKAS PRODUCTIONS</p>", unsafe_allow_html=True)

# --- CONTENU PRINCIPAL ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire des pièces comptables</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["➕ 1. PRÉPARER (Fusion)", "✂️ 2. EXTRAIRE (BOB)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.subheader("1. Fusionner pour signature")
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        with st.expander(f"👁️ Liste des fichiers ({len(files)})", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 GÉNÉRER LE PDF", key="btn_gen", use_container_width=True, type="primary"):
                writer = PdfWriter()
                carte = [{"n": f.name, "p": len(PdfReader(f).pages)} for f in fichiers_tries]
                for f in fichiers_tries: writer.append(f)
                writer.add_metadata({"/StructureProd": json.dumps(carte)})
                PDF_out = io.BytesIO()
                writer.write(PDF_out)
                st.session_state.PDF_data = PDF_out.getvalue()
                st.session_state.PDF_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
                st.success("Fusion réussie !")
        with col2:
            if st.button("🗑️ VIDER TOUT", key="btn_reset", use_container_width=True):
                st.session_state.PDF_data = None
                st.rerun()

    if st.session_state.PDF_data:
        st.download_button("📥 TÉLÉCHARGER LE PDF POUR SIGNATURE", st.session_state.PDF_data, st.session_state.PDF_name, use_container_width=True)

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraire pour encodage BOB")
    PDF_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if PDF_signe:
        if st.button("⚡ LANCER L'EXTRACTION", key="btn_extract", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(PDF_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne provient pas de l'étape 1.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1]
                    zip_out = io.BytesIO()
                    current_page = 0
                    
                    progress_bar = st.progress(0)
                    total_items = len(carte)
                    
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for i, item in enumerate(carte):
                            progress_bar.progress((i + 1) / total_items)
                            sw = PdfWriter()
                            for p in range(current_page, current_page + item["p"]):
                                sw.add_page(reader.pages[p])
                            sw.add_page(last_page)
                            current_page += item["p"]
                            buf = io.BytesIO()
                            sw.write(buf)
                            nom_final = item["n"].lower().replace(".pdf", " (signed).pdf")
                            zf.writestr(nom_final, buf.getvalue())
                            time.sleep(0.05)
                    
                    progress_bar.empty()
                    nom_archive = f"LFS - à encoder - {datetime.now().strftime('%d-%m-%Y_%Hh%M')}.zip"
                    st.success(f"✅ {total_items} documents extraits.")
                    st.download_button(f"⬇️ TÉLÉCHARGER : {nom_archive}", zip_out.getvalue(), nom_archive, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>© Copyright - Corentin Pilarczyk</div>", unsafe_allow_html=True)
