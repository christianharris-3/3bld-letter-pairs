import random

import bcrypt
import streamlit as st
st.set_page_config(layout="wide")
import json
import os

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWX"

class Funcer:
    def __init__(self, func, args):
        self.func = lambda: func(args)

def get_filename():
    return f"pairs_{st.session_state.get('username', '')}.json"

def load_data():
    if os.path.exists(get_filename()):
        with open(get_filename(), "r") as f:
            data = json.load(f)
    else:
        data = {}
    for a in LETTERS:
        for b in LETTERS:
            pair = a+b
            if a != b and (pair not in data) and len(pair) == 2:
                data[pair] = ""
    return data

def save_data(data):
    filtered_data = {}
    for key, val in data.items():
        if val != "":
            filtered_data[key] = val
    with open(get_filename(), "w") as f:
        json.dump(filtered_data, f, indent="  ")

def view_letter(pair, data, con):
    with con.form("Edit Word Form", border=False):
        st.markdown(f"## Pair {pair}")

        word = data[pair]
        if not (word == "" or word is None):
            st.markdown(f"Word is: {word}")

        new_word = st.text_input("Enter Word", key="word_input")
        submitted = st.form_submit_button("Save")

        if submitted:
            data[pair] = new_word
            save_data(data)
            st.toast(f"Pair {pair} set to {new_word}")
            st.session_state["clear_word_input"] = True
            st.rerun()


def set_pair(letters):
    st.session_state["letter_search"] = letters

def make_grid(con):
    con.markdown("## Letter Grid")

    cols = con.columns(len(LETTERS) + 1)
    for i in range(len(LETTERS)):
        cols[i+1].button(LETTERS[i], key=f"grid_col_title_{LETTERS[i]}")

    for first in LETTERS:
        cols = con.columns(len(LETTERS)+1)
        cols[0].button(first, key=f"grid_row_title_{first}")
        for i, second in enumerate(LETTERS):
            funcer = Funcer(set_pair, first+second)
            cols[i+1].button(
                first+second, key=f"grid_square_{first}{second}",
                type="tertiary", on_click=funcer.func,
                disabled=first==second
            )


def letter_search(data):
    st.markdown("# Search Letters")

    text = st.text_input("View Letter", max_chars=2, key="letter_search").upper()

    if text in data.keys():
        view_letter(text, data, st.container(border=True))

    make_grid(st.container(border=True))

def letter_quiz(data):
    st.markdown("# Quiz")

    bag = {}
    for key, val in data.items():
        if val != "":
            bag[key] = val

    if len(bag) < 2:
        st.markdown("No words given, can't quiz you on nothing!")
    else:
        if st.session_state.get("random_pair", None) is None:
            st.session_state["random_pair"] = random.choice(list(bag.keys()))
        del bag[st.session_state["random_pair"]]

        st.markdown(f"What is the word for {st.session_state['random_pair']}?")
        if st.button("Show", shortcut="Space"):
            st.markdown(f"Word is \"{data[st.session_state['random_pair']]}\"")
            shown = True
        else:
            st.markdown(f"Word is -----")
            shown = False
        if st.button("Next", shortcut = "Space" if shown else "Enter"):
            st.session_state["random_pair"] = random.choice(list(bag.keys()))
            st.rerun()

def enter_words(data):
    st.markdown("# Enter Words")

    unused_pairs = []
    for key, val in data.items():
        if val == "":
            unused_pairs.append(key)

    st.markdown(f"There are {len(unused_pairs)} pairs without words")
    pair = st.selectbox("Select Letter", unused_pairs)

    view_letter(pair, data, st.container(border=True))

def manage_files(data):
    st.markdown("# Files")

    if os.path.exists(get_filename()):
        with open(get_filename(), "r") as f:
            st.download_button("Download Words File", data=json.dumps(json.load(f), indent="  "), file_name="pairs.json")
    else:
        st.markdown("no data to download")
    file = st.file_uploader("Upload Pairs Json", type="json")
    if file is not None:
        data = json.load(file)
        with open(get_filename(), "w") as f:
            json.dump(data, f, indent="  ")
        st.success("Saved upload")


def app():
    data = load_data()

    cols = st.columns(5)
    search = cols[0].button("Search", width="stretch")
    quiz = cols[1].button("Quiz", width="stretch")
    enter = cols[2].button("Enter Words", width="stretch")
    files = cols[3].button("Files", width="stretch")

    if search: st.session_state["current_page"] = "search"
    if quiz: st.session_state["current_page"] = "quiz"
    if enter: st.session_state["current_page"] = "enter_words"
    if files: st.session_state["current_page"] = "files"

    if st.session_state.get("current_page", None) is None:
        st.session_state["current_page"] = "search"

    if st.session_state.get("clear_word_input",False):
        st.session_state["word_edit"] = ""
        st.session_state["word_input"] = ""
        st.session_state["clear_word_input"] = False

    if st.session_state["current_page"] == "search":
        letter_search(data)
    elif st.session_state["current_page"] == "quiz":
        letter_quiz(data)
    elif st.session_state["current_page"] == "enter_words":
        enter_words(data)
    elif st.session_state["current_page"] == "files":
        manage_files(data)

    if cols[4].button(f"{st.session_state['username']}: Logout", width="stretch"):
        st.session_state["authenticated"] = False
        st.rerun()

def check_credentials(accounts, username, password):
    for account in accounts:
        if username.lower() == account["Username"].lower() and check_password(password, account["Password"]):
            return True, account["Username"]
    return False, None


def hash_password(password):
    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()
    return password_hash

def check_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode(),
        password_hash.encode()
    )

def login_page():
    st.markdown("## Login")

    login, register = st.tabs(["Login", "Register"])

    accounts_file = "accounts.json"
    if not os.path.exists(accounts_file):
        with open(accounts_file, "w") as f:
            json.dump([], f, indent="  ")
    with open(accounts_file, "r") as f:
        accounts = json.load(f)

    with register:
        with st.form("register"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Repeat Password", type="password")

            submitted = st.form_submit_button("Register")

            if submitted:
                if username == "" or password == "":
                    st.error("Username and password can't be empty")
                    return
                if password != password2:
                    st.error("Passwords are not the same")
                    return
                for account in accounts:
                    if account["Username"] == username:
                        st.error("Username already in use")
                        return
                accounts.append({"Username": username, "Password": hash_password(password)})
                with open(accounts_file, "w") as f:
                    json.dump(accounts, f, indent="  ")
                st.success("Account Created")
    with login:
        with st.form("sign_in"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button("Login")

            if submitted:
                checked, username = check_credentials(accounts, username, password)
                if checked:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid Credentials")


if st.session_state.get("authenticated", False):
    app()
else:
    login_page()