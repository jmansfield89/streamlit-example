# from collections import namedtuple
# import altair as alt
# import math
# import pandas as pd
# import streamlit as st


# total_points = st.slider("Number of points in spiral", 1, 5000, 2000)
# num_turns = st.slider("Number of turns in spiral", 1, 100, 9)

# Point = namedtuple('Point', 'x y')
# data = []

# points_per_turn = total_points / num_turns

# for curr_point_num in range(total_points):
#     curr_turn, i = divmod(curr_point_num, points_per_turn)
#     angle = (curr_turn + 1) * 2 * math.pi * i / points_per_turn
#     radius = curr_point_num / total_points
#     x = radius * math.cos(angle)
#     y = radius * math.sin(angle)
#     data.append(Point(x, y))

# st.altair_chart(alt.Chart(pd.DataFrame(data), height=500, width=500)
#     .mark_circle(color='#0068c9', opacity=0.5)
#     .encode(x='x:Q', y='y:Q'))



# LIBRARY IMPORTS
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pandas as pd
import json
import urllib.request
import streamlit as st

# INPUTS
username = st.text_input("Enter your username: ")
password = st.text_input("Enter your password: ")

st.wait_for_user() #waits to execute any more code until user has input username and password.

# FUNCTIONS
# Create a session with AO3 to login with the username and password credentials provided
def return_session(username, password):
    s = requests.Session()
    payload = {
        "utf8": "%E2%9C%93",
        "user[login]": username,
        "user[password]": password,
        "commit": "Log+In"
    }
    site = s.get("https://archiveofourown.org")
    soup = BeautifulSoup(site.content, 'html.parser')
    payload["authenticity_token"] = soup.find("input", {"name": "authenticity_token"})['value']

    s.encoding = 'utf-8'
    s.post("https://archiveofourown.org/users/login", data=payload)
    return s

def get_pages(base_url, session):
    """
    Returns a list of page numbers on the base URL specified.
    """
    request = session.get(base_url)
    soup = BeautifulSoup(request.content, 'html.parser')
    pages = soup.find("ol", { "class": "pagination actions" })
    all_pages = []
    for li in pages.findAll('li'):
        all_pages.append(li.text)
    max_pages = int(all_pages[-2])
    return [*range(1, max_pages+1)]

def get_fics(base_url, session):
    """
    Returns a list of fanfics that were visited after the date specified.
    """
    while True:
        request = session.get(base_url)
        if request.status_code == 200:
            break
        else:
            time.sleep(300)
            continue

    soup = BeautifulSoup(request.content, 'html.parser')
    works = soup.find("ol", { "class": "reading work index group" })
    all_fics = []
    fics = works.findChildren("li", recursive=False)
    for i in fics:
        try:
            temp_fic = fic_check(i)
            if temp_fic['dt'] >= datetime(2022, 1, 1, 0, 0):  #specify date constrains here
                all_fics.append(temp_fic)
            else:
                break
        except:
            pass

    return all_fics

def fic_check(soup):
    """
    The fic_check function is used to extract specific information from a fanfiction
    on Archive of Our Own (AO3).

    Args:
        soup: A BeautifulSoup object representing the HTML of a fanfiction page on AO3.

    Returns:
        details: A dictionary containing the following information about the fanfiction:
            - title: the title of the fanfiction
            - author: the username of the author of the fanfiction
            - relationship: the relationship between the characters in the fanfiction
            - characters: a list of the characters in the fanfiction
            - word_count: the number of words in the fanfiction
            - tags: a list of the tags associated with the fanfiction
            - visited: the number of times the fanfiction has been visited
            - dt: the date and time the fanfiction was last visited.

    The fic_check function does this by using BeautifulSoup to parse the HTML of the 
    fanfiction page, and extracting the desired information from the page's elements. 
    For example, the title of the fanfiction is extracted by finding the h4 element 
    with the heading class, and then finding the a element within it. The dt field is 
    extracted by finding the h4 element with the viewed heading class, and then 
    parsing the date and time from the text within it.
    """

    heading = soup.find("h4", { "class": "heading"})
    
    #title - author created
    title_details = heading.findChildren("a", recursive=False)
    title_array = []
    for i in title_details:
        title_array.append(i.text)
    try:
        relationships = soup.find("li", { "class": "relationships" }).text.replace('\n', '')  #searches the HTML of the page for an element with the tag "li" and the class "relationships". 
            # Examples of relationships are:
            # Ted Lasso & Rebecca Welton - & indicates friendship, no romance, between chars
            # Ted Lasso/Rebecca Welton = / indicates romance between two chars
    except:
        relationships = "NONE"
    #characters - the author tags the characters in their story they are creating
    characters = soup.findAll("li", { "class": "characters" })
    character_array = []
    for i in characters:
        character_array.append(i.text)
    #freeform - tags outside of characters and relationships
    freeform_array = []
    freeforms = soup.findAll("li", { "class": "freeforms"})
    for i in freeforms:
        freeform_array.append(i.text)
    #visited
    visited = soup.find("h4", { "class": "viewed heading" }).text.replace('\n', '').replace(',', '')
    visited_list = visited.split()
    visited_count = visited_list[visited_list.index("Visited") + 1]
    if visited_count == "once":
        visited_count = 1
    else:
        visited_count = int(visited_count)
    #last visited
    last_visited = (' ').join(visited_list[2:5])
    #date timestamp
    dt = datetime.strptime(last_visited, '%d %b %Y')
    #word count
    word_count = int(soup.find("dd", { "class": "words"}).text.replace(',', ''))
    #details to return from the function
    details = {
        "title": title_array[0],
        "author": title_array[1],
        "relationship": relationships,
        "characters": character_array,
        "word_count": word_count,
        "tags": freeform_array,
        "visited": visited_count,
        "dt": dt
    }
    return details


