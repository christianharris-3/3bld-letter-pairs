import random

import streamlit as st
st.set_page_config(layout="wide")
import json
import os

FILENAME = "pairs.json"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWX"

class Funcer:
    def __init__(self, func, args):
        self.func = lambda: func(args)

def load_data():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            data = json.load(f)
    else:
        data = {}
        for a in LETTERS:
            for b in LETTERS:
                if a != b:
                    data[a + b] = ""
    return data

def save_data(data):
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent="  ")

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
        if st.button("Show"):
            st.markdown(f"Word is \"{data[st.session_state['random_pair']]}\"")
        else:
            st.markdown(f"Word is -----")
        if st.button("Next"):
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

data = load_data()

cols = st.columns(3)
search = cols[0].button("Search", width="stretch")
quiz = cols[1].button("Quiz", width="stretch")
enter = cols[2].button("Enter Words", width="stretch")

if search: st.session_state["current_page"] = "search"
if quiz: st.session_state["current_page"] = "quiz"
if enter: st.session_state["current_page"] = "enter_words"

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

