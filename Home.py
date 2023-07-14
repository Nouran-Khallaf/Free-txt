import streamlit as st
import base64
import os
import re
import string
import random
import pandas as pd
import numpy as np
import streamlit as st
from collections import Counter
import spacy
from spacy.tokens import Doc
from spacy.vocab import Vocab
import nltk
import io
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image as PilImage
from textblob import TextBlob
from nltk import word_tokenize, sent_tokenize, ngrams
from wordcloud import WordCloud, ImageColorGenerator
from nltk.corpus import stopwords
from labels import MESSAGES
from summarizer_labels import SUM_MESSAGES
from summa.summarizer import summarize as summa_summarizer
from langdetect import detect
nltk.download('punkt') # one time execution
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
import math
from pathlib import Path
from typing import List
import networkx as nx
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.express as px #### pip install plotly.express
from streamlit_option_menu import option_menu
import plotly.io as pio
from pyvis.network import Network
import streamlit.components.v1 as components
from langdetect import detect_langs
import json
import scattertext as tt
import spacy
from pprint import pprint
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

import shutil
from dateutil import parser
import streamlit.components.v1 as components
from io import StringIO
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode
from datetime import datetime
import plotly.graph_objects as go
import math
import random
from labels import MESSAGES
import tempfile
#########Download report
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image as ReportLabImage, Spacer, BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.units import inch


##Multilinguial 
import gettext
_ = gettext.gettext

def get_image_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')
def get_html_as_base64(path):
    with open(path, 'r') as file:
        html = file.read()
    return base64.b64encode(html.encode()).decode()

def save_uploaded_file(uploadedfile):
    with open(os.path.join("temp",uploadedfile.name),"wb") as f:
         f.write(uploadedfile.getbuffer())
    return st.success("Saved File:{} to temp".format(uploadedfile.name))

# Update with the Welsh stopwords (source: https://github.com/techiaith/ataleiriau)
en_stopwords = list(stopwords.words('english'))
cy_stopwords = open('welsh_stopwords.txt', 'r', encoding='iso-8859-1').read().split('\n') # replaced 'utf8' with 'iso-8859-1'
STOPWORDS = set(en_stopwords + cy_stopwords)
PUNCS = '''!→()-[]{};:'"\,<>./?@#$%^&*_~'''
pd.set_option('display.max_colwidth',None)

lang='en'
EXAMPLES_DIR = 'example_texts_pub'
 
nlp = spacy.load('en_core_web_sm-3.2.0')
def detect_language_file(text):
    try:
        return detect(text)
    except:
        return None

def handle_language_detection(data, column):
    english_data = None
    welsh_data = None

    data[column + '_Language'] = data[column].apply(detect_language_file)
    unique_languages = data[column + '_Language'].unique()

    if len(unique_languages) == 1:  # Only one language is present
        if 'en' in unique_languages:
            st.info(f'Your data in column {column} is English.')
        elif 'cy' in unique_languages:
            st.info(f'Your data in column {column} is Welsh.')
    else:  # More than one language is present
        if 'cy' in unique_languages and 'en' in unique_languages:
            st.info(f'Your data in column {column} contains both English and Welsh.')
            if st.button(f'Would you like to split the English and Welsh records in column {column}?'):
                english_data = data[data[column + '_Language'] == 'en']
                welsh_data = data[data[column + '_Language'] == 'cy']

                english_data_file = english_data.to_csv(index=False)
                welsh_data_file = welsh_data.to_csv(index=False)

                st.download_button(
                    "Download English data", 
                    english_data_file, 
                    file_name='english_data.csv', 
                    mime='text/csv'
                )
                st.download_button(
                    "Download Welsh data", 
                    welsh_data_file, 
                    file_name='welsh_data.csv', 
                    mime='text/csv'
                )

                st.info('Please upload each file separately for further processing.')
                return

    if 'cy' in unique_languages:
        if welsh_data is None:
            welsh_data = data[data[column + '_Language'] == 'cy']
        else:
            welsh_data = pd.concat([welsh_data, data[data[column + '_Language'] == 'cy']])

      

        st.info('Please upload each file separately for further processing.')

            

# reading example and uploaded files
@st.cache_data(experimental_allow_widgets=True)

def read_file(fname, file_source):
    file_name = fname if file_source=='example' else fname.name
    if file_name.endswith('.txt'):
        data = open(fname, 'r', encoding='cp1252').read().split('\n') if file_source=='example' else fname.read().decode('utf8').split('\n')
        data = pd.DataFrame.from_dict({i+1: data[i] for i in range(len(data))}, orient='index', columns = ['Reviews'])
        
    elif file_name.endswith(('.xls','.xlsx')):
        data = pd.read_excel(pd.ExcelFile(fname)) if file_source=='example' else pd.read_excel(fname)

    elif file_name.endswith('.tsv'):
        data = pd.read_csv(fname, sep='\t', encoding='cp1252') if file_source=='example' else pd.read_csv(fname, sep='\t', encoding='cp1252')
    else:
        return False, st.error(f"""**FileFormatError:** Unrecognised file format. Please ensure your file name has the extension `.txt`, `.xlsx`, `.xls`, `.tsv`.""", icon="🚨")
    column_list = ['date','Date','Dateandtime']
    for col in column_list:
    	if col in data.columns:
             data['Date'] = data[col].apply(lambda x: pd.to_datetime(x).strftime('%d/%m/%Y'))

    
    return True, data

def get_data(file_source='example'):
    try:
        if file_source=='example':
            example_files = sorted([f for f in os.listdir(EXAMPLES_DIR) if f.startswith('Reviews')])
            fnames = st.multiselect('Select example data file(s)', example_files, example_files[0])
            if fnames:
                return True, {fname:read_file(os.path.join(EXAMPLES_DIR, fname), file_source) for fname in fnames}
            else:
                return False, st.info('''**NoFileSelected:** Please select at least one file from the sidebar list.''', icon="ℹ️")
        
        elif file_source=='uploaded': # Todo: Consider a maximum number of files for memory management. 
            uploaded_files = st.file_uploader("Upload your data file(s)", accept_multiple_files=True, type=['txt','tsv','xlsx', 'xls'])
            if uploaded_files:
                return True, {uploaded_file.name:read_file(uploaded_file, file_source) for uploaded_file in uploaded_files}

            else:
                return False, st.info('''**NoFileUploaded:** Please upload files with the upload button or by dragging the file into the upload area. Acceptable file formats include `.txt`, `.xlsx`, `.xls`, `.tsv`.''', icon="ℹ️")
        else:
            return False, st.error(f'''**UnexpectedFileError:** Some or all of your files may be empty or invalid. Acceptable file formats include `.txt`, `.xlsx`, `.xls`, `.tsv`.''', icon="🚨")
    except Exception as err:
        return False, st.error(f'''**UnexpectedFileError:** {err} Some or all of your files may be empty or invalid. Acceptable file formats include `.txt`, `.xlsx`, `.xls`, `.tsv`.''', icon="🚨")


def select_columns(data, key):
    layout = st.columns([7, 0.2, 2, 0.2, 2, 0.2, 3, 0.2, 3])
    selected_columns = layout[0].multiselect('Select column(s) below to analyse', data.columns, help='Select columns you are interested in with this selection box', key= f"{key}_cols_multiselect")
    start_row=0
    if selected_columns: start_row = layout[2].number_input('Choose start row:', value=0, min_value=0, max_value=5)
    
    if len(selected_columns)>=2 and layout[4].checkbox('Filter rows?'):
        filter_column = layout[6].selectbox('Select filter column', selected_columns)
        if filter_column: 
            filter_key = layout[8].selectbox('Select filter key', set(data[filter_column]))
            data = data[selected_columns][start_row:].dropna(how='all')
            return data.loc[data[filter_column] == filter_key].drop_duplicates(), selected_columns
    else:
        return data[selected_columns][start_row:].dropna(how='all').drop_duplicates(), selected_columns

def detect_language(df):
    if df.empty:
        print("DataFrame is empty.")
        return None
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception as e:
            print("Failed to convert input to pandas DataFrame.")
            print("Error: ", e)
            return None
    detected_languages = []

    # Loop through all columns in the DataFrame
    for col in df.columns:
        # Check if the column data type is string or object
        if df[col].dtype not in ['string', 'object']:
            print(f"Skipping column {col} as it is not of type 'string' or 'object'.")
            continue

        # Loop through all rows in the column
        for text in df[col].fillna(''):
            # Ensure the text is string type
            text = str(text)

            # Use langdetect's detect_langs to detect the language of the text
            try:
                lang_probs =  detect_langs(text)
                if len(lang_probs) > 0:
                    most_probable_lang = max(lang_probs, key=lambda x: x.prob)
                    detected_languages.append(most_probable_lang.lang)
                else:
                    print(f"No languages detected in the text: {text}")
            except Exception as e:
                print(f"Error detecting language: {e}")

    # Count the number of occurrences of each language
    lang_counts = pd.Series(detected_languages).value_counts()

    # Determine the most common language in the DataFrame
    most_common_lang = lang_counts.index[0] if not lang_counts.empty else None

    if most_common_lang is None:
        print("No languages detected in the DataFrame.")

    return most_common_lang


@st.cache_resource()
def get_state():
    return {}

