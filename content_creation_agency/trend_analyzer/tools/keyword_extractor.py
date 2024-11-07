from agency_swarm.tools import BaseTool
from pydantic import Field
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from collections import Counter
from textblob import TextBlob
import spacy
from keybert import KeyBERT

class KeywordExtractor(BaseTool):
    """
    Advanced keyword extraction tool using multiple NLP techniques including NLTK, 
    spaCy, and KeyBERT for comprehensive text analysis
    """
    text: str = Field(..., description="The text to extract keywords from")
    min_keyword_length: int = Field(
        default=3,
        description="Minimum length of keywords to consider"
    )
    max_keywords: int = Field(
        default=15,
        description="Maximum number of keywords to return"
    )
    
    def run(self):
        """
        Extracts and analyzes keywords using multiple NLP techniques
        """
        # Download required NLTK data
        for package in ['punkt', 'averaged_perceptron_tagger', 'stopwords', 'maxent_ne_chunker', 'words']:
            nltk.download(package, quiet=True)
        
        # Initialize NLP tools
        nlp = spacy.load('en_core_web_sm')
        kw_model = KeyBERT()
        
        # Process with multiple techniques
        results = {
            "keywords": {},
            "named_entities": [],
            "key_phrases": [],
            "sentiment": {},
            "topic_keywords": []
        }
        
        # 1. Basic NLTK processing
        tokens = word_tokenize(self.text.lower())
        stop_words = set(stopwords.words('english'))
        tokens = [t for t in tokens if t.isalnum() and 
                 t not in stop_words and 
                 len(t) >= self.min_keyword_length]
        
        # POS tagging and noun extraction
        tagged = pos_tag(tokens)
        nouns = [word for word, pos in tagged if pos.startswith('NN')]
        
        # 2. Named Entity Recognition with NLTK
        sentences = sent_tokenize(self.text)
        for sentence in sentences:
            tokens = nltk.word_tokenize(sentence)
            tagged = nltk.pos_tag(tokens)
            entities = ne_chunk(tagged)
            for entity in entities:
                if hasattr(entity, 'label'):
                    results["named_entities"].append({
                        'text': ' '.join([child[0] for child in entity]),
                        'type': entity.label()
                    })
        
        # 3. Keyword extraction with KeyBERT
        keywords = kw_model.extract_keywords(
            self.text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            use_maxsum=True,
            nr_candidates=20,
            top_n=self.max_keywords
        )
        
        # 4. spaCy processing for additional insights
        doc = nlp(self.text)
        
        # Extract key phrases using noun chunks
        key_phrases = [chunk.text for chunk in doc.noun_chunks]
        results["key_phrases"] = Counter(key_phrases).most_common(self.max_keywords)
        
        # 5. Sentiment Analysis with TextBlob
        blob = TextBlob(self.text)
        results["sentiment"] = {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity
        }
        
        # Combine and rank all keywords
        all_keywords = Counter(nouns)
        for keyword, score in keywords:
            all_keywords[keyword] += int(score * 10)
        
        # Add top keywords to results
        results["keywords"] = dict(all_keywords.most_common(self.max_keywords))
        
        # Extract topic keywords using spaCy
        results["topic_keywords"] = [
            {"text": token.text, "pos": token.pos_}
            for token in doc
            if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) >= self.min_keyword_length
        ]
        
        return results

if __name__ == "__main__":
    test_text = """
    Artificial intelligence and machine learning are transforming technology. 
    GPT-4 and other large language models have revolutionized natural language processing.
    Companies like OpenAI and Google are leading innovation in AI development.
    """
    tool = KeywordExtractor(
        text=test_text,
        min_keyword_length=3,
        max_keywords=10
    )
    print(tool.run()) 