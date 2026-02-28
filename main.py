import math
import random
import time

import bcrypt
import streamlit as st
# from streamlit_extras import stylable_containers
st.set_page_config(layout="wide", page_title="3BLD Letter Pairs")
import json
import os
import copy
from datetime import datetime

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWX"
DATA_PATH = "data"

class Funcer:
    def __init__(self, func, args):
        self.func = lambda: func(args)

def get_filename():
    return f"{DATA_PATH}/pairs_{st.session_state.get('username', '')}.json"

def load_data():
    if os.path.exists(get_filename()):
        with open(get_filename(), "r") as f:
            data = json.load(f)
    else:
        data = {}

    # convert datetime
    for key in data:
        data[key]["last_checked"] = datetime.fromisoformat(data[key]["last_checked"])

    # fill out data
    for a in LETTERS:
        for b in LETTERS:
            pair = a+b
            if a != b and (pair not in data) and len(pair) == 2:
                data[pair] = {
                    "word": "",
                    "last_confidence": 0,
                    "last_checked": datetime.now(),
                }
    return data

def save_data(data):
    filtered_data = {}
    for key, val in data.items():
        if val["word"] != "":
            filtered_data[key] = copy.deepcopy(val)
            filtered_data[key]["last_checked"] = filtered_data[key]["last_checked"].isoformat()

    with open(get_filename(), "w") as f:
        json.dump(filtered_data, f, indent="  ")

def view_letter(pair, data, con):
    with con.form("Edit Word Form", border=False):
        st.markdown(f"## Pair {pair}")

        dict_ = data[pair]
        if dict_["word"] != "":
            st.markdown(f"Word is: {dict_['word']}")

        new_word = st.text_input("Enter Word", key="word_input")
        submitted = st.form_submit_button("Save")

        if submitted:
            data[pair]["word"] = new_word
            save_data(data)
            st.toast(f"Pair {pair} set to {new_word}")
            st.session_state["clear_word_input"] = True
            st.rerun()


def set_pair(letters):
    st.session_state["letter_search"] = letters

def make_grid(data, con):
    con.markdown("## Letter Grid")

    cols = con.columns(len(LETTERS) + 1)
    for i in range(len(LETTERS)):
        cols[i+1].button(LETTERS[i], key=f"grid_col_title_{LETTERS[i]}")

    st.markdown("""
    <style>
    button[kind='primary'] {
        background-color: rgb(14, 17, 23);
        color: green;
        padding: 0;
        border: 0;
    }
    button[kind='primary']:hover {
        background-color: rgb(14, 17, 23);
        color: red;
    }
    </style>""", unsafe_allow_html=True)

    for first in LETTERS:
        cols = con.columns(len(LETTERS)+1)
        cols[0].button(first, key=f"grid_row_title_{first}")
        for i, second in enumerate(LETTERS):
            funcer = Funcer(set_pair, first+second)
            has_val = data.get(first+second, {"word": ""})["word"] != ""
            cols[i+1].button(
                first+second, key=f"grid_square_{first}{second}",
                type="primary" if has_val else "tertiary", on_click=funcer.func,
                disabled=first==second
            )


def letter_search(data):
    st.markdown("# Search Letters")

    text = st.text_input("View Letter", max_chars=2, key="letter_search").upper()

    if text in data.keys():
        view_letter(text, data, st.container(border=True))

    make_grid(data, st.container(border=True))

def generate_quiz(data):
    available_pairs = {}
    for key, val in data.items():
        if val["word"] != "":
            available_pairs[key] = val

    data = []
    for key, dict_ in available_pairs.items():
        if st.session_state["test_type"] == "Test All":
            time_since = (datetime.now().timestamp() - dict_["last_checked"].timestamp()) / 60 / 60 / 24
            value = math.log2(time_since) - dict_["last_confidence"] + random.random()

            data.append((
                key,
                value
            ))
        elif st.session_state["test_type"] == "Test Unknown":
            if dict_["last_confidence"] == 1:
                data.append((
                    key, -dict_["last_checked"].timestamp() / 60 / 60 / 24 + random.random()
                ))


    data.sort(key=lambda x: x[1], reverse=True)
    return [d[0] for d in data]

def pick_pair():
    current = st.session_state.get("current_quiz", None)
    if current is None or len(current) == 0:
        return None
    return current.pop(0)

