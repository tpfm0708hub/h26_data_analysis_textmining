import joblib
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
from konlpy.tag import Okt

class SentimentAnalyzer:
    def __init__(self, model_file, encoder_file):
        self.model = load_model(model_file)
        self.encodier = joblib.load(encoder_file)
        self.korean_tokenizer = Okt().morphs

    def analyze_sentiment(self, review):
        tokens = [word for word in self.korean_tokenizer(review)]#   형태소 분석
        encoded_tokens = self.encodier.texts_to_sequences([tokens])
        X = pad_sequences(encoded_tokens)#, maxlen = self.model.input_shape[1])
        #   예측
        results = self.model.predict(X, verbose = 0)
        labels = ['부정', '긍정']
        index = np.argmax(results[0])
        user_output = labels[index]
        return user_output, results[0][index]
