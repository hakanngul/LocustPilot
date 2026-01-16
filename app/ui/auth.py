import streamlit as st
import os


def check_password() -> bool:
    """
    Returns True if the user had the correct password.
    """
    password_env = os.getenv("APP_PASSWORD")

    # Şifre environment variable olarak yoksa direkt geç
    if not password_env:
        return True

    # --- CSS: Sadece ortalama ve animasyon (Renk yok, bozulmaz) ---
    st.markdown(
        """
        <style>
        div.block-container {
            padding-top: 5rem;
        }
        .auth-logo {
            font-size: 3rem;
            text-align: center;
            display: block;
            margin-bottom: 20px;
            animation: float 6s ease-in-out infinite;
        }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        .stButton button {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- SESSION STATE BAŞLANGICI ---
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Eğer zaten giriş yapıldıysa direkt True dön
    if st.session_state["password_correct"]:
        return True

    # --- ARAYÜZ ---
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        with st.container(border=True):
            st.markdown('<div class="auth-logo">🦗</div>', unsafe_allow_html=True)
            st.markdown(
                "<h2 style='text-align: center; margin-bottom: 0;'>Locust Platform</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align: center; opacity: 0.6; font-size: 0.9rem;'>Locust Load Testing Platform</p>",
                unsafe_allow_html=True,
            )
            st.write("")

            # --- FORM MANTIĞI (DÜZELTİLDİ) ---
            with st.form("login_form", clear_on_submit=False):
                # Password input'u direkt değişkene atıyoruz
                password_input = st.text_input(
                    "Password",
                    type="password",
                    label_visibility="collapsed",
                    placeholder="Access Key...",
                )

                st.write("")
                submitted = st.form_submit_button("Authenticate", type="primary")

                # BUTONA BASILINCA ÇALIŞACAK KISIM
                if submitted:
                    if password_input == password_env:
                        st.session_state["password_correct"] = True
                        st.rerun()  # <--- BU SATIR ÇOK ÖNEMLİ (Tek tıkla geçişi sağlar)
                    else:
                        st.error(
                            "⚠️ Invalid Access Key"
                        )  # Error only shows when button is clicked and password is incorrect

            st.markdown(
                "<p style='text-align: center; font-size: 0.75rem; opacity: 0.5; margin-top: 20px;'>Secured by Locust App</p>",
                unsafe_allow_html=True,
            )

    # Giriş yapılmadıysa False dön
    return False
