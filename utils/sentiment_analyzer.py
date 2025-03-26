import tweepy
import pandas as pd
from textblob import TextBlob
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Gestionnaire d'analyse de sentiment pour les tweets.
    """
    def __init__(self):
        """
        Initialise l'analyseur de sentiment avec les clés d'API Twitter.
        """
        load_dotenv()
        
        # Récupération des clés d'API depuis les variables d'environnement
        self.consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        self.consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not all([self.consumer_key, self.consumer_secret, 
                   self.access_token, self.access_token_secret]):
            raise ValueError("Les clés d'API Twitter ne sont pas configurées")
        
        # Initialisation de l'API Twitter
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

    def analyze_sentiment(self, text: str) -> float:
        """
        Analyse le sentiment d'un texte en utilisant TextBlob.
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            float: Score de sentiment (-1 à 1)
        """
        try:
            analysis = TextBlob(text)
            return analysis.sentiment.polarity
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du sentiment: {str(e)}")
            return 0.0

    def get_tweets(
        self,
        keyword: str,
        count: int = 100,
        days: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère les tweets pour un mot-clé donné.
        
        Args:
            keyword (str): Mot-clé à rechercher
            count (int): Nombre de tweets à récupérer
            days (int, optional): Nombre de jours en arrière pour la recherche
            
        Returns:
            List[Dict]: Liste des tweets avec leurs métadonnées
        """
        try:
            # Construction de la requête
            query = keyword
            if days:
                since_date = datetime.now() - timedelta(days=days)
                query += f" since:{since_date.strftime('%Y-%m-%d')}"
            
            # Récupération des tweets
            tweets = self.api.search_tweets(q=query, count=count)
            
            # Traitement des tweets
            processed_tweets = []
            for tweet in tweets:
                processed_tweet = {
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'user': tweet.user.screen_name,
                    'followers_count': tweet.user.followers_count,
                    'retweet_count': tweet.retweet_count,
                    'favorite_count': tweet.favorite_count,
                    'sentiment': self.analyze_sentiment(tweet.text)
                }
                processed_tweets.append(processed_tweet)
            
            logger.info(f"Récupéré {len(processed_tweets)} tweets pour '{keyword}'")
            return processed_tweets
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tweets: {str(e)}")
            raise

    def get_sentiment_score(
        self,
        keyword: str,
        count: int = 100,
        days: Optional[int] = None
    ) -> Dict:
        """
        Calcule le score de sentiment agrégé pour un mot-clé.
        
        Args:
            keyword (str): Mot-clé à analyser
            count (int): Nombre de tweets à analyser
            days (int, optional): Nombre de jours en arrière
            
        Returns:
            Dict: Statistiques de sentiment
        """
        try:
            tweets = self.get_tweets(keyword, count, days)
            
            if not tweets:
                return {
                    'average_sentiment': 0.0,
                    'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                    'tweet_count': 0
                }
            
            # Calcul des statistiques
            sentiments = [tweet['sentiment'] for tweet in tweets]
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Distribution des sentiments
            distribution = {
                'positive': len([s for s in sentiments if s > 0.1]),
                'neutral': len([s for s in sentiments if -0.1 <= s <= 0.1]),
                'negative': len([s for s in sentiments if s < -0.1])
            }
            
            result = {
                'average_sentiment': avg_sentiment,
                'sentiment_distribution': distribution,
                'tweet_count': len(tweets)
            }
            
            logger.info(f"Score de sentiment calculé pour '{keyword}': {avg_sentiment:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score de sentiment: {str(e)}")
            raise

    def analyze_multiple_keywords(
        self,
        keywords: List[str],
        count: int = 100,
        days: Optional[int] = None
    ) -> Dict[str, Dict]:
        """
        Analyse le sentiment pour plusieurs mots-clés.
        
        Args:
            keywords (List[str]): Liste des mots-clés à analyser
            count (int): Nombre de tweets par mot-clé
            days (int, optional): Nombre de jours en arrière
            
        Returns:
            Dict[str, Dict]: Résultats d'analyse pour chaque mot-clé
        """
        try:
            results = {}
            for keyword in keywords:
                results[keyword] = self.get_sentiment_score(keyword, count, days)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des mots-clés: {str(e)}")
            raise 