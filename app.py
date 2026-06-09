import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN "APP MOBILE"
st.set_page_config(page_title="© PDF Manager", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* 1. STYLISATION DES TABS */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 12px !important;
        margin: 5px !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: #FF4B4B !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3) !important;
    }

    div[data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: rgba(0,0,0,0.05) !important;
        padding: 8px !important;
        border-radius: 16px !important;
        border-bottom: none !important;
    }
    
    /* Zone d'upload */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #FF4B4B !important;
        border-radius: 20px !important;
        background-color: rgba(255, 75, 75, 0.02) !important;
    }

    /* Page d'accueil */
    .home-hero {
        margin-top: 6px;
        padding: 34px 30px;
        border-radius: 8px;
        color: #FFFFFF;
        background:
            linear-gradient(135deg, rgba(23, 33, 48, 0.96), rgba(55, 77, 95, 0.92)),
            repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 16px);
        border: 1px solid rgba(255,255,255,0.12);
    }

    .home-hero h1 {
        font-size: 2.1rem;
        line-height: 1.15;
        margin: 0 0 12px 0;
        letter-spacing: 0;
    }

    .home-hero p {
        max-width: 650px;
        color: rgba(255,255,255,0.82);
        font-size: 1.03rem;
        margin: 0;
    }

    .home-kicker {
        color: #FFD166;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 12px;
        text-transform: uppercase;
    }

    .home-panel {
        padding: 18px;
        border: 1px solid rgba(49, 61, 78, 0.14);
        border-radius: 8px;
        background: #FFFFFF;
        min-height: 148px;
        box-shadow: 0 8px 24px rgba(23, 33, 48, 0.06);
    }

    .home-panel strong {
        display: block;
        color: #172130;
        font-size: 1rem;
        margin-bottom: 8px;
    }

    .home-panel span {
        color: #5D6876;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .home-step {
        padding: 14px 0;
        border-bottom: 1px solid rgba(49, 61, 78, 0.12);
    }

    .home-step:last-child {
        border-bottom: none;
    }

    .home-step-title {
        color: #172130;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .home-step-body {
        color: #5D6876;
        font-size: 0.92rem;
    }

    .home-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        color: #146C43;
        background: #EAF7EF;
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 18px;
    }

    @media (prefers-color-scheme: dark) {
        .home-panel {
            background: #171717;
            border-color: rgba(255,255,255,0.12);
        }
        .home-panel strong,
        .home-step-title {
            color: #F7F7F7;
        }
        .home-panel span,
        .home-step-body {
            color: #C7C7C7;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation des états pour le reset
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

# --- CONTENU PRINCIPAL ---
st.title("🎬 PDF Manager")
st.markdown("<p style='font-size: 1.1em; color: gray; margin-top: -20px;'>Gestionnaire des pièces comptables</p>", unsafe_allow_html=True)

tab_home, tab1, tab2 = st.tabs(["🏠 ACCUEIL", "➕ PRÉPARER", "✂️ EXTRAIRE"])

# --- ONGLET 0 : ACCUEIL ---
with tab_home:
    st.markdown("""
        <section class="home-hero">
            <div class="home-kicker">Production comptable sécurisée</div>
            <h1>Préparer, signer et retrouver chaque facture sans ressaisie.</h1>
            <p>
                PDF Manager centralise les pièces validées, conserve leur structure
                d'origine et prépare les documents signés pour l'encodage dans HORUS.
            </p>
            <span class="home-badge">Flux recommandé : Préparer → YouSign → Extraire</span>
        </section>
        """, unsafe_allow_html=True)

    st.markdown(" ")
    col_home_1, col_home_2, col_home_3 = st.columns(3)

    with col_home_1:
        st.markdown("""
            <div class="home-panel">
                <strong>Ordre maîtrisé</strong>
                <span>Les PDFs sont regroupés dans un fichier unique, avec une trace de leur nom et de leur pagination.</span>
            </div>
            """, unsafe_allow_html=True)

    with col_home_2:
        st.markdown("""
            <div class="home-panel">
                <strong>Signature simplifiée</strong>
                <span>Un seul document part à la signature, ce qui limite les manipulations et les oublis.</span>
            </div>
            """, unsafe_allow_html=True)

    with col_home_3:
        st.markdown("""
            <div class="home-panel">
                <strong>Sortie prête HORUS</strong>
                <span>Après signature, les factures sont séparées et renommées avec la nomenclature attendue.</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### Parcours de production")
    st.markdown("""
        <div class="home-step">
            <div class="home-step-title">1. Préparer le lot</div>
            <div class="home-step-body">Déposez les PDFs validés dans l'onglet PRÉPARER, puis téléchargez le PDF unique.</div>
        </div>
        <div class="home-step">
            <div class="home-step-title">2. Faire signer</div>
            <div class="home-step-body">Envoyez le PDF unique via YouSign avec le circuit de signature habituel.</div>
        </div>
        <div class="home-step">
            <div class="home-step-title">3. Extraire pour encodage</div>
            <div class="home-step-body">Déposez le PDF signé dans l'onglet EXTRAIRE pour obtenir l'archive des documents signés.</div>
        </div>
        """, unsafe_allow_html=True)

# --- ONGLET 1 : FUSION ---
with tab1:
    st.markdown("### 📂 Fusionner pour signature")
    
    files = st.file_uploader(
        "uploader_1", 
        type="pdf", 
        accept_multiple_files=True, 
        label_visibility="collapsed",
        key=f"up1_{st.session_state.uploader_key}"
    )
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        st.markdown(f"**Fichiers prêts ({len(files)}) :**")
        for f in fichiers_tries:
            st.markdown(f"✅ {f.name}")
        
        st.markdown(" ")
        col1, col2 = st.columns(2)
        
        with col1:
            writer = PdfWriter()
            # On enregistre le nom exact tel quel (MAJUSCULES préservées)
            carte = [{"n": f.name, "p": len(PdfReader(f).pages)} for f in fichiers_tries]
            for f in fichiers_tries: writer.append(f)
            writer.add_metadata({"/StructureProd": json.dumps(carte)})
            
            PDF_out = io.BytesIO()
            writer.write(PDF_out)
            nom_fusion = f"FAIRWAY - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
            
            st.download_button(
                label="🚀 GÉNÉRER & TÉLÉCHARGER",
                data=PDF_out.getvalue(),
                file_name=nom_fusion,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            if st.button("🗑️ VIDER TOUT", key="reset_tab1", use_container_width=True):
                st.session_state.uploader_key += 1
                st.rerun()

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.markdown("### ✂️ Découper le PDF signé")
    PDF_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed", key=f"up2_{st.session_state.uploader_key}")
    
    if PDF_signe:
        try:
            reader = PdfReader(PDF_signe)
            if "/StructureProd" not in reader.metadata:
                st.error("⚠️ Ce PDF ne contient pas les informations de structure nécessaires.")
            else:
                carte = json.loads(reader.metadata["/StructureProd"])
                last_page = reader.pages[-1]
                zip_out = io.BytesIO()
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
                        
                        # NOMENCLATURE : Nom d'origine (MAJ) + (signed) en minuscule
                        nom_origine = item["n"]
                        if nom_origine.lower().endswith('.pdf'):
                            # On retire l'extension .pdf (peu importe sa casse) et on ajoute le suffixe
                            nom_final = nom_origine[:-4] + " (signed).pdf"
                        else:
                            nom_final = nom_origine + " (signed).pdf"
                        
                        zf.writestr(nom_final, buf.getvalue())
                
                st.success(f"✅ {len(carte)} documents prêts avec nomenclature respectée.")
                
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    st.download_button(
                        label="⚡ TÉLÉCHARGER LES DOCUMENTS SPLITÉS",
                        data=zip_out.getvalue(),
                        file_name=f"LFS - split - {datetime.now().strftime('%d-%m-%Y')}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )
                with col_ex2:
                    if st.button("🗑️ VIDER TOUT", key="reset_tab2", use_container_width=True):
                        st.session_state.uploader_key += 1
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>© Copyright - Corentin Pilarczyk</div>", unsafe_allow_html=True)
