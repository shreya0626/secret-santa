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

# ---------- Firebase Init ----------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()


# ---------- SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state["page"] = "register"
if "user" not in st.session_state:
    st.session_state["user"] = None
if "wishlist_submitted" not in st.session_state:
    st.session_state["wishlist_submitted"] = False
if "santa_drawn" not in st.session_state:
    st.session_state["santa_drawn"] = False
if "receiver" not in st.session_state:
    st.session_state["receiver"] = None

st.title("🎉 Let's Celebrate Vitamap's Secret Santa! 🎄")

# ==================== LOGOUT BUTTON ====================
def logout():
    st.session_state["user"] = None
    st.session_state["wishlist_submitted"] = False
    st.session_state["santa_drawn"] = False
    st.session_state["receiver"] = None
    st.session_state["page"] = "register"

# ==================== PAGE 1: REGISTRATION ====================
if st.session_state["page"] == "register":
    st.subheader("👤 Participant Registration")
    selected_name = st.selectbox("Select your name", PARTICIPANTS)
    password = st.text_input("Create a password", type="password")
    password_confirm = st.text_input("Confirm password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register"):
            if password.strip() == "" or password_confirm.strip() == "":
                st.warning("Password cannot be empty!")
            elif password != password_confirm:
                st.warning("Passwords do not match!")
            else:
                user_doc = db.collection("users").document(selected_name).get()
                if user_doc.exists:
                    st.error("This user is already registered! Please login.")
                else:
                    db.collection("users").document(selected_name).set({"password": password})
                    st.success(f"User {selected_name} registered successfully!")
                    st.balloons()
                    st.session_state["page"] = "login"

    with col2:
        if st.button("Already Registered? Login"):
            st.session_state["page"] = "login"

# ==================== PAGE 2: LOGIN ====================
elif st.session_state["page"] == "login":
    st.subheader("🔑 Login")
    username = st.selectbox("Select your name", PARTICIPANTS)
    password = st.text_input("Enter your password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user_doc = db.collection("users").document(username).get()
            if user_doc.exists and user_doc.to_dict().get("password") == password:
                st.session_state["user"] = username

                wishlist_doc = db.collection("wishlists").document(username).get()
                st.session_state["wishlist_submitted"] = wishlist_doc.exists

                assignments_doc = db.collection("assignments").document(YEAR).get()
                if assignments_doc.exists:
                    receiver = assignments_doc.to_dict().get(username)
                    if receiver:
                        st.session_state["santa_drawn"] = True
                        st.session_state["receiver"] = receiver

                st.success(f"Welcome back, {username}!")
                st.balloons()
                st.session_state["page"] = "dashboard"
            else:
                st.error("Invalid username or password")
    with col2:
        if st.button("Back to Registration"):
            st.session_state["page"] = "register"

# ==================== PAGE 3: DASHBOARD ====================
elif st.session_state["page"] == "dashboard":
    user = st.session_state.get("user")
    if not user:
        st.warning("Please login first.")
        st.session_state["page"] = "login"
    else:
        st.subheader(f"🎅 Hello {user}! Secret Santa Dashboard")

        # ---------- WISHLIST ----------
        st.subheader("📝 Add / Update Your Wishlist")
        wishlist_doc = db.collection("wishlists").document(user).get()
        current_wishlist = wishlist_doc.to_dict().get("wishlist", "") if wishlist_doc.exists else ""
        wishlist_text = st.text_area("Paste product links or gift ideas", value=current_wishlist, height=120)

        if st.button("💾 Save / Update Wishlist"):
            if wishlist_text.strip() == "":
                st.warning("Wishlist cannot be empty!")
            else:
                db.collection("wishlists").document(user).set({"wishlist": wishlist_text})
                st.success("Wishlist saved successfully!")
                st.session_state["wishlist_submitted"] = True

        # ---------- DRAW SECRET SANTA ----------
        st.subheader("🎁 Draw Your Secret Santa Recipient")
        assignments_doc = db.collection("assignments").document(YEAR).get()
        drawn_assignments = assignments_doc.to_dict() if assignments_doc.exists else {}

        if not st.session_state["santa_drawn"]:
            if st.session_state["wishlist_submitted"]:
                if st.button("Draw My Recipient"):
                    available = [p for p in PARTICIPANTS if p != user and p not in drawn_assignments.values()]
                    if not available:
                        st.error("No valid recipients available. Please contact admin.")
                    else:
                        receiver = random.choice(available)
                        drawn_assignments[user] = receiver
                        db.collection("assignments").document(YEAR).set(drawn_assignments)
                        st.session_state["receiver"] = receiver
                        st.session_state["santa_drawn"] = True
                        st.success(f"🎉 You are gifting to **{receiver}**")
                        st.balloons()
                        wish_doc = db.collection("wishlists").document(receiver).get()
                        if wish_doc.exists:
                            st.info("🎯 Wishlist:")
                            st.write(wish_doc.to_dict().get("wishlist"))
                        else:
                            st.warning("Recipient has not submitted wishlist yet.")
        else:
            receiver = st.session_state["receiver"]
            st.success(f"🎉 You are gifting to **{receiver}**")
            wish_doc = db.collection("wishlists").document(receiver).get()
            if wish_doc.exists:
                st.info("🎯 Wishlist:")
                st.write(wish_doc.to_dict().get("wishlist"))
            else:
                st.warning("Recipient has not submitted wishlist yet.")

        # ---------- LOGOUT BUTTON (BOTTOM) ----------
        st.markdown("---")
        st.button("🚪 Logout", on_click=lambda: logout())