def load_data(username, password):
    """
    Collects information about the fanfictions a user has read on Archive of Our Own (AO3).

    Args:
        username: A string representing the username of an AO3 user.
        password: A string representing the password of the AO3 user.

    Returns:
        all_fics: A list of dictionaries, where each dictionary contains information about 
        a fanfiction the user has read. The information includes the fanfiction's title, 
        author, relationship, characters, word count, tags, and date and time last visited.
    """
    session = return_session(username, password)
    base_url = f"https://archiveofourown.org/users/{username}/readings"
    all_pages = get_pages(base_url, session)
    all_fics = []
    all_breaks = []
    for i in all_pages:
        try:
            fics_url = base_url + f"?page={i}"
            fics = get_fics(fics_url, session)
            for fic in fics:
                all_fics.append(fic)
                if fic["dt"] >= datetime(2021, 1, 1):
                    all_breaks.append(False)
                else:
                    all_breaks.append(True)
            time.sleep(5)
        except:
            pass

        if True in all_breaks:
            print(f'BREAKING ON PAGE {i}')
            break

    return all_fics

def resolve_request(username, password):
    """
    This function is passed the username and password, then loads some raw data using 
    the load_data function to convert the raw data into a DataFrame, and then performs 
    some calculations and transformations to generate some summary statistics and other 
    information about the data. These calculations and manipulations include finding the 
    fanfic with the most visits, calculating the total number of words, the total number 
    of fanfics, the total number of reads, the top 5 most common relationships, the top 5 
    most common characters, and the top 5 most common tags. The function then returns 
    this information in a dictionary.
    """
    raw_data = load_data(username, password)
    frame = pd.DataFrame(raw_data)
    most_visited = frame[frame.visited == frame.visited.max()]

    total_words = frame.word_count.sum()
    total_fics = len(frame)
    total_reads = frame.visited.sum()

    all_relations = []
    all_characters = []
    all_tags = []

    for i in raw_data:
        all_relations.append(i["relationship"])
        for x in i["characters"]:
            all_characters.append(x)
        for x in i["tags"]:
            all_tags.append(x)

    relations_df = pd.DataFrame(all_relations)[0].value_counts().head(5).index.tolist()
    characters_df = pd.DataFrame(all_characters)[0].value_counts().head(5).index.tolist()
    tags_df = pd.DataFrame(all_tags)[0].value_counts().head(5).index.tolist()
    mv = {
        "title": most_visited.iloc[0].title,
        "author": most_visited.iloc[0].author,
        "count": int(most_visited.iloc[0].visited),
        "relations": relations_df,
        "characters": characters_df,
        "tags": tags_df
    }

    return_data = {
        "username": username,
        "total_words": int(total_words),
        "total_fics": int(total_fics),
        "total_reads": int(total_reads),
        "most_visited": mv,
    }
    return return_data



def main():
    """
    Main function for the app which calls all other functions to display the app.
    """
    # IMPORT DATA
    raw_data = load_data(username, password)
    df = pd.DataFrame(raw_data) #convert to dataframe

    # TRANSFORM DATA


    # DISPLAY DATA
    # Create a dropdown menu that allows the user to choose which columns to display
    selected_columns = st.selectbox(
    "Select the columns to display:",
    "title", "author", "relationship", "word_count") 

    # Use the st.dataframe function to display the selected columns of the DataFrame
    st.dataframe(df[selected_columns])

    # Calculate and display summary statistics about the data
    st.write("Total number of fanfics:", len(df))
    st.write("Total number of words:", df["word_count"].sum())
    st.write("Total number of visits:", df["visited"].sum())
    st.write("Fanfic with the most visits:", df["title"].iloc[df["visited"].idxmax()])

if __name__ == "__main__":
    main()
