from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import base64
import io
from collections import Counter
import re

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return words

def find_most_common_keywords(texts, top_n=1):
    all_keywords = [keyword for text in texts for keyword in extract_keywords(text)]
    keyword_counter = Counter(all_keywords)
    most_common_keywords = keyword_counter.most_common(top_n)
    return most_common_keywords

def search_and_save_to_excel(keyword, page_number, view_count, start_date_str, end_date_str):
    try:
        page_number = int(page_number) if page_number else 1  
        view_count = int(view_count) if view_count else 30  
        start_date = datetime.strptime(start_date_str, "%Y%m%d") if start_date_str else None  
        end_date = datetime.strptime(end_date_str, "%Y%m%d") if end_date_str else None  
    except ValueError:
        return "페이지 번호와 가져올 View 개수에 숫자를 입력하세요. 유효한 검색/경로를 정해주세요."

    if not keyword:
        return "검색어를 입력하세요. 유효한 검색을 정해주세요."

    base_url = "https://search.naver.com/search.naver?where=view&sm=tab_jum&query="
    
    if start_date and end_date:
        search_url = f"{base_url}{keyword}&start={page_number}&nso=p%3Afrom{start_date.strftime('%Y%m%d')}to{end_date.strftime('%Y%m%d')}"
    else:
        search_url = f"{base_url}{keyword}&start={page_number}"

    r = requests.get(search_url)
    soup = BeautifulSoup(r.text, "html.parser")

    items = soup.select(".title_link._cross_trigger")[:view_count]

    if not items:
        return f"해당 페이지({page_number})에는 검색 결과가 없습니다."

    data = {'View 번호': [], 'View 제목': [], 'View 링크': []}

    for e, item in enumerate(items, 1):
        news_link = item.get('href') if item.get('href') else '링크 없음'
        data['View 번호'].append(e)
        data['View 제목'].append(item.text)
        data['View 링크'].append(news_link)

    df = pd.DataFrame(data)

    view_texts = df['View 제목'].str.cat(sep=' ')
    most_common_keywords = find_most_common_keywords([view_texts], top_n=1)

    st.subheader(f"가장 많이 등장한 키워드: {most_common_keywords[0][0]}")

    st.dataframe(df)

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    b64 = base64.b64encode(excel_buffer.read()).decode()
    file_name = f"{keyword}_views_data.xlsx"
    download_link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{file_name}">데이터 다운로드</a>'
    
    st.markdown(download_link, unsafe_allow_html=True)
    
    return "데이터 다운로드 링크가 생성되었습니다."

def main():
    st.title("Naver Views Scraper")

    keywords = st.text_input("검색어 (쉼표로 구분):")
    keyword_list = [keyword.strip() for keyword in keywords.split(',')]

    page_number = st.text_input("페이지 번호(시작(1),지정 안할시 기본1):")
    view_count = st.text_input("가져올 View 개수(최대 30,지정 안할시 기본30):")
    start_date = st.text_input("시작 날짜(YYYYMMDD,지정 안해도 됩니다.):")
    end_date = st.text_input("종료 날짜(YYYYMMDD,지정 안해도 됩니다.):")

    search_button = st.button("검색 및 다운로드")

    if search_button:
        for keyword in keyword_list:
            st.subheader(f"'{keyword}'에 대한 결과")
            result = search_and_save_to_excel(keyword, page_number, view_count, start_date, end_date)
            st.write(result)
            st.markdown("---")  

if __name__ == "__main__":
    main()
