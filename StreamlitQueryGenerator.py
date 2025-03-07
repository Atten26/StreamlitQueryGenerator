import streamlit as st
import pandas as pd
import zipfile
import io
import os
import pyperclip

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
            query_num = 1
            final_query = ''

    final_query = final_query[:-6]
    final_query = final_query + ')'

    df_final_query_temp = []
    df_final_query_temp.append({'ID': query_num, 'QUERY': final_query})
    df_final_query_temp = pd.DataFrame(df_final_query_temp)

    df_final_query = pd.concat([df_final_query, df_final_query_temp], ignore_index=True)

    return df_final_query

st.title('Query Upload and Execution App')

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
table_name = st.text_input("Table name")

if uploaded_file and table_name:
    excel_data = pd.read_excel(uploaded_file, dtype=str)
    df_queries = execute_query(excel_data, table_name)

    # Show only the query with ID 1
    query_id_1 = df_queries[df_queries['ID'] == 1]['QUERY'].values[0]
    st.text_area("Output queries: 1 of " + str(df_queries.shape[0]), query_id_1, height=200)

    # Button to copy the query to the clipboard
    if st.button('Copy the query'):
        pyperclip.copy(query_id_1)
        st.success("Query copied to clipboard!")

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