def letter_quiz(data):
    st.markdown("# Quiz")

    # test type selection
    test_type = st.segmented_control("Type", ["Test All", "Test Unknown"], default="Test All")
    if test_type is not None:
        st.session_state["test_type"] = test_type
    if st.session_state.get("test_type", None) is None:
        st.session_state["test_type"] = "Test All"

    # start test
    if st.button("Start Quiz"):
        st.session_state["show_quiz_stats"] = False
        quiz_data = generate_quiz(data)
        if len(quiz_data) > 0:
            st.session_state["quiz_started"] = True
            st.session_state["current_quiz"] = generate_quiz(data)
            st.session_state["current_quiz_length"] = len(st.session_state["current_quiz"])
            st.session_state["current_quiz_pair"] = pick_pair()
            st.session_state["current_quiz_stats"] = {
                "correct": 0,
                "incorrect": 0,
                "failed_pairs": {},
                "start_time": time.time(),
                "end_time": 0,
            }
        else:
            st.warning("Can't Quiz you on nothing!")
            st.session_state["quiz_started"] = False

    if st.session_state.get("quiz_started", False):
        with st.container(border=True):

            if st.session_state.get("current_quiz_pair", None) is None:
                st.session_state["current_quiz_pair"] = pick_pair()

            st.markdown(f"What is the word for {st.session_state['current_quiz_pair']}?")

            if st.session_state.get("show_quiz_answer", None) is None:
                st.session_state["show_quiz_answer"] = False

            show_button = st.button("Show", shortcut="Space")
            word_container = st.empty()
            answer_text = f"Word is \"{data[st.session_state['current_quiz_pair']]['word']}\""

            if not st.session_state["show_quiz_answer"]:
                word_container.markdown(f"Word is -----")
            else:
                word_container.markdown(answer_text)

            cols = st.columns([2, 2], width=250)

            next_word = 0
            if cols[0].button("Fail", shortcut = "1", width="stretch"):
                next_word = 1
            if cols[1].button("Success", shortcut = "2", width="stretch"):
                next_word = 2
            if show_button:
                word_container.markdown(answer_text)
                st.session_state["show_quiz_answer"] = True

            if next_word > 0:
                if not st.session_state["show_quiz_answer"]:
                    word_container.markdown(answer_text)
                    st.session_state["show_quiz_answer"] = True
                else:
                    data[st.session_state["current_quiz_pair"]]["last_confidence"] = next_word
                    data[st.session_state["current_quiz_pair"]]["last_checked"] = datetime.now()
                    if next_word == 1:
                        st.session_state["current_quiz_stats"]["incorrect"] += 1
                        st.session_state["current_quiz_stats"]["failed_pairs"][
                            st.session_state["current_quiz_pair"]] = data[st.session_state['current_quiz_pair']]['word']
                    elif next_word == 2:
                        st.session_state["current_quiz_stats"]["correct"] += 1

                    save_data(data)
                    st.session_state["current_quiz_pair"] = pick_pair()

                    if st.session_state["current_quiz_pair"] is None:
                        st.success("Quiz Complete!")
                        st.session_state["quiz_started"] = False
                        st.session_state["show_quiz_stats"] = True
                        st.session_state["current_quiz_stats"]["end_time"] = time.time()
                    st.session_state["show_quiz_answer"] = False
                    st.rerun()

            # Progress bar
            target = st.session_state["current_quiz_length"]
            progress = target - len(st.session_state["current_quiz"]) - 1 + (st.session_state["current_quiz_pair"] is None)
            st.progress(progress/target, f"Progress: {progress}/{target}")
    if st.session_state.get("show_quiz_stats", False):
        with st.container(border=True):
            stats = st.session_state["current_quiz_stats"]
            time_taken = stats["end_time"] - stats["start_time"]
            num_words = stats["correct"] + stats["incorrect"]

            st.markdown(f"### Quiz Complete {int(stats['correct']/num_words*100)}%")

            st.markdown(f"Time Taken: {int(time_taken//60)}m {round(time_taken%60)}s")
            st.progress(stats["correct"]/num_words, f"{stats['correct']}/{num_words} Correct")

            st.markdown("Incorrect Words: ")
            text = ", ".join([f"{key} -> {word}" for key, word in stats["failed_pairs"].items()])
            st.markdown(text)



def enter_words(data):
    st.markdown("# Enter Words")

    unused_pairs = []
    for key, val in data.items():
        if val["word"] == "":
            unused_pairs.append(key)

    st.markdown(f"There are {len(unused_pairs)} pairs without words")
    if len(unused_pairs) > 0:
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

    accounts_file = f"{DATA_PATH}/accounts.json"
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

if not(os.path.exists(DATA_PATH+"/")):
    os.mkdir(DATA_PATH)

if st.session_state.get("authenticated", False):
    app()
else:
    login_page()