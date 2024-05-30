import os
import nltk
import sys

from time import sleep
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from googletrans import Translator
from sqlalchemy import text

from utils import jqutils

# translator = Translator()

translator = Translator()

# Download VADER lexicon if not already downloaded
nltk.download('vader_lexicon')

# Initialize the VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Initialize NLTK language detector
nltk.download('punkt')

# Get a list of supported languages 
supported_languages = supported_language_codes = ["ar", "hi", "ko", "zh-TW", "ja", "zh", "de", "pt", "en", "it", "fr", "es"]

MOCK_NLTK = os.getenv('MOCK_NLTK')

def batch_detect_dominant_language(sample_list):
    language_list = []

    for sample in sample_list:
        try:
            # Use NLTK's language detection to detect the language code
            text = sample["text"]
            words = word_tokenize(text)
            language_code = detect(" ".join(words))

            language_list.append({
                "id": sample["id"],
                "language_code": language_code,
                "language_score": sample["language_score"],
                "text": text,
                "rating": sample["rating"]
            })
        except LangDetectException as e:
            # Handle language detection errors (e.g., when text is too short)
            language_list.append({
                "id": sample["id"],
                "language_code": "unknown",
                "language_score": sample["language_score"],
                "text": sample["text"],
                "rating": sample["rating"]
            })

    return language_list


def analyze_sentiments(reviews):
    sentiment_list = []

    for review in reviews:
        review_id = review["id"]
        review_text = review["text"]
        review_rating = review["rating"]
        language_code = review["language_code"]
        language_score = review["language_score"]

        # Translate the review text if it's in Arabic
        # if detect(review_text) == 'ar':
        try:
            if translator.detect(review_text).lang == 'ar':
                review_text = translator.translate(review_text, src='ar', dest='en').text
                language_score = translator.detect(review_text).confidence
        except:
            pass

        # Calculate sentiment score using VADER sentiment analysis
        sentiment_scores = sia.polarity_scores(review_text)
        compound_score = sentiment_scores['compound']

        # Determine sentiment based on compound score
        if compound_score >= 0.05:
            sentiment = 'positive'
        elif compound_score <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        sentiment_list.append({
            "id": review_id,
            "sentiment": sentiment,
            "sentiment_score": compound_score,
            "language_code": language_code,
            "language_score": language_score
        })

    return sentiment_list

