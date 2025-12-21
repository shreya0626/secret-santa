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
state_defaults = {
    "page": "register",
    "user": None,
    "wishlist_submitted": False,
    "santa_drawn": False,
    "receiver": None
}

for k, v in state_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("🎉 Vitamap Secret Santa – Treasure Hunt 🎄")

# ================= LOGOUT =================
def logout():
    for k, v in state_defaults.items():
        st.session_state[k] = v

# ================= REGISTER =================
if st.session_state.page == "register":
    st.subheader("👤 Registration")

    name = st.selectbox("Select your name", PARTICIPANTS)
    pwd = st.text_input("Create password", type="password")
    cpwd = st.text_input("Confirm password", type="password")

    if st.button("Register"):
        if not pwd or pwd != cpwd:
            st.warning("Passwords do not match or are empty")
        else:
            ref = db.collection("users").document(name)
            if ref.get().exists:
                st.error("Already registered. Please login.")
            else:
                ref.set({"password": pwd})
                st.success("Registration successful!")
                st.session_state.page = "login"

    if st.button("Already Registered? Login"):
        st.session_state.page = "login"

# ================= LOGIN =================
elif st.session_state.page == "login":
    st.subheader("🔑 Login")

    name = st.selectbox("Your name", PARTICIPANTS)
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        doc = db.collection("users").document(name).get()
        if doc.exists and doc.to_dict()["password"] == pwd:
            st.session_state.user = name

            st.session_state.wishlist_submitted = (
                db.collection("wishlists").document(name).get().exists
            )

            assign_doc = db.collection("assignments").document(YEAR).get()
            if assign_doc.exists:
                r = assign_doc.to_dict().get(name)
                if r:
                    st.session_state.santa_drawn = True
                    st.session_state.receiver = r

            st.success(f"Welcome {name}!")
            st.session_state.page = "dashboard"
        else:
            st.error("Invalid credentials")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔒 Forgot Password"):
            st.session_state.page = "forgot"
    with col2:
        if st.button("🆕 Back to Registration"):
            st.session_state.page = "register"

# ================= FORGOT PASSWORD =================
elif st.session_state.page == "forgot":
    st.subheader("🔒 Reset Password")

    name = st.selectbox("Select your name", PARTICIPANTS)
    np = st.text_input("New password", type="password")
    cp = st.text_input("Confirm password", type="password")

    if st.button("Update Password"):
        if not np or np != cp:
            st.warning("Passwords do not match")
        else:
            ref = db.collection("users").document(name)
            if ref.get().exists:
                ref.update({"password": np})
                st.success("Password updated!")
                st.session_state.page = "login"
            else:
                st.error("User not found")

    if st.button("⬅ Back to Login"):
        st.session_state.page = "login"

# ================= DASHBOARD =================
elif st.session_state.page == "dashboard":
    user = st.session_state.user
    st.subheader(f"🎅 Hello {user}")

    # ---------- WISHLIST ----------
    st.subheader("📝 Your Wishlist")
    wref = db.collection("wishlists").document(user)
    old = wref.get().to_dict().get("wishlist", "") if wref.get().exists else ""

    wishlist = st.text_area("Gift ideas / links", value=old)
    if st.button("Save Wishlist"):
        if wishlist.strip():
            wref.set({"wishlist": wishlist})
            st.session_state.wishlist_submitted = True
            st.success("Wishlist saved")

    # ---------- DRAW ----------
    st.subheader("🎁 Secret Santa Draw")
    aref = db.collection("assignments").document(YEAR)
    assignments = aref.get().to_dict() if aref.get().exists else {}

    if not st.session_state.santa_drawn:
        if st.session_state.wishlist_submitted:
            if st.button("Draw My Recipient"):
                available = [
                    p for p in PARTICIPANTS
                    if p != user and p not in assignments.values()
                ]
                if available:
                    r = random.choice(available)
                    assignments[user] = r
                    aref.set(assignments)
                    st.session_state.receiver = r
                    st.session_state.santa_drawn = True
                    st.success(f"🎉 You are gifting to **{r}**")
                else:
                    st.error("No recipients available")
        else:
            st.info("Submit wishlist before drawing")

    # ---------- SANTA VIEW ----------
    if st.session_state.santa_drawn:
        r = st.session_state.receiver

        st.markdown("---")
        st.subheader("🎁 Your Assigned Receiver")
        st.success(f"**{r}**")

        # Receiver wishlist
        rw = db.collection("wishlists").document(r).get()
        if rw.exists:
            st.info("📝 Receiver Wishlist")
            st.write(rw.to_dict().get("wishlist"))
        else:
            st.warning("Receiver has not added wishlist yet")

        # Add clues
        st.subheader("🧩 Add Treasure Hunt Clues (Santa Only)")
        cref = db.collection("clues").document(r)
        existing = cref.get().to_dict() if cref.get().exists else {}

        c1 = st.text_input("Clue 1", value=existing.get("clue1", ""))
        c2 = st.text_input("Clue 2", value=existing.get("clue2", ""))
        c3 = st.text_input("Final Clue", value=existing.get("clue3", ""))

        if st.button("Save Clues"):
            cref.set({
                "clue1": c1,
                "clue2": c2,
                "clue3": c3
            })
            st.success("Clues saved successfully 🗺️")

    # ---------- RECEIVER VIEW ----------
    st.markdown("---")
    st.subheader("🎯 Your Treasure Hunt Clues")

    my_clues = db.collection("clues").document(user).get()
    if my_clues.exists:
        data = my_clues.to_dict()
        st.info(f"🧩 Clue 1: {data.get('clue1','')}")
        st.info(f"🧩 Clue 2: {data.get('clue2','')}")
        st.success(f"🎁 Final Clue: {data.get('clue3','')}")
    else:
        st.warning("No clues yet. Wait for your Secret Santa 🎅")

    st.markdown("---")
    st.button("🚪 Logout", on_click=logout)
