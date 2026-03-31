try:
    from textblob import TextBlob
    import nltk
    
    # Download NLTK stopwords if not already present
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            print("Could not download NLTK stopwords. Using a minimal set.")
            
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
    except:
        # Fallback to a basic set of stopwords if NLTK download fails
        stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
                         'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 
                         'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 
                         'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
                         'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
                         'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 
                         'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 
                         'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 
                         'with', 'about', 'against', 'between', 'into', 'through', 'during', 
                         'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
                         'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'])
    
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    stop_words = set()
    print("Warning: NLP dependencies not available. NLP functionality will be limited.")

def preprocess_text(text):
    """Clean and preprocess text using NLTK"""
    if not isinstance(text, str):
        return ""
    
    # Tokenize and remove stopwords
    tokens = [word.lower() for word in text.split() 
              if word.lower() not in stop_words]
    return " ".join(tokens)

def extract_entities(text):
    """Extract noun phrases using TextBlob"""
    if not NLP_AVAILABLE:
        return ["NLP processing not available"]
    
    try:
        blob = TextBlob(text)
        return blob.noun_phrases
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return []

def analyze_sentiment(text):
    """Analyze sentiment using TextBlob"""
    if not NLP_AVAILABLE:
        return {
            'polarity': 0.0,
            'subjectivity': 0.0
        }
    
    try:
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return {
            'polarity': 0.0,
            'subjectivity': 0.0
        }

def get_pos_tags(text):
    """Get part-of-speech tags using TextBlob"""
    if not NLP_AVAILABLE:
        return []
    
    try:
        blob = TextBlob(text)
        return blob.tags
    except Exception as e:
        print(f"Error getting POS tags: {e}")
        return []