#######################session state
class SessionState(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


def get_session_state(**kwargs):
    # Get the session object from Streamlit.
    session_id = str(hash(st.session_state))
    
    # Get your SessionState object, or create it if it doesn't exist.
    if session_id not in st.session_state:
        st.session_state[session_id] = SessionState(**kwargs)

    return st.session_state[session_id]
###############################################Sentiment analysis###########################################
# --------------------Sentiments----------------------

###########Ployglot Welsh

def preprocess_text(text):
    # remove URLs, mentions, and hashtags
    text = re.sub(r"http\S+|@\S+|#\S+", "", text)

    # remove punctuation and convert to lowercase
    text = re.sub(f"[{re.escape(''.join(PUNCS))}]", "", text.lower())

    # remove stopwords
    text = " ".join(word for word in text.split() if word not in STOPWORDS)

    return text

# define function to analyze sentiment using Polyglot for Welsh language
@st.cache_data
def analyze_sentiment_welsh_polyglot(input_text):
    # preprocess input text and split into reviews
    reviews = input_text.split("\n")

    text_sentiment = []
    for review in reviews:
        review = preprocess_text(review)
        if review:
            text = Text(review, hint_language_code='cy')

            # calculate sentiment polarity per word
            sentiment_polarity_per_word = []
            for word in text.words:
                word_sentiment_polarity = word.polarity
                sentiment_polarity_per_word.append(word_sentiment_polarity)

            # calculate overall sentiment polarity
            overall_sentiment_polarity = sum(sentiment_polarity_per_word)

            # classify sentiment based on a threshold
            if overall_sentiment_polarity > 0.2:
                sentiment = "positive"
            elif overall_sentiment_polarity < -0.2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            text_sentiment.append((review, sentiment, overall_sentiment_polarity))

    return text_sentiment

from textblob import TextBlob
# define function to analyse sentiment using TextBlob for Welsh language
@st.cache_data
def analyse_sentiment_welsh(input_text):
    # preprocess input text and split into reviews
    reviews = input_text.split("\n")

    text_sentiment = []
    for review in reviews:
        review = preprocess_text(review)
        if review:
            # analyse sentiment using TextBlob
            text_blob = TextBlob(review)

            # calculate overall sentiment polarity
            overall_sentiment_polarity = text_blob.sentiment.polarity

            # classify sentiment based on a threshold
            if overall_sentiment_polarity > 0.2:
                sentiment = "positive"
            elif overall_sentiment_polarity < -0.2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            text_sentiment.append((review, sentiment, overall_sentiment_polarity))

    return text_sentiment


# --------------------Sentiments----------------------

###########Bert English
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
def preprocess_text(text):
    # remove URLs, mentions, and hashtags
    text = re.sub(r"http\S+|@\S+|#\S+", "", text)

    # remove punctuation and convert to lowercase
    text = re.sub(f"[{re.escape(''.join(PUNCS))}]", "", text.lower())

    # remove stopwords
    text = " ".join(word for word in text.split() if word not in STOPWORDS)

    return text

@st.cache_resource
def analyse_sentiment_txt(input_text,num_classes, max_seq_len=512):
    # load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
    model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

    # preprocess input text
    input_text = preprocess_text(input_text)

    if input_text:
        # Tokenize the input text
        tokens = tokenizer.encode(input_text, add_special_tokens=True, truncation=True)

        # If the token length exceeds the maximum, split into smaller chunks
        token_chunks = []
        if len(tokens) > max_seq_len:
            token_chunks = [tokens[i:i + max_seq_len] for i in range(0, len(tokens), max_seq_len)]
        else:
            token_chunks.append(tokens)

        # Process each chunk
        sentiment_scores = []
        for token_chunk in token_chunks:
            input_ids = torch.tensor([token_chunk])
            attention_mask = torch.tensor([[1] * len(token_chunk)])

            # Run the model
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            scores = outputs.logits.softmax(dim=1).detach().numpy()[0]
            sentiment_scores.append(scores)

        # Aggregate the scores
        avg_scores = np.mean(sentiment_scores, axis=0)
        sentiment_labels = ['Very negative', 'Negative', 'Neutral', 'Positive', 'Very positive']
        sentiment_index = avg_scores.argmax()
        sentiments =[]
        if num_classes == 3:
            sentiment_labels_3 = ['Negative', 'Neutral', 'Positive']
            if sentiment_index < 2:
                sentiment_index = 0  # Negative
            elif sentiment_index > 2:
                sentiment_index = 2  # Positive
            else:
                sentiment_index = 1  # Neutral
            sentiment_label = sentiment_labels_3[sentiment_index]
        else:
            sentiment_label = sentiment_labels[sentiment_index]

        sentiment_score = avg_scores[sentiment_index]
        sentiments.append((input_text, sentiment_label, sentiment_score))

    return sentiments
  


@st.cache_resource
def analyse_sentiment(input_text,num_classes, max_seq_len=512):
    # load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
    model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

    # preprocess input text and split into reviews
    reviews = input_text.split("\n")

    # initialize sentiment counters
    sentiment_counts = {'Negative': 0, 'Neutral': 0, 'Positive': 0}

    # predict sentiment for each review
    sentiments = []
    for review in reviews:
        original_review = review
        review = preprocess_text(review)
        if review:
            # Tokenize the review
            tokens = tokenizer.encode(review, add_special_tokens=True, truncation=True)

            # If the token length exceeds the maximum, split into smaller chunks
            token_chunks = []
            if len(tokens) > max_seq_len:
                token_chunks = [tokens[i:i + max_seq_len] for i in range(0, len(tokens), max_seq_len)]
            else:
                token_chunks.append(tokens)

            # Process each chunk
            sentiment_scores = []
            for token_chunk in token_chunks:
                input_ids = torch.tensor([token_chunk])
                attention_mask = torch.tensor([[1] * len(token_chunk)])

                # Run the model
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                scores = outputs.logits.softmax(dim=1).detach().numpy()[0]
                sentiment_scores.append(scores)

            # Aggregate the scores
            avg_scores = np.mean(sentiment_scores, axis=0)
            sentiment_labels = ['Very negative', 'Negative', 'Neutral', 'Positive', 'Very positive']
            sentiment_index = avg_scores.argmax()

            if num_classes == 3:
                sentiment_labels_3 = ['Negative', 'Neutral', 'Positive']
                if sentiment_index < 2:
                    sentiment_index = 0  # Negative
                elif sentiment_index > 2:
                    sentiment_index = 2  # Positive
                else:
                    sentiment_index = 1  # Neutral
                sentiment_label = sentiment_labels_3[sentiment_index]
            else:
                sentiment_label = sentiment_labels[sentiment_index]

            sentiment_score = avg_scores[sentiment_index]
            sentiments.append((original_review, sentiment_label, sentiment_score))

            # map 'Very negative' and 'Very positive' to 'Negative' and 'Positive'
            if sentiment_label in ['Very negative', 'Negative']:
                sentiment_counts['Negative'] += 1
            elif sentiment_label in ['Very positive', 'Positive']:
                sentiment_counts['Positive'] += 1
            else:
                sentiment_counts['Neutral'] += 1

    return sentiments, sentiment_counts

#####
import plotly.graph_objs as go
import plotly.io as pio

def plot_sentiment(df):
    # count the number of reviews in each sentiment label
    counts = df['Sentiment Label'].value_counts()

    # create the bar chart
    data = [
        go.Bar(
            x=counts.index,
            y=counts.values,
            text=counts.values,
            textposition='auto',
            marker=dict(color='rgb(63, 81, 181)')
        )
    ]

    # set the layout
    layout = go.Layout(
        title='Sentiment Analysis Results',
        xaxis=dict(title='Sentiment Label'),
        yaxis=dict(title='Number of Reviews'),
        plot_bgcolor='white',
        font=dict(family='Arial, sans-serif', size=14, color='black'),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # create the figure
    fig = go.Figure(data=data, layout=layout)
    #Save the plot to an image
    
    pio.write_image(fig, 'Bar_fig.png', format='png', width=800, height=600, scale=2)
    # show the plot
    st.plotly_chart(fig)
    buffer = io.StringIO()
    fig.write_html(buffer, include_plotlyjs='cdn')
    html_bytes = buffer.getvalue().encode()

    st.download_button(
            label='Download Bar Chart',
            data=html_bytes,
            file_name='Sentiment_analysis_bar.html',
            mime='text/html'
        )

from streamlit_plotly_events import plotly_events
import plotly.express as px

def plot_sentiment_pie(df):

    # count the number of reviews in each sentiment label
    counts = df['Sentiment Label'].value_counts()

    # calculate the proportions
    proportions = counts / counts.sum()

    # create the pie chart
    data = [
        go.Pie(
            labels=proportions.index,
            values=proportions.values,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Plotly)
        )
    ]

    # set the layout
    layout = go.Layout(
        title='Sentiment Analysis Results',
        plot_bgcolor='white',
        font=dict(family='Arial, sans-serif', size=14, color='black'),
        margin=dict(l=50, r=50, t=80, b=50),

    )

    fig = go.Figure(data=data, layout=layout)
    selected_points = plotly_events(fig, select_event=True)
    st.write('The figure displays the sentiment analysis of the data, you can press on any part of the graph to display the data')
    if selected_points:
        # filter the dataframe based on the selected point
        point_number = selected_points[0]['pointNumber']
        sentiment_label = proportions.index[point_number]
        df = df[df['Sentiment Label'] == sentiment_label]
        st.write(f'The proportion of " {sentiment_label} "')
        st.dataframe(df,use_container_width = True)
    
    # update the counts and proportions based on the filtered dataframe
    counts = df['Sentiment Label'].value_counts()
    proportions = counts / counts.sum()

    # update the pie chart data
    #fig.update_traces(labels=proportions.index, values=proportions.values)
    #Save the plot to an image
    pio.write_image(fig, 'Pie_fig.png', format='png', width=800, height=600, scale=2)
	
    buffer = io.StringIO()
    fig.write_html(buffer, include_plotlyjs='cdn')
    html_bytes = buffer.getvalue().encode()

    st.download_button(
        label='Download Pie Chart',
        data=html_bytes,
        file_name='Sentiment_analysis_pie.html',
        mime='text/html'
    )
    
nlp = spacy.load('en_core_web_sm-3.2.0')  
nlp.max_length = 9000000
######generate the scatter text 

def generate_scattertext_visualization(dfanalysis):
    # Get the DataFrame with sentiment analysis results
    df = dfanalysis
    # Parse the text using spaCy
    df['ParsedReview'] = df['Review'].apply(nlp)

    # Create a Scattertext Corpus
    corpus = tt.CorpusFromParsedDocuments(
        df,
        category_col="Sentiment Label",
        parsed_col="ParsedReview"
    ).build()
    
    
    term_scorer = tt.RankDifference()
    html = tt.produce_scattertext_explorer(
     corpus,
    category="Positive",
    category_name="Positive",   
    not_category_name='Negative_and_Neutral',
    not_categories=df["Sentiment Label"].unique().tolist(),
    minimum_term_frequency=5,
    pmi_threshold_coefficient=5,
    width_in_pixels=1000,
    metadata=df["Sentiment Label"],
    term_scorer=term_scorer
       ) 
    st.write('''
    The blue color representing Positive words and the red color representing
    Negatives  provides an easy to discern visual that allows the viewer to 
    quickly identify where differences exist in the text. The yellow 
    and orangish colors on the plot are an easy way to identify terms that 
    are most shared among the two classes. In this case as you go toward the top-right 
    of the chart you will find the most frequent of the most-shared terms and the bottom-left 
    is where you will find the least frequent of the most-shared terms.''')
    st.write('''
The score is on a scale of -1 to 1. Scores that are near zero have word frequencies 
that are similar for both classes (these are the yellow and orange dots). Scores that are near 1 
will have word frequencies dominated by the positive class (in blue). Scores that are near -1 
will have word frequencies dominated by the negative class (in red). 
The darker the color of red or blue indicates the closer the score is to -1 or 1.
''')

    st.write(''' As you scroll over dots on the plane you will see a pop up with statistics. 
    The statistics include the word frequency per 25,000 words for both classes. It also features a/** Scaled F-Score/**. 
    The word frequency metric is really easy to discern. That metric is what Scattertext uses as 
    the coordinates for each point. You can see that metric represented below with 195:71 per 25k words.
''')

    st.write('''
    When you use the query box or click on the word dot you are given metrics regarding 
    frequency broken down by per-word-frequency (as seen in the pop-up),
    AND you can also see frequency per-1,000-docs (doc in this case is a reddit post).

''')
    # Save the visualization as an HTML file
    with open("scattertext_visualization.html", "w") as f:
        f.write(html)
#----------------------------------------------------------summarisation----------------------------------------------------#	
summary=''
#####text_rank
def text_rank_summarize(article, ratio):
  return summa_summarizer(article, ratio=ratio)

# ------------------Summarizer--------------
def run_summarizer(input_text, num,lang='en'):

    chosen_ratio_2 = st.slider(SUM_MESSAGES[f'{lang}.sb.sl'],key = f"q{num}_1", min_value=10, max_value=50, step=10)/100

    #if st.button(SUM_MESSAGES[f'{lang}.button'],key = f'bb+ {num}'):
    #if input_text and input_text!='<Rhowch eich testun (Please enter your text...)>':
    summary = text_rank_summarize(input_text, ratio=chosen_ratio_2)
    if summary:
                st.write(text_rank_summarize(input_text, ratio=chosen_ratio_2))
    else:
                st.write(sent_tokenize(text_rank_summarize(input_text, ratio=0.5))[0])
    #else:
     #       st.write("Please enter your text in the above textbox")
    return summary      
            
            
#-------------Summariser--------------
def run_summarizertxt(input_text, lang='en'):

    chosen_ratio = st.slider(SUM_MESSAGES[f'{lang}.sb.sl']+ ' ',min_value=10, max_value=50, step=10)/100

    if st.button(SUM_MESSAGES[f'{lang}.button']):
        if input_text and input_text!='<Please enter your text...>' and len(input_text) > 10:
            summ = text_rank_summarize(input_text, ratio=chosen_ratio)
            if summ:
                summary = text_rank_summarize(input_text, ratio=chosen_ratio)
                st.write(summary)
            else:
                summary = sent_tokenize(text_rank_summarize(input_text, ratio=0.5))[0]
                st.write(summary)
        else:
            st.write("Please enter your text in the above textbox")
	
##-------------------------------------------Review analysis and illuistration------------------------------------		
class txtanalysis:
    def __init__(self, reviews):
        self.reviews = reviews

    def show_reviews(self, fname,tab):
        with tab:
            
            st.markdown(f'''📄 Viewing data: `{fname}`''')
            st.header('View and Filter all Data')
            df = pd.DataFrame(self.reviews)
            data = self.reviews
            st.write(data)
            #### interactive dataframe
            gb = GridOptionsBuilder.from_dataframe(data)
            gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
            gb.configure_side_bar() #Add a sidebar
            gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
            gridOptions = gb.build()

            grid_response = AgGrid(
    data,
    gridOptions=gridOptions,
    data_return_mode='AS_INPUT', 
    update_mode='MODEL_CHANGED', 
    fit_columns_on_grid_load=False,
    
    enable_enterprise_modules=True,
    height=350, 
    width='100%',
    reload_data=True
        )
            data = grid_response['data']
            selected = grid_response['selected_rows'] 
            
            df = pd.DataFrame(selected) #Pass the selected rows to a new dataframe df

		
            st.write('Total number of reviews: ', len(self.reviews))
	    
            column_list = ['date','Date','Dateandtime']
            for col in column_list:
                 if col in data.columns:
                      st.header('Filter Data based on Date range')
                      data['Date_sort'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')
                      data= data.sort_values('Date_sort')
                      start_date = data['Date'].min()
                      end_date = data['Date'].max()
                      start_d, end_d = st.select_slider('Select a range dates', 
						      options=data['Date'].unique(),
						      value=(str(start_date), str(end_date)))
                      from dateutil import parser
                      start_d= parser.parse(start_d)
                      start_d= datetime.strftime(start_d, '%d/%m/%y')
                      end_d= parser.parse(end_d)
                      end_d = datetime.strftime(end_d, '%d/%m/%y')
                      mask = (data['Date_sort'] >= start_d) & (data['Date_sort'] <= end_d)
                      filterdf = data.loc[mask]
                      st._legacy_dataframe(filterdf)
                      st.write('filtered  number of reviews: ', len(filterdf))
                      
    def show_wordcloud(self, fname,tab):
        ## st.info('Word cloud ran into a technical hitch and we are fixing it...Thanks for you patience', icon='😎')
        image_path=get_wordcloud(self.reviews, fname,tab)
	    
        return image_path
    
    def show_kwic(self, fname,tab):
        context = plot_kwic(self.reviews, fname,tab)
        return context
    def concordance_txt(input_data, tab ):
      with tab:
        st.header('Search Word')
        st.write('Please write a search word')

        search_word = st.text_input('', 'the')
        
        st.write('The graph below represents the searched word in the middle and the right and the left context for the word, the bigger the font size the more frequent the word is')
        st.write('The word frequency is represented by the weight in the tool tip')

      
        html.create_html_txt(search_word, input_data)

        HtmlFile = open("GFG-2.html", 'r')
        source_code = HtmlFile.read()
        st.download_button(
        "Download WordTree",
        data=source_code,
        file_name="GFG-2.html",
        mime="text/html",
        )
        print(source_code)
        components.html(source_code,height = 800)

    def concordance(self, fname,tab):
        with tab:
       	    st.header('Search Word')
            st.write('Please write a search word')
           
            search_word = st.text_input('', 'the')
            st.write('The graph below represents the searched word in the middle and the right and the left context for the word, the bigger the font size the more frequent the word is')
            st.write('The word frequency is represented by the weight in the tool tip')
            # Create a download button for the HTML file
         
            html.create_html(self, fname,search_word)
            HtmlFile = open("GFG-1.html", 'r')
            source_code = HtmlFile.read()
            st.download_button(
            "Download WordTree",
            data=source_code,
            file_name="GFG-1.html",
            mime="text/html",
        )
            print(source_code)
            components.html(source_code,height = 800)
            

#create function to get a color dictionary
def get_colordict(palette,number,start):
    pal = list(sns.color_palette(palette=palette, n_colors=number).as_hex())
    color_d = dict(enumerate(pal, start=start))
    return color_d

###ploty figure scale
def scatter(dataframe):
    df = px.data.gapminder()
    Plot_scatter = px.scatter(dataframe,y="freq", size="freq", color="word",
           hover_name="word", log_x=True, size_max=60)

    return(Plot_scatter)
#################Get the PyMusas tags ################
###read the PYmusas list
pymusaslist = pd.read_csv('data/Pymusas-list.txt', names= ['USAS Tags','Equivalent Tag'])
def Pymsas_tags(text):
    with open('cy_tagged.txt','w') as f:
    	f.write(text)
    lang_detected = detect(text)
    if lang_detected == 'cy':
        files = {
   	 'type': (None, 'rest'),
    	'style': (None, 'tab'),
    	'lang': (None, 'cy'),
    	'text': text,
		}
        response = requests.post('http://ucrel-api-01.lancaster.ac.uk/cgi-bin/pymusas.pl', files=files)
        data = response.text
        cy_tagged =pd.read_csv('cy_tagged.txt',sep='\t')
        cy_tagged['USAS Tags'] = cy_tagged['USAS Tags'].str.split('[,/mf]').str[0].str.replace('[\[\]"\']', '', regex=True)
        cy_tagged['USAS Tags'] = cy_tagged['USAS Tags'].str.split('+').str[0]
        merged_df = pd.merge(cy_tagged, pymusaslist, on='USAS Tags', how='left')
        merged_df.loc[merged_df['Equivalent Tag'].notnull(), 'USAS Tags'] = merged_df['Equivalent Tag'] 
        merged_df = merged_df.drop(['Equivalent Tag'], axis=1)
        
    elif lang_detected == 'en':
        nlp = spacy.load('en_core_web_sm-3.2.0')	
        english_tagger_pipeline = spacy.load('en_dual_none_contextual')
        nlp.add_pipe('pymusas_rule_based_tagger', source=english_tagger_pipeline)
        output_doc = nlp(text)
        cols = ['Text', 'Lemma', 'POS', 'USAS Tags']
        tagged_tokens = []
        for token in output_doc:
             tagged_tokens.append((token.text, token.lemma_, token.tag_, token._.pymusas_tags[0]))
        tagged_tokens_df = pd.DataFrame(tagged_tokens, columns = cols)
        tagged_tokens_df['USAS Tags'] = tagged_tokens_df['USAS Tags'].str.split('[/mf]').str[0].str.replace('[\[\]"\']|-{2,}|\+{2,}', '', regex=True)
        merged_df = pd.merge(tagged_tokens_df, pymusaslist, on='USAS Tags', how='left')
        merged_df.loc[merged_df['Equivalent Tag'].notnull(), 'USAS Tags'] = merged_df['Equivalent Tag'] 
        merged_df = merged_df.drop(['Equivalent Tag'], axis=1)
        tags_to_remove = ['Unmatched', 'Grammatical bin', 'Pronouns', 'Period']
        merged_df = merged_df[~merged_df['USAS Tags'].str.contains('|'.join(tags_to_remove))]

    return(merged_df['USAS Tags'])


    
###to upload image
def load_image(image_file):
	img = PilImage.open(image_file)
	return img

def get_wordcloud (data, key,tab):

    tab.markdown('''    
    ☁️ Word Cloud
    ''')
    
    layout = tab.columns([7, 1, 4])
    cloud_columns = layout[0].multiselect('Which column do you wish to view the word cloud from?', data.columns, list(data.columns), help='Select free text columns to view the word cloud', key=f"{key}_cloud_multiselect")
    input_data = ' '.join([' '.join([str(t) for t in list(data[col]) if t not in STOPWORDS]) for col in cloud_columns])
    # input_data = ' '.join([' '.join([str(t) for t in list(data[col]) if t not in STOPWORDS]) for col in data])
    for c in PUNCS: input_data = input_data.lower().replace(c,'')
    
    input_bigrams  = [' '.join(g) for g in nltk.ngrams(input_data.split(),2)]
    input_trigrams = [' '.join(g) for g in nltk.ngrams(input_data.split(),3)]
    input_4grams   = [' '.join(g) for g in nltk.ngrams(input_data.split(),4)]
    #'Welsh Flag': 'img/welsh_flag.png', 'Sherlock Holmes': 'img/holmes_silhouette.png',
    
    image_mask_2 = {'cloud':'img/cloud.png','Welsh Flag': 'img/welsh_flag.png', 'Sherlock Holmes': 'img/holmes_silhouette.png', 'national-trust':'img/national-trust-logo-black-on-white-silhouette.webp','Cadw':'img/cadw-clip.jpeg','Rectangle': None,'Tweet':'img/tweet.png','circle':'img/circle.png', 'Cadw2':'img/CadwLogo.png'}
    
   # Calculate the total number of words in the text
    Bnc_corpus=pd.read_csv('keness/Bnc.csv')
    #### Get the frequency list of the requested data using NLTK
    words = nltk.tokenize.word_tokenize(input_data)
    fdist1 = nltk.FreqDist(words)
    filtered_word_freq = dict((word, freq) for word, freq in fdist1.items() if not word.isdigit())
    column1 = list(filtered_word_freq.keys())
    column2= list(filtered_word_freq.values())
    word_freq = pd.DataFrame()
    word_freq['word']= column1
    word_freq['freq']= column2
    s = Bnc_corpus.loc[Bnc_corpus['word'].isin(column1)]
    word_freq = word_freq.merge(s, how='inner', on='word')
    #tab.write(word_freq)
    df = word_freq[['word','freq','f_Reference']]
    
    #tab2.subheader("upload mask Image")
    #image_file = tab2.file_uploader("Upload Images", type=["png","jpg","jpeg"])
    maskfile_2 = image_mask_2[tab.selectbox('Select Cloud shape:', image_mask_2.keys(), help='Select the shape of the word cloud')]
    colors =['grey','yellow','white','black','green','blue','red']
    outlines = tab.selectbox('Select cloud outline color ', colors, help='Select outline color word cloud')
    mask = np.array(PilImage.open(maskfile_2)) if maskfile_2 else maskfile_2
   
    
    doc = nlp(input_data)

    try:
        #creating wordcloud
        wc = WordCloud(
            # max_words=maxWords,
            stopwords=STOPWORDS,
            width=2000, height=1000,
		contour_color=outlines, contour_width = 1,
            relative_scaling = 0,
            mask=mask,
		
            background_color="white",
            font_path='font/Ubuntu-B.ttf'
        ).generate_from_text(input_data)
        

        # Allow the user to select the measure to use
	#measure = tab2.selectbox("Select a measure:", options=["Frequency","KENESS", "Log-Likelihood"])    
        all_words = []
        cloud_type = tab.selectbox('Choose Cloud category:', ['All words', 'Semantic Tags', 'Bigrams', 'Trigrams', '4-grams', 'Nouns', 'Proper nouns', 'Verbs', 'Adjectives', 'Adverbs', 'Numbers'], key=f"{key}_cloud_select")
        if cloud_type == 'All words':
             all_words = nltk.tokenize.word_tokenize(input_data)
             df = calculate_measures(df,'KENESS')
             all_words = df['word'].tolist()  # Update all_words from the DataFrame after calculation
        elif cloud_type == 'Bigrams':
            all_words = list(set([' '.join(g) for g in nltk.ngrams(input_data.split(),2)]))
        elif cloud_type == 'Trigrams':
            all_words = list(set([' '.join(g) for g in nltk.ngrams(input_data.split(),3)]))
        elif cloud_type == '4-grams':
            all_words = list(set([' '.join(g) for g in nltk.ngrams(input_data.split(),4)]))
        elif cloud_type in ['Nouns', 'Proper nouns', 'Verbs', 'Adjectives', 'Adverbs', 'Numbers']:
              pos_dict = {'Nouns': 'NOUN', 'Proper nouns': 'PROPN', 'Verbs': 'VERB', 'Adjectives': 'ADJ', 'Adverbs': 'ADV', 'Numbers': 'NUM'}
              all_words = [token.text for token in doc if token.pos_ == pos_dict[cloud_type]]
        elif cloud_type == 'Semantic Tags':
              tags = Pymsas_tags(input_data)
              all_words = list(tags.astype(str))
        else: 
            pass
        all_words = list(set(all_words))
        # Set a fixed number of columns
        n_cols = 5

        # Calculate number of rows
        n_rows = len(all_words) // n_cols
        if len(all_words) % n_cols:
             n_rows += 1
           # Create Select/Deselect all checkbox
        select_all = tab.checkbox('Select/Deselect all', value=True, key=f"{key}_select_all")

        deselected_words = []
        if select_all:
         for i in range(n_rows):
           cols = tab.columns(n_cols)
           for j in range(n_cols):
               idx = i * n_cols + j
               if idx < len(all_words):
                    word = all_words[idx]
                    checkbox = cols[j].checkbox(f'"{word}"', value=True, key=f"{key}_word_{word}")
                    if not checkbox:
                        deselected_words.append(word)
        else:
         for i in range(n_rows):
           cols = tab.columns(n_cols)
           for j in range(n_cols):
               idx = i * n_cols + j
               if idx < len(all_words):
                    word = all_words[idx]
                    checkbox = cols[j].checkbox(f'"{word}"', value=False, key=f"{key}_word_{word}")
                    if not checkbox:
                        deselected_words.append(word)
                        pass
         # Exclude deselected words from input_data
      
        if cloud_type == 'All words':
           df = df[~df['word'].isin(deselected_words)]
           wordcloud = wc.generate_from_frequencies(df.set_index('word')['KENESS'])
        else:
           freqs = Counter(all_words)
           deselected_freqs = {k: v for k, v in freqs.items() if k not in deselected_words}
           wordcloud = wc.generate_from_frequencies(deselected_freqs)

	    
        color = tab.radio('Select image colour:', ('Color', 'Black'), key=f"{key}_cloud_radio")
        img_cols = ImageColorGenerator(mask) if color == 'Black' else None
        plt.figure(figsize=[20,15])
        wordcloud_img = wordcloud.recolor(color_func=img_cols)
        plt.imshow(wordcloud_img, interpolation="bilinear")
        plt.axis("off")

        with tab:
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.pyplot()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                  wordcloud_img.to_file(tmpfile.name)
                  word_cloud_path = tmpfile.name

            img = PilImage.open(tmpfile.name)
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes = img_bytes.getvalue()
  

            # Add a download button in Streamlit to download the temporary image file
            st.download_button(
                label="Download Word Cloud Image",
                 data=img_bytes,
                 file_name="word_cloud.png",
                   mime="image/png",
                   )
    except ValueError as err:
        with tab:
            st.info(f'Oh oh.. Please ensure that at least one free text column is chosen: {err}', icon="🤨")
    if word_cloud_path is not None:
        return word_cloud_path
    else:
        return "Path not found or word cloud not created"
   ####generate a wordcloud based on Keness
#####English Keness
####load the Bnc Frequency list
def calculate_measures(df,measure):

    # Convert the frequency column to an integer data type
    df['freq'] = df['freq'].astype(int)

    # Calculate the total number of words in the text
    total_words = df['freq'].sum()
    # Calculate the total number of words in the reference corpus
    ref_words = 968267
   # Calculate the KENESS and log-likelihood measures for each word
    values = []
    for index, row in df.iterrows():
        observed_freq = row['freq']
        expected_freq = row['f_Reference'] * total_words / ref_words
        if measure == 'KENESS':
            value = math.log(observed_freq / expected_freq) / math.log(2)
        elif measure == 'Log-Likelihood':
            value = 2 * (observed_freq * math.log(observed_freq / expected_freq) +
                          (total_words - observed_freq) * math.log((total_words - observed_freq) / (total_words - expected_freq)))
        values.append(value)

    # Add the measure values to the dataframe
    df[measure] = values
    return df


# ---------------Checkbox options------------------
def checkbox_container(data):
    #st.markdown('What do you want to do with the data?')
    #layout = st.columns(2)
    #if layout[0].button('Select All'):
    for i in data:
          st.session_state['dynamic_checkbox_' + i] = True
          #st.experimental_rerun()
    

def get_selected_checkboxes():
    return [i.replace('dynamic_checkbox_','') for i in st.session_state.keys() if i.startswith('dynamic_checkbox_') and 
    st.session_state[i]]

#--------------Get Top n most_common words plus counts---------------
def getTopNWords(text, removeStops=False, topn=30):
    text = text.translate(text.maketrans("", "", string.punctuation))
    text = [word for word in text.lower().split()
                if word not in STOPWORDS] if removeStops else text.lower().split()
    return Counter(text).most_common(topn) 
#
#
#---------------------keyword in context ----------------------------
def get_kwic(text, keyword, window_size=1, maxInstances=10, lower_case=False):
    text = text.translate(text.maketrans("", "", string.punctuation))
    if lower_case:
        text = text.lower()
        keyword = keyword.lower()
    kwic_insts = []
    tokens = text.split()
    keyword_indexes = [i for i in range(len(tokens)) if tokens[i].lower() == keyword.lower()]
    for index in keyword_indexes[:maxInstances]:
        left_context = ' '.join(tokens[index-window_size:index])
        target_word = tokens[index]
        right_context = ' '.join(tokens[index+1:index+window_size+1])
        kwic_insts.append((left_context, target_word, right_context))
    return kwic_insts

#---------- get collocation ------------------------
def get_collocs(kwic_insts,topn=30):
    words=[]
    for l, t, r in kwic_insts:
        words += l.split() + r.split()
    all_words = [word for word in words if word not in STOPWORDS]
    return Counter(all_words).most_common(topn)

#----------- plot collocation ------------------------
from pyvis.network import Network
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
def plot_coll_15(keyword, collocs, expander, tab, output_file='network.html'):
    words, counts = zip(*collocs)
    top_collocs_df = pd.DataFrame(collocs, columns=['word', 'freq'])
    top_collocs_df.insert(1, 'source', keyword)
    top_collocs_df = top_collocs_df[top_collocs_df['word'] != keyword]  # remove row where keyword == word
    G = nx.from_pandas_edgelist(top_collocs_df, source='source', target='word', edge_attr='freq')
    n = max(counts)

    # Find the most frequent word
    most_frequent_word = max(collocs, key=lambda x: x[1])[0]

    # Create a network plot
    net = Network(notebook=True, height='750px', width='100%')

    # Adjust gravity based on frequency
    gravity = -200 * n / sum(counts)

    net.barnes_hut(gravity=gravity*30)  # Adjust gravity to control the spread and increase repulsion force

    # Add nodes
    for node, count in zip(G.nodes(), counts):
        node_color = 'green' if node == most_frequent_word else 'gray' if node == keyword else 'blue'
        node_size = 100 * count / n
        font_size = max(10, int(node_size / 2))  # Adjust font size based on node size, minimum size is 10
        net.add_node(node, label=node, color=node_color, size=node_size, font={'size': font_size, 'face': 'Arial'})

    # Add edges
    for source, target, freq in top_collocs_df[['source', 'word', 'freq']].values:
        if source in net.get_nodes() and target in net.get_nodes():
            net.add_edge(source, target, value=freq)

    # Save the visualization to an HTML file
    net.save_graph(output_file)


def plot_coll_14(keyword, collocs, expander, tab, output_file='network.html'):
    words, counts = zip(*collocs)
    top_collocs_df = pd.DataFrame(collocs, columns=['word', 'freq'])
    top_collocs_df.insert(1, 'source', keyword)
    top_collocs_df = top_collocs_df[top_collocs_df['word'] != keyword]  # remove row where keyword == word
    G = nx.from_pandas_edgelist(top_collocs_df, source='source', target='word', edge_attr='freq')
    n = max(counts)

    # Find the most frequent word
    most_frequent_word = max(collocs, key=lambda x: x[1])[0]

    
   # Create a network plot
    net = Network(notebook=True, height='750px', width='100%')

    # Adjust gravity based on frequency
    gravity = -200 * n / sum(counts)

    net.barnes_hut( gravity=gravity* 30)  # Adjust gravity to control the spread and increase repulsion force
  

    # Add nodes
    for node, count in zip(G.nodes(), counts):
        node_color = 'green' if node == most_frequent_word else 'gray' if node == keyword else 'blue'
        node_size = 100 * count / n
        font_size = max(6, int(node_size / 2))  # Adjust font size based on node size, minimum size is 6
        net.add_node(node, label=node,title=node ,color=node_color, size=node_size, font={'size': font_size, 'face': 'Arial'})

    # Add edges
    for source, target, freq in top_collocs_df[['source', 'word', 'freq']].values:
        if source in net.get_nodes() and target in net.get_nodes():
            net.add_edge(source, target, value=freq)
     # Save the visualization to an HTML file
    net.save_graph(output_file)
#----------- plot collocation ------------------------
def plot_collocation(keyword, collocs):
    words, counts = zip(*collocs)
    N, total = len(counts), sum(counts)
    plt.figure(figsize=(8,8))
    plt.xlim([-0.5, 0.5])
    plt.ylim([-0.5, 0.5])
    plt.plot([0],[0], '-o', color='blue',  markersize=25, alpha=0.7)
    plt.text(0,0, keyword, color='red', fontsize=14)
    for i in range(N):
        x, y = random.uniform((i+1)/(2*N),(i+1.5)/(2*N)), random.uniform((i+1)/(2*N), (i+1.5)/(2*N)) 
        x = x if random.choice((True, False)) else -x
        y = y if random.choice((True, False)) else -y
        plt.plot(x, y, '-og', markersize=counts[i]*10, alpha=0.3)
        plt.text(x, y, words[i], fontsize=12)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()

 #-------------------------- N-gram Generator ---------------------------

def gen_ngram(text, _ngrams=2, topn=10):
    if _ngrams==1:
	
        return getTopNWords(text, topn)
    ngram_list=[]
    for sent in sent_tokenize(text):
        for char in sent:
            if char in PUNCS: sent = sent.replace(char, "")
        ngram_list += ngrams(word_tokenize(sent), _ngrams)
	#.most_common(topn)
    ngram_counts = Counter(ngram_list).most_common(topn)
    sum_ngram_counts = sum([c for _, c in ngram_counts])
    return [(f"{' '.join(ng):27s}", f"{c:10d}", f"{c/sum_ngram_counts:.2f}%")
            for ng, c in ngram_counts]

def plot_kwic_txt(input_data,tab):
    tab.markdown('''💬 Word location in text''')
    #input_data = ' '.join([str(t) for t in df[0].split(' ') if t not in STOPWORDS])
    
    for c in PUNCS: input_data = input_data.lower().replace(c,'')
    
    try:
        with tab:
            topwords = [f"{w} ({c})" for w, c in getTopNWords(input_data, removeStops=True)]
            keyword = st.selectbox('Select a keyword:', topwords).split('(',1)[0].strip()
            window_size = st.slider('Select the window size:', 1, 10, 5)
            maxInsts = st.slider('Maximum number of instances :', 5, 50, 15, 5, key="slider2_key")
        # col2_lcase = st.checkbox("Lowercase?", key='col2_checkbox')
            kwic_instances = get_kwic(input_data, keyword, window_size, maxInsts, True)
        
        #keyword_analysis = tab6.radio('Analysis:', ('Keyword in context', 'Collocation'))
        #if keyword_analysis == 'Keyword in context':
            with st.expander('Keyword in Context'):
                kwic_instances_df = pd.DataFrame(kwic_instances,
                columns =['Left context', 'Keyword', 'Right context'])
                #kwic_instances_df.style.hide_index()
                
          
		   #### interactive dataframe
                gb = GridOptionsBuilder.from_dataframe(kwic_instances_df)
              
                gb.configure_column("Left context", cellClass ='text-right', headerClass= 'ag-header-cell-text' )
		
                gb.configure_column("Keyword", cellClass ='text-center', cellStyle= {
                   'color': 'red', 
                   'font-weight': 'bold'  })
                gb.configure_column("Right context", cellClass ='text-left')
                gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
                gb.configure_side_bar() #Add a sidebar
                gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
                gridOptions = gb.build()

                grid_response = AgGrid(
                kwic_instances_df,
                gridOptions=gridOptions,
                   data_return_mode='AS_INPUT', 
                   update_mode='MODEL_CHANGED', 
                   fit_columns_on_grid_load=False,
    
                   enable_enterprise_modules=True,
		   key='select_grid_2',
                   height=350, width= '100%',
                   columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                     reload_data=True
                      )
                data = grid_response['data']
                selected = grid_response['selected_rows'] 
                df = pd.DataFrame(selected)
            expander = st.expander('Collocation')
            with expander: #Could you replace with NLTK concordance later?
            # keyword = st.text_input('Enter a keyword:','staff')
                Word_type = st.selectbox('Choose word type:',
                 ['All words', 'Nouns', 'Proper nouns', 'Verbs', 'Adjectives', 'Adverbs', 'Numbers'])
                collocs = get_collocs(kwic_instances)
                colloc_str = ', '.join([f"{w} [{c}]" for w, c in collocs])
                words = nlp(colloc_str)
                st.write('The search word is placed in the middle, and the green circle represnts the most frequent word that appeared next to the search word, the darker blue the circle is the more frequent the word is, also the frequency represnted by the length and thickness of the lines attaching the words')
                st.write('The number represents the number of occurrences for each collocated word.')
                reset_button = st.button('Reset Graph')

                if reset_button:
                         plot_coll_14(keyword, collocs, expander, tab)
                if Word_type == 'All words':
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                    
                elif Word_type == 'Nouns':
                       
                       collocs = [token.text for token in words if token.pos_ == "NOUN"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Proper nouns':
                       collocs = [token.text for token in words if token.pos_ == "PROPN"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                
                elif Word_type == 'Verbs':
                       collocs = [token.text for token in words if token.pos_ == "VERB"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Adjectives':
                       collocs = [token.text for token in words if token.pos_ == "ADJ"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Adverbs':
                       collocs = [token.text for token in words if token.pos_ == "ADV"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Numbers':
                       collocs = [token.text for token in words if token.pos_ == "NUM"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                else: 
                      pass
		
             
                plot_coll_14(keyword, collocs, expander, tab,output_file='network_output.html')
                with open('network_output.html', 'r', encoding='utf-8') as f:
                         html_string = f.read()
                components.html(html_string, width=800, height=750, scrolling=True)
                with open('network_output.html', 'rb') as f:
                        html_bytes = f.read()
                st.download_button(
                  label='Download Collocation Graph',
                  data=html_bytes,
                  file_name='network_output.html',
                   mime='text/html'
                       )
	    #expander = st.expander('collocation')
           # with expander: #Could you replace with NLTK concordance later?
            # keyword = st.text_input('Enter a keyword:','staff')
               # collocs = get_collocs(kwic_instances) #TODO: Modify to accept 'topn'               
               # colloc_str = ', '.join([f"{w}[{c}]" for w, c in collocs])
               # st.write(f"Collocations for '{keyword}':\n{colloc_str}")
               # plot_coll_14(keyword, collocs,expander,tab)
                #plot_coll(keyword, collocs,expander,tab6)
    except ValueError as err:
        with tab:
                st.info(f'Please ensure that at least one free text column is chosen: {err}', icon="🤨")
    return kwic_instances_df
def plot_kwic(data, key,tab):
    tab.markdown('''💬 Word location in text''')
    
    # cloud_columns = st.multiselect(
        # 'Select your free text columns:', data.columns, list(data.columns), help='Select free text columns to view the word cloud', key=f"{key}_kwic_multiselect")
        
    # input_data = ' '.join([' '.join([str(t) for t in list(data[col]) if t not in STOPWORDS]) for col in cloud_columns])
    input_data = ' '.join([' '.join([str(t) for t in list(data[col]) if t not in STOPWORDS]) for col in data])
    nlp = spacy.load('en_core_web_sm-3.2.0')
    doc = nlp(input_data)
    for c in PUNCS: input_data = input_data.lower().replace(c,'')
    
    try:
        with tab:
            topwords = [f"{w} ({c})" for w, c in getTopNWords(input_data, removeStops=True)]
            st.write('The number with the word represents how many time this word appeared in the data')
            keyword = st.selectbox('Select keyword:', topwords).split('(',1)[0].strip()
            
            window_size = st.slider('Select window size:', 1, 10, 5)
            maxInsts = st.slider('Maximum number of instances:', 5, 50, 15, 5,  key="slider1_key")
        
            kwic_instances = get_kwic(input_data, keyword, window_size, maxInsts, True)
            with st.expander('Keyword_in_Context'):
                kwic_instances_df = pd.DataFrame(kwic_instances,
                    columns =['Left context', 'Keyword', 'Right context'])
                #kwic_instances_df.style.hide_index()
                
          
		   #### interactive dataframe
                gb = GridOptionsBuilder.from_dataframe(kwic_instances_df)
              
                gb.configure_column("Left context", cellClass ='text-right', headerClass= 'ag-header-cell-text' )
		
                gb.configure_column("Keyword", cellClass ='text-center', cellStyle= {
                   'color': 'red', 
                   'font-weight': 'bold'  })
                gb.configure_column("Right context", cellClass ='text-left')
                gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
                gb.configure_side_bar() #Add a sidebar
                gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
                gridOptions = gb.build()

                grid_response = AgGrid(
                kwic_instances_df,
                gridOptions=gridOptions,
                   data_return_mode='AS_INPUT', 
                   update_mode='MODEL_CHANGED', 
                   fit_columns_on_grid_load=False,
    
                   enable_enterprise_modules=True,
		   key='select_grid',
                   height=350, width= '100%',
                   columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                     reload_data=True
                      )
                data = grid_response['data']
                selected = grid_response['selected_rows'] 
                df = pd.DataFrame(selected) 
                #st.write(df)
		
            expander = st.expander('Collocation')
            with expander: #Could you replace with NLTK concordance later?
            # keyword = st.text_input('Enter a keyword:','staff')
                Word_type = st.selectbox('Choose word type:',
                 ['All words', 'Nouns', 'Proper nouns', 'Verbs', 'Adjectives', 'Adverbs', 'Numbers'], key= f"{key}_type_select")
                collocs = get_collocs(kwic_instances)
                colloc_str = ', '.join([f"{w} [{c}]" for w, c in collocs])
                words = nlp(colloc_str)
                st.write('The search word is placed in the middle, and the green circle represnts the most frequent word that appeared next to the search word, the darker blue the circle is the more frequent the word is, also the frequency represnted by the length and thickness of the lines attaching the words')
                st.write('The number represents the number of occurrences for each collocated word.')
                reset_button = st.button('Reset Graph')

                if reset_button:
                         plot_coll_14(keyword, collocs, expander, tab)
                if Word_type == 'All words':
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                    
                elif Word_type == 'Nouns':
                       
                       collocs = [token.text for token in words if token.pos_ == "NOUN"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Proper nouns':
                       collocs = [token.text for token in words if token.pos_ == "PROPN"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                
                elif Word_type == 'Verbs':
                       collocs = [token.text for token in words if token.pos_ == "VERB"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Adjectives':
                       collocs = [token.text for token in words if token.pos_ == "ADJ"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Adverbs':
                       collocs = [token.text for token in words if token.pos_ == "ADV"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                elif Word_type == 'Numbers':
                       collocs = [token.text for token in words if token.pos_ == "NUM"]
                       st.write(collocs)
                       st.write(f"Collocations for '{keyword}':\n{colloc_str}")
                else: 
                      pass
		
             
                plot_coll_14(keyword, collocs, expander, tab,output_file='network_output.html')
                with open('network_output.html', 'r', encoding='utf-8') as f:
                         html_string = f.read()
                components.html(html_string, width=800, height=750, scrolling=True)
                with open('network_output.html', 'rb') as f:
                        html_bytes = f.read()
                st.download_button(
                  label='Download Collocation Graph',
                  data=html_bytes,
                  file_name='network_output.html',
                   mime='text/html'
                       )
    
     
                
    except ValueError as err:
        with tab:
                st.info(f'Oh oh.. Please ensure that at least one free text column is chosen: {err}', icon="🤨")
    return kwic_instances_df
########## Generate the PDF#############
# Add a state variable to store the generated PDF data
generated_pdf_data = None
#---------------------------------------------------------------------------------------
def header(canvas, doc):
    # Add logo and title in a table
    logo_path = "img/FreeTxt_logo.png" 
    logo = PilImage.open(logo_path)
    logo_width, logo_height = logo.size
    aspect_ratio = float(logo_height) / float(logo_width)
    logo = ReportLabImage(logo_path, width=100, height=int(100 * aspect_ratio))
    title_text = "FreeTxt Analysis Report"
    title_style = ParagraphStyle("Title", fontSize=18, alignment=TA_LEFT)
    title = Paragraph(title_text, title_style)
    header_data = [[logo, title]]
    header_table = Table(header_data)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (1, 0), 'TOP'),
        ('LEFTPADDING', (1, 0), (1, 0), 1),
    ]))
    w, h = header_table.wrap(doc.width, doc.topMargin)
    header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h + 20)


#---------------------------------------------------------------------------------------

# Function to convert DataFrame to a CSV file and allow it to be downloaded
def download_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="Sentiment-analysis.csv">Download CSV File</a>'
    return href
#-----------------------------------------------------------------------------------------
# --- Initialising SessionState ---
if "load_state" not in st.session_state:
     st.session_state.load_state = False


###############PAGES########################################################################################

# ----------------
st.set_page_config(
     page_title='Welsh Free Text Tool',
     page_icon='🌐',
     layout="wide",
     initial_sidebar_state="expanded",
     menu_items={
         'Get Help': "https://ucrel.lancs.ac.uk/freetxt/",
         'Report a bug': "https://github.com/UCREL/welsh-freetxt-app/issues",
                 'About': '''## The FreeTxt/TestunRhydd tool 
         FreeTxt was developed as part of an AHRC funded collaborative
    FreeTxt supporting bilingual free-text survey  
    and questionnaire data analysis
    research project involving colleagues from
    Cardiff University and Lancaster University (Grant Number AH/W004844/1). 
    The team included PI - Dawn Knight;
    CIs - Paul Rayson, Mo El-Haj;
    RAs - Ignatius Ezeani, Nouran Khallaf and Steve Morris. 
    The Project Advisory Group included representatives from 
    National Trust Wales, Cadw, National Museum Wales,
    CBAC | WJEC and National Centre for Learning Welsh.
    -------------------------------------------------------   
    Datblygwyd TestunRhydd fel rhan o brosiect ymchwil 
    cydweithredol a gyllidwyd gan yr AHRC 
    ‘TestunRhydd: yn cefnogi dadansoddi data arolygon testun 
    rhydd a holiaduron dwyieithog’ sy’n cynnwys cydweithwyr
    o Brifysgol Caerdydd a Phrifysgol Caerhirfryn (Rhif y 
    Grant AH/W004844/1).  
    Roedd y tîm yn cynnwys PY – Dawn Knight; 
    CYwyr – Paul Rayson, Mo El-Haj; CydY 
    – Igantius Ezeani, Nouran Khallaf a Steve Morris.
    Roedd Grŵp Ymgynghorol y Prosiect yn cynnwys cynrychiolwyr 
    o Ymddiriedolaeth Genedlaethol Cymru, Amgueddfa Cymru,
    CBAC a’r Ganolfan Dysgu Cymraeg Genedlaethol.  
       '''
     }
 )

css = '''
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size:1.2rem;
    }
</style>
'''

st.markdown(css, unsafe_allow_html=True) 




###########################################Demo page#######################################################################
def demo_page():
    # Demo page content and layout
    # ...
    
    st.markdown("""
    <style>
        .stButton>button {
            display: inline-block;
            padding: 10px 20px;
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            outline: none;
            color: #000; /* Black text */
            background-color: #A9A9A9; /* Grey background */
            border: none;
            border-radius: 15px;
            box-shadow: 0 9px #999;
        }
        .stButton>button:hover {
            color: #ADD8E6; /* Light blue text when hovered */
            background-color: #808080; /* Darker grey background when hovered */
        }
        .stButton>button:active {
            background-color: #808080; /* Even darker grey background when clicked */
            box-shadow: 0 5px #666;
            transform: translateY(4px);
        }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
    f"""
    <div style="overflow: hidden; padding: 30px; background-color: lightgrey ;">	
	</div>"""
	, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        st.image("img/FreeTxt_logo_R.png", width=300) 
    #with col2:
        #st.markdown("<h1 style='text-align: center; margin-top: 0px;'>Demo</h1>", unsafe_allow_html=True)
    with col1:
        st.markdown("""
    <p style='text-align: left; 
              margin-top: 0px; 
              font-size: 80px; 
              color: #4a4a4a; 
              font-family: sans-serif; 
              text-shadow: 2px 2px #aaa;
              font-weight: normal;'>
    User Guide
    </p>""", unsafe_allow_html=True)



    st.markdown(
    f"""
<style>
.link-container a.menu-link {{
    float: left;
    color: #4a4a4a;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    font-size: 18px;
    margin: 0px;
    transition: 0.3s;
}}
.link-container a.menu-link:hover {{
    color: #2281EF;
    font-weight: bold;
    text-decoration: underline;
}}
#demo-link {{
    color: #2281EF; // This is the hyperlink color
    font-weight: bold;
    text-decoration: underline;
}}

</style>

<div class="link-container" style="overflow: hidden; padding: 10px; background-color: lightgrey;">
    <a  class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=home" target="_self">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg> Home
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=txtanalysis" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 13.5V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m12-3V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m-6-9V3.75m0 3.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 9.75V10.5"></path>
        </svg> Analysis
    </a>
    <a id="demo-link" class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=demo" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"></path>
        </svg>
        User Guide
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=about" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"></path>
        </svg>About
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=contact" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
           <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"></path>
        </svg>
        Contact Us
    </a>
</div>
""",
    unsafe_allow_html=True)

      
    st.markdown(
    f"""
    <style>
    .content-container {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        grid-template-rows: repeat(3, 1fr);
        gap: 10px;
        justify-items: center;
        align-items: center;
        padding: 10px;
        border-radius: 5px;
        background-color: white;
        color: white;
        text-align: center;
    }}
    
    .content-container > :nth-child(5) {{
        grid-column: 1 / -1;
    }}
    .a-image {{
        border-radius: 5px;
        transition: transform .2s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 1px rgba(0, 0, 0, 0.24);
        position: relative;
    }}
    .a-image:hover {{
        transform: scale(1.1);
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    }}
    .a-image:hover::after {{
        content: attr(title);
        position: absolute;
        top: -30px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.8);
        padding: 5px 10px;
        border-radius: 3px;
        font-size: 14px;
        color: white;
    }}
    </style>
    <div class="content-container">
        <div>
            <h3>Word Collocation</h3>
            <iframe class="a-image" src="data:text/html;base64,{get_html_as_base64('img/analysis/network_output.html')}" width="550" height="350" title="Network Output"></iframe>
        </div>
        <div>
            <h3>Word Context</h3>
            <img class="a-image" src="data:image/png;base64,{get_image_as_base64('img/analysis/Keyword.png')}" alt="Keyword in Context" width="500" title="Keyword in Context">
        </div>
        <div>
            <h3>Positive and Negative Ratio<h3>
            <iframe class="a-image" src="data:text/html;base64,{get_html_as_base64('img/analysis/Sentiment_analysis_pie.html')}" width="500" height="400" title="Sentiment Analysis Pie"></iframe>
        </div>
        <div>
            <h3>Word Cloud</h3>
            <img class="a-image" src="data:image/png;base64,{get_image_as_base64('img/analysis/word_cloud.png')}" alt="Wordcloud" width="500" title="Wordcloud">
        </div>
        <div>
            <h3>Text Visualisation</h3>
            <iframe class="a-image" src="data:text/html;base64,{get_html_as_base64('img/analysis/scattertext_visualization.html')}" width="900" height="500" title="Scattertext Visualization"></iframe>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

    st.markdown(
f"""
<style>
    .logo-container {{
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        border: 2px solid grey; 
        border-radius: 5px;  
    }}
    .logo {{
        width: 100px;
        height: 100px;
        margin: 10px;
        object-fit: contain;
        flex-grow: 1;
    }}
</style>
""",
unsafe_allow_html=True
)
    st.markdown(
    f"""
    <div class="logo-container">
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/cardiff.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Lancaster.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NTW.JPG')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Amgueddfa_Cymru_logo.svg.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Cadw.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NCLW.jpg')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/WJEC_CBAC_logo.svg.png')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/ukri-ahrc-square-logo.png')}" />
    </div>
    """,
    unsafe_allow_html=True,
     )
#######################################################################################################
##create the html file for the wordTree
class html:
    def __init__(self, reviews):
        self.reviews = reviews
    def create_html(self, fname,search_word):
    
    # Creating an HTML file to pass to google chart
        Func = open("GFG-1.html","w")
        sentences = ''.join(str(self.reviews.values.tolist()))
        st.write(sentences)
        Func.write('''<html>
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {packages:['wordtree']});
      google.charts.setOnLoadCallback(drawChart);

      function drawChart() {
        var data = google.visualization.arrayToDataTable(
          '''+
           sentences
             +
         ''' 
        );

        var options = {
          wordtree: {
            format: 'implicit',
            type: 'double',
            word:
            "'''          
            +
            search_word
            +
            '''
                        
            ,
            colors: ['red', 'black', 'green']
          }
        };

        var chart = new google.visualization.WordTree(document.getElementById('wordtree_basic'));
        chart.draw(data, options);
      }
    </script>
  </head>
  <body>
    <div id="wordtree_basic" style="width: 900px; height: 500px;"></div>
  </body>
</html>

    
        ''')
        Func.close()
    def create_html_txt(search_word, input_data):
    # Creating an HTML file to pass to google chart
      Func = open("GFG-2.html","w")
      lines = input_data.split('\n')
      input_data = pd.DataFrame(lines, columns=['reviews'])
      sentences = input_data['reviews'].values.tolist()

    # Convert to list of lists and remove empty sentences
      sentences = [[sentence] for sentence in sentences if sentence.strip()]

    # Convert list of lists to string
      sentences_string = str(json.dumps(sentences))

      st.write(sentences_string)
      Func.write('''<html>
     <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {packages:['wordtree']});
      google.charts.setOnLoadCallback(drawChart);

      function drawChart() {
        var data = google.visualization.arrayToDataTable(
          
           sentences
        
        );

        var options = {
          wordtree: {
            format: 'implicit',
            type: 'double',
            word:
            "'''          
            +
            search_word
            +
            '''"
                        
            ,
            colors: ['red', 'black', 'green']
          }
        };

        var chart = new google.visualization.WordTree(document.getElementById('wordtree_basic'));
        chart.draw(data, options);
      }
    </script>
  </head>
  <body>
    <div id="wordtree_basic" style="width: 900px; height: 500px;"></div>
  </body>
</html>

    
        ''')
      Func.close()

###########################################about page#######################################################################
def about_page():
    # About page content and layout
    # ...
    st.markdown(
    f"""
    <div style="overflow: hidden; padding: 30px; background-color: lightgrey ;">	
	</div>"""
	, unsafe_allow_html=True)
    st.markdown("""
    <style>
        .stButton>button {
            display: inline-block;
            padding: 10px 20px;
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            outline: none;
            color: #000; /* Black text */
            background-color: #A9A9A9; /* Grey background */
            border: none;
            border-radius: 15px;
            box-shadow: 0 9px #999;
        }
        .stButton>button:hover {
            color: #ADD8E6; /* Light blue text when hovered */
            background-color: #808080; /* Darker grey background when hovered */
        }
        .stButton>button:active {
            background-color: #808080; /* Even darker grey background when clicked */
            box-shadow: 0 5px #666;
            transform: translateY(4px);
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        st.image("img/FreeTxt_logo_R.png", width=300) 
    #with col2:
        #st.markdown("<h1 style='text-align: center; margin-top: 0px;'>Demo</h1>", unsafe_allow_html=True)
    with col1:
           st.markdown("""
    <p style='text-align: left; 
              margin-top: 0px; 
              font-size: 80px; 
              color: #4a4a4a; 
              font-family: sans-serif; 
              text-shadow: 2px 2px #aaa;
              font-weight: normal;'>
    About
    </p>""", unsafe_allow_html=True)


    st.markdown(
    f"""
<style>
.link-container a.menu-link {{
    float: left;
    color: #4a4a4a;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    font-size: 18px;
    margin: 0px;
    transition: 0.3s;
}}
.link-container a.menu-link:hover {{
    color: #2281EF;
    font-weight: bold;
    text-decoration: underline;
}}
#about-link {{
    color: #2281EF; // This is the hyperlink color
    font-weight: bold;
    text-decoration: underline;
}}
</style>

<div class="link-container" style="overflow: hidden; padding: 10px; background-color: lightgrey;">
    <a  class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=home" target="_self">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg> Home
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=txtanalysis" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 13.5V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m12-3V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m-6-9V3.75m0 3.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 9.75V10.5"></path>
        </svg> Analysis
    </a>
    <a  class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=demo" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"></path>
        </svg>
        User Guide
    </a>
    <a id = "about-link" class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=about" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"></path>
        </svg>About
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=contact" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
           <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"></path>
        </svg>
        Contact Us
    </a>
</div>
""",
    unsafe_allow_html=True)

    st.markdown(
    """
<div  padding: 10px;">
    <h2>The FreeTxt/TestunRhydd tool</h2>
    <p>FreeTxt was developed as part of an AHRC funded collaborative research project involving colleagues from Cardiff University and Lancaster University (Grant Number AH/W004844/1).</p>
    <p>The team included:</p>
    <ul>
        <li>PI - Dawn Knight</li>
        <li>CIs - Paul Rayson, Mo El-Haj</li>
        <li>RAs - Ignatius Ezeani, Nouran Khallaf and Steve Morris</li>
    </ul>
    <p>The Project Advisory Group included representatives from National Trust Wales, Cadw, National Museum Wales, CBAC | WJEC, and National Centre for Learning Welsh.</p>
</div>
""",
    unsafe_allow_html=True
)


    st.markdown(
f"""
<style>
    .logo-container {{
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        
    }}
    .logo {{
        width: 100px;
        height: 100px;
        margin: 10px;
        object-fit: contain;
        flex-grow: 1;
    }}
</style>
""",
unsafe_allow_html=True
)
    st.markdown(
    f"""
    <div class="logo-container">
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/cardiff.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Lancaster.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NTW.JPG')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Amgueddfa_Cymru_logo.svg.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Cadw.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NCLW.jpg')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/WJEC_CBAC_logo.svg.png')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/ukri-ahrc-square-logo.png')}" />
    </div>
    """,
    unsafe_allow_html=True,
     )
###########################################contact us  page#######################################################################
def contact_page():
    # contact page content and layout
    # ...
    st.markdown(
    f"""
    <div style="overflow: hidden; padding: 30px; background-color: lightgrey ;">	
	</div>"""
	, unsafe_allow_html=True)
    st.markdown("""
    <style>
        .stButton>button {
            display: inline-block;
            padding: 10px 20px;
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            outline: none;
            color: #000; /* Black text */
            background-color: #A9A9A9; /* Grey background */
            border: none;
            border-radius: 15px;
            box-shadow: 0 9px #999;
        }
        .stButton>button:hover {
            color: #ADD8E6; /* Light blue text when hovered */
            background-color: #808080; /* Darker grey background when hovered */
        }
        .stButton>button:active {
            background-color: #808080; /* Even darker grey background when clicked */
            box-shadow: 0 5px #666;
            transform: translateY(4px);
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        st.image("img/FreeTxt_logo_R.png", width=300) 
    #with col2:
        #st.markdown("<h1 style='text-align: center; margin-top: 0px;'>Demo</h1>", unsafe_allow_html=True)
    with col1:
           st.markdown("""
    <p style='text-align: left; 
              margin-top: 0px; 
              font-size: 80px; 
              color: #4a4a4a; 
              font-family: sans-serif; 
              text-shadow: 2px 2px #aaa;
              font-weight: normal;'>
    Contact us
    </p>""", unsafe_allow_html=True)



    st.markdown(
    f"""
<style>
.link-container a.menu-link {{
    float: left;
    color: #4a4a4a;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    font-size: 18px;
    margin: 0px;
    transition: 0.3s;
}}
.link-container a.menu-link:hover {{
    color: #2281EF;
    font-weight: bold;
    text-decoration: underline;
}}
#contact-link {{
    color: #2281EF; // This is the hyperlink color
    font-weight: bold;
    text-decoration: underline;
}}
</style>

<div class="link-container" style="overflow: hidden; padding: 10px; background-color: lightgrey;">
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=home" target="_self">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg> Home
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=txtanalysis" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 13.5V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m12-3V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m-6-9V3.75m0 3.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 9.75V10.5"></path>
        </svg> Analysis
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=demo" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"></path>
        </svg>
        User Guide
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=about" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"></path>
        </svg>About
    </a>
    <a id="contact-link" class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=contact" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
           <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"></path>
        </svg>
        Contact Us
    </a>
</div>
""",
    unsafe_allow_html=True)
    st.markdown(
    """
<div  padding: 10px;">
    
</div>
""",
    unsafe_allow_html=True
)


    st.markdown(
f"""
<style>
    .logo-container {{
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        
    }}
    .logo {{
        width: 100px;
        height: 100px;
        margin: 10px;
        object-fit: contain;
        flex-grow: 1;
    }}
</style>
""",
unsafe_allow_html=True
)
    st.markdown(
    f"""
    <div class="logo-container">
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/cardiff.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Lancaster.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NTW.JPG')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Amgueddfa_Cymru_logo.svg.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Cadw.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NCLW.jpg')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/WJEC_CBAC_logo.svg.png')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/ukri-ahrc-square-logo.png')}" />
    </div>
    """,
    unsafe_allow_html=True,
     )
#######################################################################################################
###########################################textbox_analysis_page#######################################################################
def textbox_analysis_page():
    state = get_state()
    st.markdown(
    f"""
    <div style="overflow: hidden; padding: 30px; background-color: lightgrey ;">	
	</div>"""
	, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
         
        st.image("img/FreeTxt_logo_R.png", width=300) 
        

    with col1:
        st.markdown("""
    <p style='text-align: left; 
              margin-top: 0px; 
              font-size: 80px; 
              color: #4a4a4a; 
              font-family: sans-serif; 
              text-shadow: 2px 2px #aaa;
              font-weight: normal;'>
    Text Analysis
    </p>""", unsafe_allow_html=True)


        st.markdown("""
    <style>
        .stButton>button {
            display: inline-block;
            padding: 10px 20px;
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            outline: none;
            color: #000; /* Black text */
            background-color: #A9A9A9; /* Grey background */
            border: none;
            border-radius: 15px;
            box-shadow: 0 9px #999;
        }
        .stButton>button:hover {
            color: #ADD8E6; /* Light blue text when hovered */
            background-color: #808080; /* Darker grey background when hovered */
        }
        .stButton>button:active {
            background-color: #808080; /* Even darker grey background when clicked */
            box-shadow: 0 5px #666;
            transform: translateY(4px);
        }
    </style>
    """, unsafe_allow_html=True)

    #selected3 = option_menu(None, ["Home", "Analysis",  "Demo"], 
   #     icons=['house', 'sliders2',  'gear'], 
    #    menu_icon="cast", default_index=1, orientation="horizontal",
    ##    styles={
     #       "container": {"padding": "0!important", "background-color": "#fafafa"},
    #        "icon": {"color": "orange", "font-size": "25px"}, 
     #       "nav-link": {"font-size": "25px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
    #        "nav-link-selected": {"background-color": "green"},
    #    }
   # )
    #st.session_state["selected3"] = selected3

    #if st.session_state["selected3"] == "Home":
     #   st.experimental_set_query_params(page="home")
        
   # elif st.session_state["selected3"] == "Analysis":
    #   st.experimental_set_query_params(page="analysis")
       
   # elif st.session_state["selected3"] == "Demo":
     #  st.experimental_set_query_params(page="demo")
       
        
    # Analysis page content and layout

    st.markdown(
    f"""
<style>
.link-container a.menu-link {{
    float: left;
    color: #4a4a4a;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    font-size: 18px;
    margin: 0px;
    transition: 0.3s;
}}
.link-container a.menu-link:hover {{
    color: #2281EF;
    font-weight: bold;
    text-decoration: underline;
}}
#analysis-link {{
    color: #2281EF; // This is the hyperlink color
    font-weight: bold;
    text-decoration: underline;
}}
</style>

<div class="link-container" style="overflow: hidden; padding: 10px; background-color: lightgrey;">
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=home" target="_self">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg> Home
    </a>
    <a id = "analysis-link" class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=txtanalysis" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 13.5V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m12-3V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m-6-9V3.75m0 3.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 9.75V10.5"></path>
        </svg> Analysis
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=demo" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"></path>
        </svg>
        User Guide
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=about" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"></path>
        </svg>About
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=contact" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
           <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"></path>
        </svg>
        Contact Us
    </a>
</div>
""",
    unsafe_allow_html=True)
    colm1, middle_colm, colm2 = st.columns([2, 1, 2])

    with colm1:
     st.header("Start analysing your text")
     text = st.text_area('Please paste your text here', '')

    with middle_colm:
      st.write('')
      st.write('')
      st.write('')
      st.write('')
      st.write('')
      st.write('')
      st.markdown("<h2 style='text-align: center; color: black;'>OR</h2>", unsafe_allow_html=True)

    with colm2:
      st.write("<br>"*4, unsafe_allow_html=True)
      st.markdown("""
<style>
.fancy-link {
    font-size: 35px; 
    font-family: Arial, sans-serif; 
    color: #4a4a4a; 
    background-color: #ddd; 
    padding: 10px 20px; 
    border-radius: 5px; 
    text-decoration: none;
    transition: background-color 0.3s ease, font-size 0.3s ease;
}
.fancy-link:hover {
    background-color: #bbb;
    font-size: 42px;
}
</style>

<a href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=analysis" 
   target = "_self"
   class = "fancy-link">
    Upload your own File
</a>
""", unsafe_allow_html=True)

       
	    
    #text = st.text_area("Your text", value=st.session_state.uploaded_text)

 

    dfanalysis = pd.DataFrame()


    if st.button('Analyse') or st.session_state.load_state:
        st.session_state.load_state = True
        area =[]
        if len(text) < 10:
            st.write("Please enter your text in the above textbox")
        else:
            area.append(text)    
            df = pd.DataFrame(area)
            df.columns =['Reviews']
            df = df['Reviews'].dropna(how='all').drop_duplicates()
            df = df.str.lower()
            if df.empty:
                    st.info('''** 🤨**: Please paste text to analyse.''', icon="ℹ️")
          
            else:
                              
                    input_data = ' '.join([str(t) for t in df[0].split(' ') if t not in STOPWORDS])
                     
                    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8= st.tabs(["📈 Meaning analysis",'💬 Keyword scatter','📝 Summarisation',"📈 Data View", "☁️ Keyword Cloud",'💬 Keyword in Context & Collocation', "🌳 Word Tree",'📥 Download pdf'])
                    
                    with tab1:
                        analysis_type = st.selectbox(
                                'How would you like to analyse the text?',
                                         ('analyse whole text', 'analyse sentence by sentence')
                                                              )
                        num_classes = st.radio('How do you want to categorize the sentiments?', ('3 Class Sentiments (Positive, Neutral, Negative)', '5 Class Sentiments (Very Positive, Positive, Neutral, Negative, Very Negative)'))
                        num_classes = 3 if num_classes.startswith("3") else 5

                        language = detect_language(df)  

                        if language == 'en':
                                  st.write("""
                                 The sentiment analysis is performed using the ["nlptown/bert-base-multilingual-uncased-sentiment"](https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment) model from Hugging Face. This model is trained on product reviews in multiple languages and utilizes the BERT architecture.

                                   As per the information on the Hugging Face model page, the accuracy of this model for sentiment analysis on English text is approximately 95%.
                               """)
                                  if analysis_type == 'analyse whole text':
                                      sentiments = analyse_sentiment_txt(input_data,num_classes)
                                  else:
                                    input_data = input_data.replace('.', '.\n')
                                    sentiments, sentiment_counts = analyse_sentiment(input_data, num_classes)
                                     

                                    net_sentiment = sentiment_counts['Positive'] - sentiment_counts['Negative']
                            
                                    st.header(f"Net sentiment: {net_sentiment}")
                                    if net_sentiment > 0:
                                         st.write(f'The net sentiment score of {net_sentiment} indicates that there are {net_sentiment} more positive sentiments than negative sentiments in the given text. This suggests that the overall sentiment of the text is positive.')
                                    elif net_sentiment < 0:
                                         st.write(f'The net sentiment score of {net_sentiment} indicates that there are {abs(net_sentiment)} more negative sentiments than positive sentiments in the given text. This suggests that the overall sentiment of the text is negative.')
                                    else:
                                        st.write('The net sentiment score is zero, which indicates an equal number of positive and negative sentiments. This suggests that the overall sentiment of the text is neutral.')


                                      
                        elif language == 'cy':
                                  if analysis_type == 'analyse whole text':
                                       sentiments = analyse_sentiment_txt(input_data,num_classes)
                                  else:
                                       input_data = input_data.replace('.', '.\n')
                                       sentiments = analyse_sentiment(input_data,num_classes)

                        dfanalysis = pd.DataFrame(sentiments, columns=['Review', 'Sentiment Label', 'Sentiment Score'])
                        plot_sentiment_pie(dfanalysis)
                        plot_sentiment(dfanalysis)
                      
                    with tab7:
                            input_data = input_data.replace('. ', '.\n').replace('.', '.\n')
                            txtanalysis.concordance_txt(input_data,tab7)
                    with tab2:
                      if not dfanalysis.empty:
                         #### interactive dataframe
                         gb = GridOptionsBuilder.from_dataframe(dfanalysis)
                         gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
                         gb.configure_side_bar() #Add a sidebar
                         #gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
                         gridOptions = gb.build()

                         grid_response = AgGrid(
                              dfanalysis,
                              gridOptions=gridOptions,
                               data_return_mode='AS_INPUT', 
                            update_mode='MODEL_CHANGED', 
                             fit_columns_on_grid_load=False,
    
                                  enable_enterprise_modules=True,
                             height=350, 
                              width='100%',
                              reload_data=True
                                                )
                         data = grid_response['data']
                         selected = grid_response['selected_rows'] 
                         dd = pd.DataFrame(selected) #Pass the selected rows to a new dataframe df
                         # Add a button to download the DataFrame as a CSV file
                         if st.button('Download CSV'):
                                    st.markdown(download_csv(dfanalysis), unsafe_allow_html=True)

			
			
			###scattertext
                         st.header('Scatter Text')
                                                  # Copy the scattertext_visualization.html to a temporary file
                         st.write('For better reprentation we recommend selecting 3 sentiment classes')
                         st.write('The 2,000 most sentiment-associated uni grams are displayed as points in the scatter plot. Their x- and y- axes are the dense ranks of their usage in positive vs negative and neutral respectively.')
                         generate_scattertext_visualization(dfanalysis)
                         scattertext_html_path='scattertext_visualization.html'
                         tmp_scattertext_path = "tmp_scattertext_visualization.html"
                         shutil.copyfile(scattertext_html_path, tmp_scattertext_path)

                         # Add a download button for the Scattertext HTML file
                         with open(tmp_scattertext_path, "rb") as file:
                                    scattertext_html_data = file.read()

                         st.download_button(
                             label="Download Scattertext Visualization HTML",
                             data=scattertext_html_data,
                          file_name="scattertext_visualization.html",
                            mime="text/html",
                                )
                         
                         
                         HtmlFile = open("scattertext_visualization.html", 'r', encoding='utf-8')
                         source_code = HtmlFile.read() 
                         print(source_code)
                         components.html(source_code,height = 1500,width = 800)   
       
                    with tab3:

                       st.write('This tool, adapted from the Welsh Summarization project, produces a basic extractive summary of the review text from the selected columns.')
                       summarized_text =run_summarizertxt(text)
	       ##show review
                    ##show review
            tab4.dataframe(df ,use_container_width=True)
        ###show word cloud
        
            tab5.markdown('''    
    ☁️ Word Cloud
    ''')
    
            layout = tab5.columns([7, 1, 4])
            #cloud_columns = layout[0].multiselect('Which column do you wish to view the word cloud from?', data.columns, list(data.columns), help='Select free text columns to view the word cloud', key=f"{key}_cloud_multiselect")
            #input_data = ' '.join([' '.join([str(t) for t in list(data[col]) if t not in STOPWORDS]) for col in cloud_columns])
    # input_data = ' '.join([' '.join([str(t) for t in list(data[col]) if t not in STOPWORDS]) for col in data])
            #input_data = ' '.join([str(t) for t in df[0].split(' ') if t not in STOPWORDS])
            for c in PUNCS: input_data = input_data.lower().replace(c,'')
    
            input_bigrams  = [' '.join(g) for g in nltk.ngrams(input_data.split(),2)]
            input_trigrams = [' '.join(g) for g in nltk.ngrams(input_data.split(),3)]
            input_4grams   = [' '.join(g) for g in nltk.ngrams(input_data.split(),4)]
    #'Welsh Flag': 'img/welsh_flag.png', 'Sherlock Holmes': 'img/holmes_silhouette.png',
    
            image_mask_2 = {'cloud':'img/cloud.png','Welsh Flag': 'img/welsh_flag.png', 'Sherlock Holmes': 'img/holmes_silhouette.png', 'national-trust':'img/national-trust-logo-black-on-white-silhouette.webp','Cadw':'img/cadw-clip.jpeg','Rectangle': None,'Tweet':'img/tweet.png','circle':'img/circle.png', 'Cadw2':'img/CadwLogo.png'}
    
   # Calculate the total number of words in the text
            Bnc_corpus=pd.read_csv('keness/Bnc.csv')
    #### Get the frequency list of the requested data using NLTK
            words = nltk.tokenize.word_tokenize(input_data)
            fdist1 = nltk.FreqDist(words)
            filtered_word_freq = dict((word, freq) for word, freq in fdist1.items() if not word.isdigit())
            column1 = list(filtered_word_freq.keys())
            column2= list(filtered_word_freq.values())
            word_freq = pd.DataFrame()
            word_freq['word']= column1
            word_freq['freq']= column2
            s = Bnc_corpus.loc[Bnc_corpus['word'].isin(column1)]
            word_freq = word_freq.merge(s, how='inner', on='word')
    #tab.write(word_freq)
            df = word_freq[['word','freq','f_Reference']]
    
    #tab2.subheader("upload mask Image")
    #image_file = tab5.file_uploader("Upload Images", type=["png","jpg","jpeg"])
            maskfile_2 = image_mask_2[tab5.selectbox('Select Cloud shape:', image_mask_2.keys(), help='Select the shape of the word cloud')]
            colors =['grey','yellow','white','black','green','blue','red']
            outlines = tab5.selectbox('Select cloud outline color ', colors, help='Select outline color word cloud')
            mask = np.array(PilImage.open(maskfile_2)) if maskfile_2 else maskfile_2
   
    
            doc = nlp(input_data)

            try:
        #creating wordcloud
               wc = WordCloud(
            # max_words=maxWords,
            stopwords=STOPWORDS,
            width=2000, height=1000,
		contour_color=outlines, contour_width = 1,
            relative_scaling = 0,
            mask=mask,
		
            background_color="white",
            font_path='font/Ubuntu-B.ttf'
        ).generate_from_text(input_data)
        

        # Allow the user to select the measure to use
	#measure = tab2.selectbox("Select a measure:", options=["Frequency","KENESS", "Log-Likelihood"])    
               all_words = []
               cloud_type = tab5.selectbox('Choose Cloud category:', ['All words', 'Semantic Tags', 'Bigrams', 'Trigrams', '4-grams', 'Nouns', 'Proper nouns', 'Verbs', 'Adjectives', 'Adverbs', 'Numbers'])
               if cloud_type == 'All words':
                 all_words = nltk.tokenize.word_tokenize(input_data)
                 df = calculate_measures(df,'KENESS')
                 all_words = df['word'].tolist() 
               elif cloud_type == 'Bigrams':
                  all_words = list(set([' '.join(g) for g in nltk.ngrams(input_data.split(),2)]))
               elif cloud_type == 'Trigrams':
                   all_words = list(set([' '.join(g) for g in nltk.ngrams(input_data.split(),3)]))
               elif cloud_type == '4-grams':
                   all_words = list(set([' '.join(g) for g in nltk.ngrams(input_data.split(),4)]))
               elif cloud_type in ['Nouns', 'Proper nouns', 'Verbs', 'Adjectives', 'Adverbs', 'Numbers']:
                   pos_dict = {'Nouns': 'NOUN', 'Proper nouns': 'PROPN', 'Verbs': 'VERB', 'Adjectives': 'ADJ', 'Adverbs': 'ADV', 'Numbers': 'NUM'}
                   all_words = [token.text for token in doc if token.pos_ == pos_dict[cloud_type]]
               elif cloud_type == 'Semantic Tags':
                   tags = Pymsas_tags(input_data)
                   all_words = list(tags.astype(str))
               else: 
                   pass
               all_words = list(set(all_words))
        # Set a fixed number of columns
               n_cols = 5

        # Calculate number of rows
               n_rows = len(all_words) // n_cols
               if len(all_words) % n_cols:
                    n_rows += 1

               deselected_words = []
               for i in range(n_rows):
                  cols = tab5.columns(n_cols)
                  for j in range(n_cols):
                     idx = i * n_cols + j
                     if idx < len(all_words):
                        word = all_words[idx]
                        checkbox = cols[j].checkbox(f'"{word}"', value=True, key=f"0_word_{word}")
                        if not checkbox:
                             deselected_words.append(word)
    
         # Exclude deselected words from input_data
      
               if cloud_type == 'All words':
                 df = df[~df['word'].isin(deselected_words)]
                 wordcloud = wc.generate_from_frequencies(df.set_index('word')['KENESS'])
               else:
                   freqs = Counter(all_words)
                   deselected_freqs = {k: v for k, v in freqs.items() if k not in deselected_words}
                   wordcloud = wc.generate_from_frequencies(deselected_freqs)

               color = tab5.radio('Select image colour:', ('Color', 'Black'))
               img_cols = ImageColorGenerator(mask) if color == 'Black' else None
               plt.figure(figsize=[20,15])
               wordcloud_img = wordcloud.recolor(color_func=img_cols)
               plt.imshow(wordcloud_img, interpolation="bilinear")
               plt.axis("off")

               with tab5:
                   st.set_option('deprecation.showPyplotGlobalUse', False)
                   st.pyplot()
                   with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                       wordcloud_img.to_file(tmpfile.name)
                       word_cloud_path = tmpfile.name

                   img = PilImage.open(tmpfile.name)
                   img_bytes = BytesIO()
                   img.save(img_bytes, format='PNG')
                   img_bytes = img_bytes.getvalue()
  

            # Add a download button in Streamlit to download the temporary image file
                   st.download_button(
                label="Download Word Cloud Image",
                 data=img_bytes,
                 file_name="word_cloud.png",
                   mime="image/png",
                   )
            except ValueError as err:
              with tab5:
                     st.info(f'Oh oh.. Please ensure that at least one free text column is chosen: {err}', icon="🤨")
        
            with tab6:
                plot_kwic_txt(input_data,tab6)
            with tab8:
                        checkbox = st.checkbox("Generate PDF report")
                        if checkbox:

                        # Create the PDF
                            buffer = BytesIO()
                            doc = BaseDocTemplate(buffer, pagesize=A4,topMargin=1.5 * inch, showBoundary=0)

    # Create the frame for the content
                            frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')

    
    # Create a PageTemplate with the header
                            template = PageTemplate(id='header_template', frames=frame, onPage=header)
                            doc.addPageTemplates([template])
                            elements = []

    
       
        

    # Add a spacer between header and input text
                            elements.append(Spacer(1, 20))
        # Build PDF
	
	
                            doc.build(elements)
                            buffer.seek(0)
                            generated_pdf_data = buffer.read()

   # Display the download button only after generating the report
                            if generated_pdf_data:
                              st.download_button("Download PDF", generated_pdf_data, "report_TextAnalysis.pdf", "application/pdf")

                             

###########################################Analysis page#######################################################################
def analysis_page():
    state = get_state()
    st.markdown(
    f"""
    <div style="overflow: hidden; padding: 30px; background-color: lightgrey ;">	
	</div>"""
	, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
         
        st.image("img/FreeTxt_logo_R.png", width=300) 
        

    with col1:
        st.markdown("""
    <p style='text-align: left; 
              margin-top: 0px; 
              font-size: 80px; 
              color: #4a4a4a; 
              font-family: sans-serif; 
              text-shadow: 2px 2px #aaa;
              font-weight: normal;'>
    Text Analysis
    </p>""", unsafe_allow_html=True)


        st.markdown("""
    <style>
        .stButton>button {
            display: inline-block;
            padding: 10px 20px;
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            outline: none;
            color: #000; /* Black text */
            background-color: #A9A9A9; /* Grey background */
            border: none;
            border-radius: 15px;
            box-shadow: 0 9px #999;
        }
        .stButton>button:hover {
            color: #ADD8E6; /* Light blue text when hovered */
            background-color: #808080; /* Darker grey background when hovered */
        }
        .stButton>button:active {
            background-color: #808080; /* Even darker grey background when clicked */
            box-shadow: 0 5px #666;
            transform: translateY(4px);
        }
    </style>
    """, unsafe_allow_html=True)

    #selected3 = option_menu(None, ["Home", "Analysis",  "Demo"], 
   #     icons=['house', 'sliders2',  'gear'], 
    #    menu_icon="cast", default_index=1, orientation="horizontal",
    ##    styles={
     #       "container": {"padding": "0!important", "background-color": "#fafafa"},
    #        "icon": {"color": "orange", "font-size": "25px"}, 
     #       "nav-link": {"font-size": "25px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
    #        "nav-link-selected": {"background-color": "green"},
    #    }
   # )
    #st.session_state["selected3"] = selected3

    #if st.session_state["selected3"] == "Home":
     #   st.experimental_set_query_params(page="home")
        
   # elif st.session_state["selected3"] == "Analysis":
    #   st.experimental_set_query_params(page="analysis")
       
   # elif st.session_state["selected3"] == "Demo":
     #  st.experimental_set_query_params(page="demo")
       
        
    # Analysis page content and layout

    st.markdown(
    f"""
<style>
.link-container a.menu-link {{
    float: left;
    color: #4a4a4a;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    font-size: 18px;
    margin: 0px;
    transition: 0.3s;
}}
.link-container a.menu-link:hover {{
    color: #2281EF;
    font-weight: bold;
    text-decoration: underline;
}}
#analysis-link {{
    color: #2281EF; // This is the hyperlink color
    font-weight: bold;
    text-decoration: underline;
}}
</style>

<div class="link-container" style="overflow: hidden; padding: 10px; background-color: lightgrey;">
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=home" target="_self">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg> Home
    </a>
    <a id = "analysis-link" class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=txtanalysis" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 13.5V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m12-3V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m-6-9V3.75m0 3.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 9.75V10.5"></path>
        </svg> Analysis
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=demo" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"></path>
        </svg>
        User Guide
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=about" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"></path>
        </svg>About
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=contact" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
           <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"></path>
        </svg>
        Contact Us
    </a>
</div>
""",
    unsafe_allow_html=True)
    #st.header("Start analysing your text")
    
    #if 'uploaded_text' in st.session_state:
      #  st.text_area("Your text", value=st.session_state.uploaded_text)
    if 'uploaded_file' in st.session_state:
        st.write(f"You've uploaded {st.session_state.uploaded_file.name}")
    #elif 'uploaded_text' not in st.session_state:
        #text = st.text_area("Paste your text here")
        #uploaded_file = st.file_uploader("Or upload a document", type=['txt', 'doc', 'docx', 'pdf'])

        #if text:
          #  st.session_state.uploaded_text = text


        #elif uploaded_file:
         #   save_uploaded_file(uploaded_file)
          #  st.session_state.uploaded_file = uploaded_file
    #####---------------get the data
    option = st.radio(MESSAGES[lang][0], (MESSAGES[lang][1], MESSAGES[lang][2]))
    if option == MESSAGES[lang][1]: input_data = get_data()
    elif option == MESSAGES[lang][2]: input_data = get_data(file_source='uploaded')
    else: pass
    status, data = input_data
    dfanalysis = pd.DataFrame()


    if status:
        filenames = list(data.keys())
	
       
        for i in range(len(filenames)):
          
                _, df = data[filenames[i]]
                
                df, selected_columns = select_columns(df, key=i)
                df = df.astype(str)
                # Convert all string values in the DataFrame to lowercase
                df = df.applymap(lambda s: s.lower())
                check_language = st.checkbox('Check file language')
                if check_language:
                      handle_language_detection(df,selected_columns[0])
                if df.empty:
                    st.info('''**NoColumnSelected 🤨**: Please select one or more columns to analyse.''', icon="ℹ️")
                else:
                        
                    input_text = '\n'.join(['\n'.join([str(t) for t in list(df[col]) if str(t) not in STOPWORDS and str(t) not in PUNCS]) for col in df])
                     
                    tab1, tab2,tab3,tab4,tab5,tab6,tab7,tab8= st.tabs(["📈 Meaning analysis",'💬 Keyword scatter','📝 Summarisation',"📈 Data View", "☁️ Keyword Cloud",'💬 Keyword in Context & Collocation', "🌳 Word Tree",'📥 Download pdf'])
                    with tab1:
                      if status:
                        num_classes = st.radio('How do you want to categorize the sentiments?', ('3 Class Sentiments (Positive, Neutral, Negative)', '5 Class Sentiments (Very Positive, Positive, Neutral, Negative, Very Negative)'))
                        num_classes = 3 if num_classes.startswith("3") else 5
                        language = detect_language(df)  
                        if language == 'en':
                            sentiments, sentiment_counts = analyse_sentiment(input_text, num_classes)
                            st.write("""
                           The sentiment analysis is performed using the ["nlptown/bert-base-multilingual-uncased-sentiment"](https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment) model from Hugging Face. This model is trained on product reviews in multiple languages and utilizes the BERT architecture.

                          As per the information on the Hugging Face model page, the accuracy of this model for sentiment analysis on English text is approximately 95%.
                               """)

                            net_sentiment = sentiment_counts['Positive'] - sentiment_counts['Negative']
                            
                            st.header(f"Net sentiment: {net_sentiment}")
                            if net_sentiment > 0:
                                 st.write(f'The net sentiment score of {net_sentiment} indicates that there are {net_sentiment} more positive sentiments than negative sentiments in the given text. This suggests that the overall sentiment of the text is positive.')
                            elif net_sentiment < 0:
                                 st.write(f'The net sentiment score of {net_sentiment} indicates that there are {abs(net_sentiment)} more negative sentiments than positive sentiments in the given text. This suggests that the overall sentiment of the text is negative.')
                            else:
                                 st.write('The net sentiment score is zero, which indicates an equal number of positive and negative sentiments. This suggests that the overall sentiment of the text is neutral.')

                            dfanalysis = pd.DataFrame(sentiments, columns=['Review', 'Sentiment Label', 'Sentiment Score'])
                            plot_sentiment_pie(dfanalysis)
                            plot_sentiment(dfanalysis)
                      
                        elif language == 'cy':
                            #sentiments = analyse_sentiment_welsh(input_text)
                            sentiments = analyse_sentiment(input_text,num_classes)
                            dfanalysis = pd.DataFrame(sentiments, columns=['Review', 'Sentiment Label', 'Sentiment Score'])
                            plot_sentiment_pie(dfanalysis)
                            plot_sentiment(dfanalysis)
                       
                    with tab2:
                      if not dfanalysis.empty:
                         #### interactive dataframe
                         gb = GridOptionsBuilder.from_dataframe(dfanalysis)
                         gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
                         gb.configure_side_bar() #Add a sidebar
                         #gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
                         gridOptions = gb.build()

                         grid_response = AgGrid(
                              dfanalysis,
                              gridOptions=gridOptions,
                               data_return_mode='AS_INPUT', 
                            update_mode='MODEL_CHANGED', 
                             fit_columns_on_grid_load=False,
    
                                  enable_enterprise_modules=True,
                             height=350, 
                              width='100%',
                              reload_data=True
                                                )
                         data = grid_response['data']
                         selected = grid_response['selected_rows'] 
                         dd = pd.DataFrame(selected) #Pass the selected rows to a new dataframe df
                         # Add a button to download the DataFrame as a CSV file
                         if st.button('Download CSV'):
                                    st.markdown(download_csv(dfanalysis), unsafe_allow_html=True)

			
			
			###scattertext
                         st.header('Scatter Text')
                                                  # Copy the scattertext_visualization.html to a temporary file
                         st.write('For better reprentation we recommend selecting 3 sentiment classes')
                         st.write('The 2,000 most sentiment-associated uni grams are displayed as points in the scatter plot. Their x- and y- axes are the dense ranks of their usage in positive vs negative and neutral respectively.')
                         generate_scattertext_visualization(dfanalysis)
                         scattertext_html_path='scattertext_visualization.html'
                         tmp_scattertext_path = "tmp_scattertext_visualization.html"
                         shutil.copyfile(scattertext_html_path, tmp_scattertext_path)

                         # Add a download button for the Scattertext HTML file
                         with open(tmp_scattertext_path, "rb") as file:
                                    scattertext_html_data = file.read()

                         st.download_button(
                             label="Download Scattertext Visualization HTML",
                             data=scattertext_html_data,
                          file_name="scattertext_visualization.html",
                            mime="text/html",
                                )
                         
                         
                         HtmlFile = open("scattertext_visualization.html", 'r', encoding='utf-8')
                         source_code = HtmlFile.read() 
                         print(source_code)
                         components.html(source_code,height = 1500,width = 800)
                    with tab3:

                       st.write('This tool, adapted from the Welsh Summarization project, produces a basic extractive summary of the review text from the selected columns.')
                       summarized_text =run_summarizer(input_text[:2000],i)
	       ##show review
                    tab4.header('View all Data')
                    tab4.dataframe(df ,use_container_width=True)
                    textanalysis = txtanalysis(df)
                    textanalysis.show_reviews(filenames[i],tab4)
                    word_cloud_path = textanalysis.show_wordcloud(filenames[i],tab5)
                    Keyword_context = textanalysis.show_kwic(filenames[i],tab6)
                    textanalysis.concordance(filenames[i],tab7)

         
                    with tab8:
                     column1, column2 = st.columns([1, 2])
                     
                     with column1:
                      try:
                     # Check if the DataFrame exists
                       if not dfanalysis.empty :
			#####pdf_generator
			##############Sentiment analysis
                        data_list_checkbox = st.checkbox("Include Data List as a Table")
                        sentiment_pie_checkbox = st.checkbox("Include Sentiment Pie Graph")
                        sentiment_bar_checkbox = st.checkbox("Include Sentiment Bar Graph")
                        #Wordtree_checkbox = st.checkbox("Include Word Tree")
		       ##############summarisation,
                        download_text = st.checkbox("Include original text")
                        download_summary = st.checkbox("Include summarized text")
                        #full_data_table_checkbox = st.checkbox("Include Full Data Table")
                        word_cloud_checkbox = st.checkbox("Include Word Cloud Image")
                        keyword_context_table_checkbox = st.checkbox("Include Keyword in Context Table")
			
                        # Create the PDF
                            
                        buffer = BytesIO()
                        doc = BaseDocTemplate(buffer, pagesize=A4,topMargin=1.5 * inch, showBoundary=0)

                        # Create the frame for the content
                        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')

    
                        # Create a PageTemplate with the header
                        template = PageTemplate(id='header_template', frames=frame, onPage=header)
                        doc.addPageTemplates([template])
                        elements = []
                        # Add a spacer between header and input text
                        elements.append(Spacer(1, 20))
                        styles = getSampleStyleSheet()
                        # Define the styles for summarisation
  
                        styles.add(ParagraphStyle(name='InputText', fontSize=12, textColor=colors.black))
                        styles.add(ParagraphStyle(name='SummarizedText', fontSize=12, textColor=colors.black))
			# Add content based on selected checkboxes
                        if data_list_checkbox:
  

                            column_names = ['Review', 'Sentiment Label', 'Sentiment Score']
                            table_data = [column_names] + dfanalysis[column_names].values.tolist()
                            col_widths = [200, 100, 100]  # Adjust these values according to your needs
                            wrapped_cells = []

                            
                            cell_style_normal = ParagraphStyle(name='cell_style_normal', parent=styles['Normal'], alignment=1)
                            cell_style_header = ParagraphStyle(name='cell_style_header', parent=styles['Normal'], alignment=1, textColor=colors.whitesmoke, backColor=colors.grey, fontName='Helvetica-Bold', fontSize=14, spaceAfter=12)

                            wrapped_data = []
                            for row in table_data:
                                  wrapped_cells = []
                                  for i, cell in enumerate(row):
                                       cell_style = cell_style_header if len(wrapped_data) == 0 else cell_style_normal
                                       wrapped_cell = Paragraph(str(cell), style=cell_style)
                                       wrapped_cells.append(wrapped_cell)
                                  wrapped_data.append(wrapped_cells)
                            table = Table(wrapped_data, colWidths=col_widths)

                            table.setStyle(TableStyle([
                                  ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

                             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                                  ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                  ('FONTSIZE', (0, 0), (-1, 0), 14),

                                   ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                           ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                  ('GRID', (0, 0), (-1, -1), 1, colors.black),
       
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                                         ]))
                            elements.append(table)
                            elements.append(Spacer(1, 20))


                        if sentiment_pie_checkbox:
                        # Add the sentiment pie graph
                        
                           pie_graph_path = "Pie_fig.png"
                           if os.path.exists(pie_graph_path):                
                              pie_graph = ReportLabImage(pie_graph_path, width= 325, height =250)
                              elements.append(pie_graph)
                              elements.append(Spacer(1, 20))
                           else:
                             st.error("Sentiment Pie Graph image not found")

                        if sentiment_bar_checkbox:
                         # Add the sentiment bar graph
                           
                           bar_graph_path = "Bar_fig.png"
                           if os.path.exists(bar_graph_path):
                               bar_graph = ReportLabImage(bar_graph_path, width= 325, height =250)
                               elements.append(bar_graph)
                               elements.append(Spacer(1, 20))
                           else:
                              st.error("Sentiment Bar Graph image not found")

                        if word_cloud_checkbox:
                           
                           if os.path.exists(word_cloud_path):
                               word_cloud_graph = ReportLabImage(word_cloud_path, width= 325, height =250)
                               elements.append(word_cloud_graph)
                               elements.append(Spacer(1, 20))
                           else:
                              st.error("WordCloud image not found")
				
                        if download_text:
                                 # Add the input text
                                        input_text_paragraph = Paragraph(f"Input Text:\n{input_text}", styles['InputText'])
                                        elements.append(input_text_paragraph)

                                        elements.append(Spacer(1, 20))

                        if download_summary:

                                   # Add the summarized text
                                           
                            summarized_text_paragraph = Paragraph(f"Summarized Text:\n{summarized_text}", styles['SummarizedText'])
                            elements.append(summarized_text_paragraph)
			
			
                        


                        if keyword_context_table_checkbox:
           
                            columns = ['Left context', 'Keyword', 'Right context']
                            table_data = [columns] + Keyword_context.values.tolist()
                            col_widths = [150, 100, 150] 
                            wrapped_cells = []

                            styles = getSampleStyleSheet()
                            cell_style_normal = ParagraphStyle(name='cell_style_normal', parent=styles['Normal'], alignment=1)
                            cell_style_header = ParagraphStyle(name='cell_style_header', parent=styles['Normal'], alignment=1, textColor=colors.whitesmoke, backColor=colors.grey, fontName='Helvetica-Bold', fontSize=14, spaceAfter=12)

                            wrapped_data = []
                            for row in table_data:
                                     wrapped_cells = []
                                     for i, cell in enumerate(row):
                                           cell_style = cell_style_header if len(wrapped_data) == 0 else cell_style_normal
                                           wrapped_cell = Paragraph(str(cell), style=cell_style)
                                           wrapped_cells.append(wrapped_cell)
                                     wrapped_data.append(wrapped_cells)
                            table = Table(wrapped_data, colWidths=col_widths)

                            table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('TEXTCOLOR', (1, 1), (1, -1), colors.red),

    ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ('ALIGN', (2, 1), (2, -1), 'LEFT'),

    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),

    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),

    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ]))
                            # Add heading 'Keyword in Context'
                            heading_style = ParagraphStyle(name='heading_style', parent=styles['Normal'], fontSize=18, fontName='Helvetica-Bold', spaceAfter=12)
                            heading = Paragraph('Keyword in Context', style=heading_style)
                            elements.append(heading)
                            elements.append(Spacer(1, 20))
                            elements.append(table)
                            elements.append(Spacer(1, 20))
			
			
			
			
			
                       else:
                          st.error("DataFrame not found")
                      except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
                        

                     with column2:
			
                       generate_pdf_button = st.button("Generate PDF")
                       if generate_pdf_button:
                          # Build PDF
                          doc.build(elements)
                          buffer.seek(0)
                          generated_pdf_data = buffer.read()

                          # Display the download button only after generating the report
                          if generated_pdf_data:
                                  #st.download_button("Download PDF", generated_pdf_data, "report_positiveandnegative.pdf", "application/pdf")
                                  b64 = base64.b64encode(generated_pdf_data).decode()  # some strings <-> bytes conversions necessary here
                                  href = f'<a href="data:application/pdf;base64,{b64}" download="report_positiveandnegative.pdf">Download PDF</a>'
                                  st.markdown(href, unsafe_allow_html=True)
        



	
