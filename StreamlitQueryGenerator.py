import streamlit as st
import pandas as pd
import zipfile
import io
import os

import pathlib  # Per lavorare con percorsi di file
import logging  # Per registrare informazioni di log
import shutil   # Per copiare e fare backup dei file
from bs4 import BeautifulSoup  # Per analizzare e modificare il file HTML



def execute_query(excel_data, table_name):
    insert_query = 'INSERT INTO '
    table_name = '"' + table_name + '"'
    insert_query = insert_query + table_name
    col_str = '('
    count_len_col = 0
    for col in excel_data.columns:
        count_len_col = count_len_col + len(' "' + col + '",')
        if count_len_col > 220:
            col_str = col_str + '\n "' + col + '",'
            count_len_col = 0
        else:
            col_str = col_str + ' "' + col + '",'

    col_str = col_str[:-1]
    col_str = col_str + ')'

    df_final_query = pd.DataFrame(columns=['ID', 'QUERY'])
    final_query = insert_query + col_str + '(\n'

    count_len_row = 0
    query_num = 1
    for index, row in excel_data.iterrows():
        if len(final_query) == 0:
            final_query = insert_query + col_str + '(\n'
        row_str = 'SELECT '
        count_len_row = 0
        for col in excel_data.columns:
            if str(row[col]) == 'nan':
                count_len_row = count_len_row + len('\'\',' + ' FROM DUMMY UNION\n')
                if count_len_row > 220:
                    row_str = row_str + '\n\'\','
                    count_len_row = 0
                else:
                    row_str = row_str + '\'\','
            else:
                if "'" in str(row[col]):
                    value = str(row[col]).replace("'","''")
                else:
                    value = str(row[col])
                count_len_row = count_len_row + len('\'' + value + '\',' + ' FROM DUMMY UNION\n')
                if count_len_row > 220:
                    row_str = row_str + '\n\'' + value + '\','
                    count_len_row = 0
                else:
                    row_str = row_str + '\'' + value + '\','

        row_str = row_str[:-1]
        row_str = row_str + ' FROM DUMMY UNION\n'
        final_query = final_query + row_str
        if len(final_query) > 490000:
            final_query = final_query[:-6]
            final_query = final_query + ')'

            df_final_query_temp = []
            df_final_query_temp.append({'ID': query_num, 'QUERY': final_query})
            df_final_query_temp = pd.DataFrame(df_final_query_temp)

            df_final_query = pd.concat([df_final_query, df_final_query_temp], ignore_index=True)
            query_num = query_num + 1
            final_query = ''

    final_query = final_query[:-6]
    final_query = final_query + ')'

    df_final_query_temp = []
    df_final_query_temp.append({'ID': query_num, 'QUERY': final_query})
    df_final_query_temp = pd.DataFrame(df_final_query_temp)

    df_final_query = pd.concat([df_final_query, df_final_query_temp], ignore_index=True)

    return df_final_query

# Inizio Main
adsense_url = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"
GA_AdSense = """
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
    <ins class="adsbygoogle"
        style="display:block; width:300px; height:250px;"
        data-ad-client="ca-pub-4818294403178989"
        data-full-width-responsive="true"></ins>
    <script>
        (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
"""

# Insert the script in the head tag of the static template inside your virtual
index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
logging.info(f'editing {index_path}')
soup = BeautifulSoup(index_path.read_text(), features="html.parser")
if not soup.find("script", src=adsense_url): 
    # bck_index = index_path.with_suffix('.bck')
    # if bck_index.exists():
    #     shutil.copy(bck_index, index_path)  
    # else:
    #     shutil.copy(index_path, bck_index)  
    html = str(soup)
    new_html = html.replace('<head>', '<head>\n' + GA_AdSense)
    index_path.write_text(new_html)

# Sidebar per navigare tra le pagine
st.sidebar.title("Navigation")
pagina = st.sidebar.radio("Go to", ["Home", "Guide"])

if pagina == "Home":
    st.title('Insert Query Generator')

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    table_name = st.text_input("Table name")

    if uploaded_file and table_name:
        excel_data = pd.read_excel(uploaded_file, dtype=str)
        df_queries = execute_query(excel_data, table_name)

        # Show only the query with ID 1
        query_id_1 = df_queries[df_queries['ID'] == 1]['QUERY'].values[0]
        st.text_area("Output queries: 1 of " + str(df_queries.shape[0]), query_id_1, height=200)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for _, output_query in df_queries.iterrows():
                file_path = "QUERY_" + str(output_query["ID"]) + ".txt"
                zip_file.writestr(file_path, output_query["QUERY"])

        zip_buffer.seek(0)

        st.download_button(
            label="Download queries",
            data=zip_buffer,
            file_name="queries.zip",
            mime="application/zip"
        )
elif pagina == "Guide":
    st.title("User Guide for the Excel-to-SQL Query Generator")
    
    st.subheader("Overview")
    st.write(
        "This application allows users to generate SQL INSERT queries effortlessly "
        "by uploading an Excel file containing the data you want to insert into the database, "
        "naming the target database table, and following simple steps. "
        "The generated queries can then be executed in the DBACockpit to insert records into the desired table."
    )
    
    st.subheader("How to Use the Application")
    
    # Sezione con elenchi e spaziature corrette
    st.markdown("""
    1. **Upload the Excel File**:
        - Prepare your Excel file:
            - The first row **must** contain the column headers (e.g., `ID`, `Name`, `Date`).
            - The subsequent rows should include the data records to be inserted.
        - Upload the file through the designated upload button in the application.

    2. **Provide the Table Name**:
        - Specify the name of the target database table in the input field.

    3. **Generate SQL Queries**:
        - Press **Enter**.
        - The application will process your data and generate one or more SQL INSERT queries.
        - If multiple queries are generated, the first query will be displayed on the screen for easy preview.

    4. **Copy or Download Queries**:
        - To copy a single query:
            - Click on the query text, press **Ctrl + A**, then copy it using **Ctrl + C**.
        - To download all queries:
            - Use the **Download queries** button to save a ZIP file containing all generated queries.
            - **Note**: If the data volume is large, the application will divide it into multiple queries to ensure proper execution.

    5. **Execute the Queries in DBACockpit**:
        - Open the **dbacockpit** transaction on the SAP gui.
        - Navigate to:
            - `Diagnostics` > `SQL Editor`.
        - Paste the query into the designated input box.
        - Execute the query to insert the records into the table.
    """)

# Fine del codice
