import streamlit as st
import json
import io
import zipfile
import os
from datetime import datetime
from pypdf import PdfReader, PdfWriter
import dropbox_sign
from dropbox_sign.apis import SignatureRequestApi
from dropbox_sign.models import SignatureRequestSendRequest

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="LE FAUX SOIR - Production", page_icon="🎬", layout="centered")

# CSS pour la francisation et l'esthétique
st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] button { display: none !important; }
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
    div[data-testid="stFileUploaderDropzone"] section > div > div::after {
        content: "Documents PDF uniquement • Max 200 Mo";
        display: block; font-size: 0.85rem; color: #808495; margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation des variables de session
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
if 'pdf_name' not in st.session_state: st.session_state.pdf_name = ""

def reset_app():
    st.session_state.pdf_data = None
    st.session_state.pdf_name = ""
    st.rerun()

# --- HEADER ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire de Production</p>", unsafe_allow_html=True)

# Création des 3 onglets
tab1, tab2, tab3 = st.tabs(["➕ 1. PRÉPARER (Fusion)", "✍️ 2. SIGNER (Dropbox)", "✂️ 3. EXTRAIRE (BOB)"])

# --- ÉTAPE 1 : FUSION ---
with tab1:
    st.subheader("1. Préparer le document global")
    st.markdown("<p style='color: gray; margin-top:-15px;'>Ajouter les pdfs qui sont placés dans \"OK Laurie\"</p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        
        # Statistiques
        m1, m2 = st.columns(2)
        total_p = sum([len(PdfReader(f).pages) for f in fichiers_tries])
        m1.metric("Documents", len(files))
        m2.metric("Total Pages", total_p)

        with st.expander("👁️ Liste des fichiers chargés", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 GÉNÉRER LA FUSION", use_container_width=True, type="primary"):
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
                
                st.session_state.pdf_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y - %Hh%M')}.pdf"
                st.session_state.pdf_data = pdf_out.getvalue()
                st.success("Document global généré ! Passez à l'étape 2 pour l'envoi.")
        
        with col_btn2:
            if st.button("🗑️ VIDER LA LISTE", use_container_width=True): reset_app()

# --- ÉTAPE 2 : SIGNATURE ---
with tab2:
    st.subheader("2. Envoyer pour signature")
    if st.session_state.pdf_data is None:
        st.info("Veuillez d'abord préparer un document à l'étape 1.")
    else:
        st.write(f"📄 Document prêt : `{st.session_state.pdf_name}`")
        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            nom = st.text_input("Nom du signataire", placeholder="Prénom Nom")
        with col_b:
            email = st.text_input("Email du signataire", placeholder="exemple@prod.com")
            
        if st.button("🚀 ENVOYER VIA DROPBOX SIGN", use_container_width=True, type="primary"):
            if email and nom:
                try:
                    api_key = st.secrets["DROPBOX_SIGN_API_KEY"]
                    configuration = dropbox_sign.Configuration(username=api_key)
                    with dropbox_sign.ApiClient(configuration) as api_client:
                        signature_api = SignatureRequestApi(api_client)
                        
                        temp_path = "to_sign.pdf"
                        with open(temp_path, "wb") as f: f.write(st.session_state.pdf_data)

                        request = SignatureRequestSendRequest(
                            title=st.session_state.pdf_name,
                            subject="Documents à signer - Le Faux Soir",
                            message=f"Bonjour {nom}, merci de signer ces documents de production.",
                            signers=[{"email_address": email, "name": nom}],
                            files=[open(temp_path, "rb")],
                            test_mode=True
                        )
                        signature_api.signature_request_send(request)
                        st.success(f"✅ Envoyé avec succès à {nom} !")
                        st.balloons()
                        if os.path.exists(temp_path): os.remove(temp_path)
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Veuillez remplir le nom et l'email.")
        
        st.download_button("⬇️ Ou télécharger pour envoi manuel", st.session_state.pdf_data, st.session_state.pdf_name, use_container_width=True)

# --- ÉTAPE 3 : EXTRACTION BOB ---
with tab3:
    st.subheader("3. Extraire pour encodage BOB")
    st.markdown("""
        <p style='color: gray; margin-top:-15px;'>
        Déposer le pdf global signé par le.la directeur.rice de production ou post-production.
        </p>
        <p style='color: gray; margin-top: -10px;'>
        Les pdfs signés seront prêts à être encodés.
        </p>
        """, unsafe_allow_html=True)
    
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
                        for p in range(current_page, current_page + item["p"]): sw.add_page(reader.pages[p])
                        sw.add_page(last_page)
                        current_page += item["p"]
                        buf = io.BytesIO()
                        sw.write(buf)
                        zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                st.balloons()
                st.download_button("⬇️ TÉLÉCHARGER LE PACK ZIP POUR BOB", zip_out.getvalue(), f"LFS - BOB - {datetime.now().strftime('%d-%m-%Y')}.zip", use_container_width=True)
            except:
                st.error("Ce fichier ne contient pas les données de structure.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>🎬 LE FAUX SOIR - PRODUCTION</div>", unsafe_allow_html=True)
