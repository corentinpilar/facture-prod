import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# --- 1. CONFIGURATION ET DESIGN ---
st.set_page_config(page_title="LE FAUX SOIR - Production", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "📁 Parcourir les fichiers";
        display: inline-block; background-color: #FF4B4B; color: white;
        padding: 10px 20px; border-radius: 8px; font-weight: bold;
    }
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "🎬 Déposez les documents ici";
        display: block; font-size: 1.2rem; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
if 'pdf_name' not in st.session_state: st.session_state.pdf_name = ""

# --- HEADER ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire de Production</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["➕ 1. FUSIONNER", "✍️ 2. SIGNER (Lien Direct)", "✂️ 3. EXTRAIRE (BOB)"])

# --- ÉTAPE 1 : FUSION ---
with tab1:
    st.subheader("1. Préparer le document global")
    st.markdown("<p style='color: gray; margin-top:-15px;'>Ajouter les pdfs qui sont placés dans \"OK Laurie\"</p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        
        with st.expander(f"👁️ Liste des {len(files)} documents", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        if st.button("🚀 GÉNÉRER LA FUSION POUR SIGNATURE", use_container_width=True, type="primary"):
            writer = PdfWriter()
            carte = []
            for f in fichiers_tries:
                reader = PdfReader(f)
                writer.append(f)
                carte.append({"n": f.name, "p": len(reader.pages)})
            
            # Injection de la structure invisible pour BOB
            writer.add_metadata({"/StructureProd": json.dumps(carte)})
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            
            st.session_state.pdf_data = pdf_out.getvalue()
            st.session_state.pdf_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
            st.success("Fusion réussie ! Téléchargez le fichier et passez à l'étape 2.")
            st.download_button("⬇️ TÉLÉCHARGER LE PDF FUSIONNÉ", st.session_state.pdf_data, st.session_state.pdf_name, use_container_width=True)

# --- ÉTAPE 2 : SIGNATURE (Lien Direct) ---
with tab2:
    st.subheader("2. Envoyer sur Dropbox Sign")
    st.info("💡 Sans API, vous devez simplement glisser le fichier téléchargé sur Dropbox Sign.")
    
    col_icon, col_text = st.columns([1, 4])
    with col_icon:
        st.markdown("# ✍️")
    with col_text:
        st.markdown("""
        **Procédure rapide :**
        1. Cliquez sur le bouton ci-dessous pour ouvrir Dropbox Sign.
        2. Glissez-y le fichier généré à l'étape 1.
        3. Ajoutez le destinataire et envoyez !
        """)
    
    st.link_button("🌐 OUVRIR DROPBOX SIGN", "https://app.hellosign.com/home/sendForSignature", use_container_width=True)

# --- ÉTAPE 3 : EXTRACTION BOB ---
with tab3:
    st.subheader("3. Extraire pour encodage BOB")
    st.markdown("<p style='color: gray; margin-top:-15px;'>Déposer le pdf global signé par le.la directeur.rice de production.</p>", unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(pdf_signe)
                carte = json.loads(reader.metadata["/StructureProd"])
                last_page = reader.pages[-1]
                zip_out = io.BytesIO()
                current_page = 0
                
                with zipfile.ZipFile(zip_out, "w") as zf:
                    for item in carte:
                        sw = PdfWriter()
                        for p in range(current_page, current_page + item["p"]):
                            sw.add_page(reader.pages[p])
                        sw.add_page(last_page) # Ajout de la page de signature Dropbox
                        current_page += item["p"]
                        buf = io.BytesIO()
                        sw.write(buf)
                        zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                
                st.balloons()
                st.download_button("⬇️ TÉLÉCHARGER LE PACK ZIP POUR BOB", zip_out.getvalue(), f"LFS - BOB - {datetime.now().strftime('%d-%m-%Y')}.zip", use_container_width=True)
            except:
                st.error("Erreur : Ce PDF ne contient pas la structure 'Le Faux Soir'.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>🎬 LE FAUX SOIR - PRODUCTION</div>", unsafe_allow_html=True)