def handle_sentiment_analyze_pending_reviews(marketplace_id):

    db_engine = jqutils.get_db_engine()

    # get reviews not yet processed through sentiment analysis
    query = text("""
            SELECT customer_review_id, customer_review_text, customer_review_rating, language_code, language_score
            FROM customer_review
            WHERE sentiment is null or sentiment = ''
            AND marketplace_id = :marketplace_id
        """)
    with db_engine.connect() as conn:
        result = conn.execute(query, marketplace_id=marketplace_id).fetchall()

    print(f"Found {len(result)} reviews to analyze")

    review_list = []
    unknown_review_list = {
        "positive": [],
        "negative": []
    }
    review_rating_positive_threshold = 2.5
    for one_review in result:
        if one_review["customer_review_text"]:
            review_list.append({
                "id": one_review["customer_review_id"],
                "text": one_review["customer_review_text"],
                "language_code": one_review["language_code"],
                "language_score": one_review["language_score"],
                "rating": one_review["customer_review_rating"]
            })
        elif int(one_review['customer_review_rating']) > review_rating_positive_threshold:
            unknown_review_list['positive'].append(one_review["customer_review_id"])
        else:
            unknown_review_list['negative'].append(one_review["customer_review_id"])

    # get dominant language for each review
    if MOCK_NLTK == "0":
        # Detect the dominant language for each review
        language_list = batch_detect_dominant_language(review_list)
    else:
        print("MOCKING NLTK: DOMINANT LANGUAGE DETECTION FEATURE")
        language_list = []
        for one_review in review_list:
            language_list.append({
                "id": one_review["id"],
                "language_code": "en",
                "language_score": 0.99,
                "text": one_review["text"],
                "rating": one_review["rating"]
            })

    print("Detected dominant language for reviews", len(language_list))

    # batch according to dominant language
    language_sorted_review_dict = {}
    for one_language in language_list:
        language_code = one_language["language_code"]
        language_score = one_language["language_score"]

        language_sorted_review_dict.setdefault(language_code, [])

        language_sorted_review_dict[language_code].append({
            "id": one_language["id"],
            "text": one_language["text"],
            "language_code": language_code,
            "language_score": language_score,
            "rating": one_language["rating"]
        })

    # get sentiment for each review based on dominant language
    sentiment_list = []
    not_supported_language_reviews = []
    for one_language_code in language_sorted_review_dict.keys():
        if one_language_code in supported_languages:
            if MOCK_NLTK == "0":
                # Perform sentiment analysis for each group of reviews by language
                for language_code, reviews in language_sorted_review_dict.items():
                    sentiment_list.extend(analyze_sentiments(reviews))

            else:
                print("MOCKING NLTK: SENTIMENT ANALYSIS FEATURE")
                sentiment_subset_list = []
                random_p = True
                for one_review in language_sorted_review_dict[one_language_code]:
                    sentiment_subset_list.append({
                        "id": one_review["id"],
                        "sentiment": "positive" if random_p else "negative",
                        "sentiment_score": 0.99 if random_p else 0.87,
                        "language_code": one_language_code,
                        "language_score": one_review["language_score"]
                    })
                    random_p = not random_p
                sentiment_list.extend(sentiment_subset_list)
        else:
            not_supported_language_reviews.extend(language_sorted_review_dict[one_language_code])

    for one_review in not_supported_language_reviews:
        review_rating = one_review['rating']
        review_id = one_review['id']
        if review_rating > review_rating_positive_threshold:
            unknown_review_list['positive'].append(review_id)
        else:
            unknown_review_list['negative'].append(review_id)

    if unknown_review_list['positive']:
        query = text("""
            UPDATE customer_review
            SET sentiment = :sentiment
            WHERE customer_review_id IN :review_id_list
        """)
        with db_engine.connect() as conn:
            conn.execute(query, sentiment="positive", review_id_list=unknown_review_list['positive'])

    if unknown_review_list['negative']:
        query = text("""
            UPDATE customer_review
            SET sentiment = :sentiment
            WHERE customer_review_id IN :review_id_list
        """)
        with db_engine.connect() as conn:
            conn.execute(query, sentiment="negative", review_id_list=unknown_review_list['negative'])

    # separate reviews based on sentiment
    positive_review_list = []
    negative_review_list = []
    neutral_review_list = []
    for one_review in sentiment_list:
        review_sentiment = one_review["sentiment"]
        review_id = one_review["id"]

        if review_sentiment == "positive":
            positive_review_list.append(review_id)
        elif review_sentiment == "negative":
            negative_review_list.append(review_id)
        elif review_sentiment == "neutral":
            neutral_review_list.append(review_id)

        # update sentiment for positive reviews
        if len(positive_review_list) > 0:
            query = text("""
                    UPDATE customer_review
                    SET sentiment = :sentiment, language_code = :language_code, language_score = :language_score
                    WHERE customer_review_id IN :review_id_list
                """)
            with db_engine.connect() as conn:
                conn.execute(query, sentiment="positive", language_code=one_review["language_code"], language_score=one_review["language_score"], review_id_list=positive_review_list)

        # update sentiment for negative reviews
        if len(negative_review_list) > 0:
            query = text("""
                    UPDATE customer_review
                    SET sentiment = :sentiment, language_code = :language_code, language_score = :language_score
                    WHERE customer_review_id IN :review_id_list
                """)
            with db_engine.connect() as conn:
                conn.execute(query, sentiment="negative", language_code=one_review["language_code"], language_score=one_review["language_score"], review_id_list=negative_review_list)

        # update sentiment for neutral reviews
        if len(neutral_review_list) > 0:
            query = text("""
                    UPDATE customer_review
                    SET sentiment = :sentiment, language_code = :language_code, language_score = :language_score
                    WHERE customer_review_id IN :review_id_list
                """)
            with db_engine.connect() as conn:
                conn.execute(query, sentiment="neutral", language_code=one_review["language_code"], language_score=one_review["language_score"], review_id_list=neutral_review_list)

    print(f"Updated sentiment for {len(sentiment_list)} reviews")