###########################################Home page#######################################################################
def main():
    state = get_state()
    st.markdown(
    f"""
    <div style="overflow: hidden; padding: 30px; background-color: lightgrey ;">	
	</div>"""
	, unsafe_allow_html=True)
    col1, col3 = st.columns([3, 1])
    with col3:
        st.image("img/FreeTxt_logo_R.png", width=300) 
    
    with col1:
       st.markdown("""
    <p style='text-align: left; 
              margin-top: 0px; 
              font-size: 80px; 
              color: #4a4a4a; 
              font-family: sans-serif; 
              text-shadow: 2px 2px #aaa;
              font-weight: normal;'>
    Welcome to FreeTxt
    
    </p>""", unsafe_allow_html=True)

    


    st.markdown(
    f"""
<style>
.link-container a.menu-link {{
    float: left;
    color: #4a4a4a;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    font-size: 18px;
    margin: 0px;
    transition: 0.3s;
}}
.link-container a.menu-link:hover {{
    color: #2281EF;
    font-weight: bold;
    text-decoration: underline;
}}
#home-link {{
    color: #2281EF; // This is the hyperlink color
    font-weight: bold;
    text-decoration: underline;
}}
</style>
</style>

<div class="link-container" style="overflow: hidden; padding: 10px; background-color: lightgrey;">
    <a id="home-link" class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=home" target="_self">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg> Home
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=txtanalysis" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 13.5V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m12-3V3.75m0 9.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 3.75V16.5m-6-9V3.75m0 3.75a1.5 1.5 0 010 3m0-3a1.5 1.5 0 000 3m0 9.75V10.5"></path>
        </svg> Analysis
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=demo" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"></path>
        </svg>
        User Guide
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=about" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"></path>
        </svg>About
    </a>
    <a class="menu-link" href="https://nouran-khallaf-free-txt-home-c88nm3.streamlit.app/?page=contact" target="_self">
        <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="height: 25px;">
           <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"></path>
        </svg>
        Contact Us
    </a>
</div>
""",
    unsafe_allow_html=True)
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html =True)

 

   
  
    st.markdown(
      """
<div style='background-color: white; padding: 10px; border-radius: 5px; color: black; font-size:20px; '>
A free online text analysis and visualisation tool for English and Welsh. 
FreeTxt allows you to upload free-text feedback data from surveys, questionnaires etc., 
and to carry out quick and detailed analysis of the responses. FreeTxt will reveal 
common patterns of meaning in the feedback (e.g. what people are talking about/what they are saying about things),
common feelings about topics being discussed (i.e. their ‘sentiment’), 
and can produce simple summaries of the feedback provided. FreeTxt presents the results of 
analyses in visually engaging and easy to interpret ways, and has been designed to allow anyone in 
any sector in Wales and beyond to use it.
</div>
""",
    unsafe_allow_html=True,
    )  



            

          


   


    st.markdown(
    f"""
    <style>
    .content-container {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        grid-template-rows: repeat(3, 1fr);
        gap: 10px;
        justify-items: center;
        align-items: center;
        padding: 10px;
        border-radius: 5px;
        background-color: white;
        color: white;
        text-align: center;
    }}
    
    .content-container > :nth-child(5) {{
        grid-column: 1 / -1;
    }}
    .a-image {{
        border-radius: 5px;
        transition: transform .2s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 1px rgba(0, 0, 0, 0.24);
        position: relative;
    }}
    .a-image:hover {{
        transform: scale(1.1);
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    }}
    .a-image:hover::after {{
        content: attr(title);
        position: absolute;
        top: -30px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.8);
        padding: 5px 10px;
        border-radius: 3px;
        font-size: 14px;
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)
            
 

    

    #st.write("---")
    #st.header("The FreeTxt way-in")
    
   
    st.markdown(
      """
<div style='background-color: lightgrey; padding: 10px; border-radius: 5px; color: black; font-size: 14px;'>
 FreeTxt was developed as part of an AHRC funded collaborative FreeTxt supporting bilingual free-text 
 survey and questionnaire data analysis research project involving colleagues from Cardiff University and 
 Lancaster University (Grant Number AH/W004844/1).
 The team included 
 PI - Dawn Knight; CIs - Paul Rayson, Mo El-Haj; 
 RAs - Ignatius Ezeani, Nouran Khallaf and Steve Morris.
 The Project Advisory Group included representatives from:
 National Trust Wales, Cadw, National Museum Wales, CBAC | WJEC and National Centre for Learning Welsh.

</div>
""",
    unsafe_allow_html=True
    )     
    

    #st.markdown("<br></br>", unsafe_allow_html=True) # Creates some space before logos
#border: 2px solid grey; 
 #       border-radius: 5px;  
    st.markdown(
f"""
<style>
    .logo-container {{
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        
    }}
    .logo {{
        width: 100px;
        height: 100px;
        margin: 10px;
        object-fit: contain;
        flex-grow: 1;
    }}
</style>
""",
unsafe_allow_html=True
)
    st.markdown(
    f"""
    <div class="logo-container">
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/cardiff.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Lancaster.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NTW.JPG')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Amgueddfa_Cymru_logo.svg.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/Cadw.png')}" />
        <img class="logo" src="data:image/png;base64,{get_image_as_base64('img/NCLW.jpg')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/WJEC_CBAC_logo.svg.png')}" />
	<img class="logo" src="data:image/png;base64,{get_image_as_base64('img/ukri-ahrc-square-logo.png')}" />
    </div>
    """,
    unsafe_allow_html=True,
     )


def app():
 #   st.markdown(
  #  """
   # <style>
   # .stApp {
   #     background-color: #D3D6D6;
   # }
   # </style>
   # """,
   # unsafe_allow_html=True
#)







    query_params = st.experimental_get_query_params()
    page = query_params.get("page", [None])[0]
    
	
    if page == "demo":
          st.experimental_set_query_params(page="demo")
          demo_page()
    elif page == "txtanalysis":
          st.experimental_set_query_params(page="txtanalysis")
          textbox_analysis_page()
    elif page == "analysis":
          st.experimental_set_query_params(page="analysis")
          analysis_page()
    elif page == "about":
          st.experimental_set_query_params(page="about")
          about_page()
    elif page == "contact":
          st.experimental_set_query_params(page="contact")
          contact_page()
    elif page == "home":
          st.experimental_set_query_params(page="home")
          main()


    else:
        main()


if __name__ == "__main__":
    app()
