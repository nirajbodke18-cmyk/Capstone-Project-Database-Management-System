import streamlit as st
import numpy as np
import pandas as pd
import sqlite3 
import hashlib
import os
import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

conn = sqlite3.connect('data.db')
c = conn.cursor()


# Function to create a connection to the SQLite database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     project_title TEXT,
                     domain TEXT,
                     student_name TEXT,
                     year TEXT,
                     guide_name TEXT,
                     github_link TEXT,
                     abstract TEXT)''')
        conn.commit()
    except sqlite3.Error as e:
        print(e)
        
def insert_project(conn, project_data):
    sql = ''' INSERT INTO projects(project_title, domain, student_name, year, guide_name, github_link, abstract)
              VALUES(?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, project_data)
    conn.commit()
    return cur.lastrowid
    
def get_all_projects(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects")
    rows = cur.fetchall()
    return rows

def get_filtered_projects(conn, domain):
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE domain=?", (domain,))
    rows = cur.fetchall()
    return rows

def calculate_similarity(new_project, existing_projects):
    new_abstract = new_project['abstract']
    existing_abstracts = [proj[7] for proj in existing_projects]  # Abstract is at index 7

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([new_abstract] + existing_abstracts)
    similarity_scores = cosine_similarity(vectors[0], vectors[1:])
    max_similarity_index = similarity_scores.argmax()
    return max_similarity_index, similarity_scores.flatten()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT, user_type TEXT)')

def add_userdata(username,password, user_type):
    c.execute('INSERT INTO userstable(username,password, user_type) VALUES (?,?,?)',(username,password, user_type))
    conn.commit()

def login_user(username,password, user_type):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ? AND user_type = ?',(username,password, user_type))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

def main():
    st.subheader('Capstone Project Database Management System')
    conn = create_connection("data.db")
    if conn is not None:
        create_table(conn)
    else:
        st.error("Error: Unable to connect to database.")
    st.sidebar.subheader("K. K. Wagh Polytechnic, Nashik")
    st.sidebar.subheader("Department of Computer Technology")
    menu = ["Home","Login","SignUp"]
    choice = st.sidebar.selectbox("Menu",menu)

    if choice == "Home":
        st.image("Project.png")
        st.markdown('<div style="text-align: justify;">The Capstone Project Database Management System is a crucial tool designed to streamline the process of managing student projects effectively. One of its innovative features involves employing a similarity score mechanism to determine whether a project has been previously completed by a student or not. This is achieved by allowing students to upload abstracts of their proposed projects, which are then analyzed against existing entries in the database. Through advanced algorithms, the system calculates a similarity score, indicating the extent to which the proposed project resembles those already completed. This functionality serves to prevent redundancy and promote originality in student projects, ensuring that each endeavor contributes meaningfully to the academic landscape. </div>', unsafe_allow_html=True)
    elif choice == "Login":
        user_type = st.sidebar.selectbox("User Type",['Admin(Staff)','User'])
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password",type='password')
        if st.sidebar.checkbox("Login/Logout"):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username,check_hashes(password,hashed_pswd), user_type)
            if result:
                st.sidebar.success("Login Success")
                if(user_type == 'Admin(Staff)'):
                    menu = ["Add Project","Search Project"]
                else:
                    menu = ["Search Project","Show Projects"]
                choice = st.selectbox("Menu",menu)
                if choice == "Add Project":
                    st.subheader("Register a New Project")
                    project_title = st.text_input("Project Title")
                    domain = st.selectbox('Select Domain:', ['IoT', 'AI/ML', 'Image Processing', 'Embedded', 'Block chain', 'Security', 'NLP', 'Robotics'])
                    student_name = st.text_input("Student Name")
                    year = st.text_input("Year")
                    guide_name = st.text_input("Guide Name")
                    github_link = st.text_input("GitHub Link")
                    abstract = st.text_area("Abstract (300-500 words)")

                    if st.button("Submit"):
                        if len(abstract.split()) < 50:
                            st.warning("Abstract should be between 300 and 500 words.")
                        else:
                            project_data = (project_title, domain, student_name, year, guide_name, github_link, abstract)
                            insert_project(conn, project_data)
                            st.success("Project Registered Successfully!")
                    
                elif choice == "Search Project":
                    #st.subheader("Registered Projects")
                    projects = get_all_projects(conn)
                    #for project in projects:
                    #    st.write(project)

                    # Page: Check Similarity
                    st.subheader("Check Similarity with Existing Projects")
                    new_abstract = st.text_area("Enter Abstract of New Project")
                    if st.button("Check"):
                        if len(new_abstract.split()) < 50:
                            st.warning("Abstract should be between 300 and 500 words.")
                        else:
                            new_project = {'abstract': new_abstract}
                            max_similarity_index, similarity_scores = calculate_similarity(new_project, projects)
                            print(similarity_scores[max_similarity_index])
                            if float(similarity_scores[max_similarity_index]) > 0.20:
                                st.write("**Highest Similarity Score:**", (similarity_scores[max_similarity_index])*100,"%")
                                st.write("**Details of the Project with Highest Similarity:**")
                                st.write("**Project Title:**", projects[max_similarity_index][1])
                                st.write("**Category:**", projects[max_similarity_index][2])
                                st.write("**Lead Developer:**", projects[max_similarity_index][3])
                                st.write("**Year:**", projects[max_similarity_index][4])
                                st.write("**Supervisor:**", projects[max_similarity_index][5])
                                st.write("**GitHub Repository:**", projects[max_similarity_index][6])
                            else:
                                st.error("No Matching Projects Found...")
                elif choice == "Show Projects":
                    domain = st.selectbox('Select Domain:', ['All','IoT', 'AI/ML', 'Image Processing', 'Embedded', 'Block chain', 'Security', 'NLP', 'Robotics'])
                    if domain !='All':
                        data = get_filtered_projects(conn, domain)
                        if len(data) > 0:
                            df = pd.DataFrame(data, columns=["No","project_title", "domain", "student_name", "year", "guide_name", "github_link", "abstract"])
                            df.drop(columns=df.columns[0], inplace=True)
                            df.drop(columns=df.columns[6], inplace=True)
                            st.write(df)
                        else:
                            st.warning("No Projects found for this domain...")
                    else:
                        data = get_all_projects(conn)
                        df = pd.DataFrame(data, columns=["No","project_title", "domain", "student_name", "year", "guide_name", "github_link", "abstract"])
                        df.drop(columns=df.columns[0], inplace=True)
                        df.drop(columns=df.columns[6], inplace=True)
                        st.write(df)
                        
            else:
                    st.sidebar.warning("Incorrect Username/Password")
        else:
                st.sidebar.warning("Please Enter Valid Credentials...")
    elif choice == "SignUp":
        st.subheader("Create New Account")
        user_type = st.selectbox("User Type",['Admin(Staff)','User'])
        new_user = st.text_input("Username")
        new_password = st.text_input("Password",type='password')
        if st.button("Signup"):
            if(new_user!='' and new_password!=''):
                create_usertable()
                add_userdata(new_user,make_hashes(new_password), user_type)
                st.success("You have successfully created a valid Account")
                st.info("Go to Login Menu to login")
            else:
                st.warning("Please Enter Valid Credentials...")

if __name__ == '__main__':
	main()
