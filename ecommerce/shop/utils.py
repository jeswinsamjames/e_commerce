import numpy as np
import joblib
from .models import Product 
import pandas as pd

# Load the trained SVD model
model_path = 'ml_models/svd_model.pkl'
algo = joblib.load(model_path)

def recommend_products(user_id, top_n=5):
    # Assuming you have a DataFrame with user-product interactions similar to your_user_product_df
    user_product_df = pd.read_csv('path_to_your_user_product_interactions.csv')  # Load your data
    
    # Get all product ids
    all_product_ids = user_product_df['product_id'].unique()
    
    # Predict ratings for all products
    predictions = [algo.predict(user_id, product_id) for product_id in all_product_ids]
    
    # Sort the predictions by estimated rating
    predictions.sort(key=lambda x: x.est, reverse=True)
    
    # Get the top N recommended products
    top_predictions = predictions[:top_n]
    top_product_ids = [pred.iid for pred in top_predictions]
    
    return top_product_ids
