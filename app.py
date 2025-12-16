import streamlit as st
import random
import firebase_admin
from firebase_admin import credentials, firestore

# ================= CONFIG =================
YEAR = "2025"
PARTICIPANTS = [
    "Shreya", "Sinchana", "Punashri", "Govind",
    "Prasad", "Chethana", "Thanuja", "Mamatha",
    "Harini", "Ghanashyam", "Sharath Kumar",
    "Sudheshna", "Goutham"
]

# ================= FIREBASE INIT =================
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ================= SESSION STATE =================
if "page" not in st.session_state:
    st.session_state.page = "register"
if "user" not in st.session_state:
    st.session_state.user = None
if "wishlist_submitted" not in st.session_state:
    st.session_state.wishlist_submitted = False
if "santa_drawn" not in st.session_state:
    st.session_state.santa_drawn = False
if "receiver" not in st.session_state:
    st.session_state.receiver = None

st.title("🎉 Let's Celebrate Vitamap's Secret Santa! 🎄")

# ================= LOGOUT =================
def logout():
    st.session_state.user = None
    st.session_state.wishlist_submitted = False
    st.session_state.santa_drawn = False
    st.session_state.receiver = None
    st.session_state.page = "register"

# ================= REGISTER =================
if st.session_state.page == "register":
    st.subheader("👤 Participant Registration")

    selected_name = st.selectbox("Select your name", PARTICIPANTS)
    password = st.text_input("Create a password", type="password")
    confirm = st.text_input("Confirm password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Register"):
            if not password or not confirm:
                st.warning("Password cannot be empty!")
            elif password != confirm:
                st.warning("Passwords do not match!")
            else:
                user_ref = db.collection("users").document(selected_name)
                if user_ref.get().exists:
                    st.error("User already registered. Please login.")
                else:
                    user_ref.set({"password": password})
                    st.success("Registration successful!")
                    st.balloons()
                    st.session_state.page = "login"

    with col2:
        if st.button("Already Registered? Login"):
            st.session_state.page = "login"

# ================= LOGIN =================
elif st.session_state.page == "login":
    st.subheader("🔑 Login")

    username = st.selectbox("Select your name", PARTICIPANTS)
    password = st.text_input("Enter your password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            user_doc = db.collection("users").document(username).get()
            if user_doc.exists and user_doc.to_dict().get("password") == password:
                st.session_state.user = username

                wishlist_doc = db.collection("wishlists").document(username).get()
                st.session_state.wishlist_submitted = wishlist_doc.exists

                assign_doc = db.collection("assignments").document(YEAR).get()
                if assign_doc.exists:
                    receiver = assign_doc.to_dict().get(username)
                    if receiver:
                        st.session_state.santa_drawn = True
                        st.session_state.receiver = receiver

                st.success(f"Welcome {username}!")
                st.balloons()
                st.session_state.page = "dashboard"
            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Back to Registration"):
            st.session_state.page = "register"

# ================= DASHBOARD =================
elif st.session_state.page == "dashboard":
    user = st.session_state.user
    if not user:
        st.session_state.page = "login"
        st.stop()

    st.subheader(f"🎅 Hello {user}!")

    # ---------- WISHLIST ----------
    st.subheader("📝 Your Wishlist")
    wishlist_doc = db.collection("wishlists").document(user).get()
    wishlist_value = wishlist_doc.to_dict().get("wishlist", "") if wishlist_doc.exists else ""

    wishlist = st.text_area(
        "Add gift ideas or product links",
        value=wishlist_value,
        height=120
    )

    if st.button("Save Wishlist"):
        if wishlist.strip():
            db.collection("wishlists").document(user).set({"wishlist": wishlist})
            st.success("Wishlist saved!")
            st.session_state.wishlist_submitted = True
        else:
            st.warning("Wishlist cannot be empty")

    # ---------- DRAW ----------
    st.subheader("🎁 Secret Santa Draw")
    assignments_ref = db.collection("assignments").document(YEAR)
    assignments = assignments_ref.get().to_dict() if assignments_ref.get().exists else {}

    if not st.session_state.santa_drawn:
        if st.session_state.wishlist_submitted:
            if st.button("Draw My Recipient"):
                available = [
                    p for p in PARTICIPANTS
                    if p != user and p not in assignments.values()
                ]

                if not available:
                    st.error("No recipients available. Contact admin.")
                else:
                    receiver = random.choice(available)
                    assignments[user] = receiver
                    assignments_ref.set(assignments)

                    st.session_state.receiver = receiver
                    st.session_state.santa_drawn = True
                    st.success(f"🎉 You are gifting to **{receiver}**")
                    st.balloons()
        else:
            st.info("Submit wishlist before drawing.")

    if st.session_state.santa_drawn:
        receiver = st.session_state.receiver
        st.success(f"🎉 You are gifting to **{receiver}**")

        wish = db.collection("wishlists").document(receiver).get()
        if wish.exists:
            st.info("🎯 Recipient Wishlist")
            st.write(wish.to_dict().get("wishlist"))
        else:
            st.warning("Recipient has not added a wishlist yet.")

    st.markdown("---")
    st.button("🚪 Logout", on_click=logout)
