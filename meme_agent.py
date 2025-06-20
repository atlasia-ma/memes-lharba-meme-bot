import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import json
import chromadb
from chromadb.config import Settings
from huggingface_hub import InferenceClient
import time

class MemeFinder:
    def __init__(self, meme_db_path: str = "data/meme_database.csv", use_llm: bool = True, hf_token: str = None):
        # Load meme database
        self.meme_df = pd.read_csv(meme_db_path)
        
        # Initialize sentence transformer for semantic search
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Chroma DB
        self.chroma_client = chromadb.Client(Settings(
            persist_directory="data/chroma_db",
            is_persistent=True
        ))
        
        # Create or get the collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="memes",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Check if collection is empty and populate if needed
        if self.collection.count() == 0:
            self._populate_chroma_db()
            
        # Initialize LLM for advanced matching
        self.use_llm = use_llm
        if use_llm:
            print("Setting up Hugging Face Inference Client...")
            self.llm_model_id = "Qwen/Qwen2.5-72B-Instruct"
            self.hf_token = hf_token or os.environ.get("HF_TOKEN")
            if not self.hf_token:
                print("⚠️ Warning: No Hugging Face token provided. Some API calls may be rate-limited.")
            else:
                self.client = InferenceClient(
                    provider="hf-inference",
                    api_key=self.hf_token,
                )
            print("Hugging Face Inference Client ready!")

    def _populate_chroma_db(self):
        """Populate Chroma DB with meme embeddings"""
        # Clean the data - replace NaN values with empty strings
        self.meme_df['description'] = self.meme_df['description'].fillna("")
        
        # Create embeddings for all meme descriptions
        embeddings = self.model.encode(self.meme_df['description'].tolist())
        
        # Add to Chroma DB
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=self.meme_df['description'].tolist(),
            ids=[f"meme_{i}" for i in range(len(self.meme_df))],
            metadatas=[{"filename": row['filename']} for _, row in self.meme_df.iterrows()]
        )
        print(f"Added {len(self.meme_df)} memes to Chroma DB")
    
    def find_relevant_meme(self, context: str, top_k: int = 1) -> Dict:
        """
        Find the most relevant meme based on conversation context
        
        Args:
            context: The text to find a meme for
            top_k: Number of results to return
            
        Returns:
            Dict containing the meme filename, description, and similarity score
        """
        if self.use_llm:
            return self._find_meme_with_llm(context)
        else:
            return self._find_meme_with_similarity(context, top_k)
    
    def _find_meme_with_similarity(self, context: str, top_k: int = 1) -> Dict:
        """Find meme using vector similarity search"""
        # Encode the context
        context_embedding = self.model.encode([context])[0]
        
        # Query Chroma DB
        results = self.collection.query(
            query_embeddings=[context_embedding.tolist()],
            n_results=top_k
        )
        
        if not results or not results['ids'] or len(results['ids']) == 0:
            return {"error": "No matching memes found"}
        
        # Get the first result
        idx = int(results['ids'][0][0].split('_')[1])
        meme = self.meme_df.iloc[idx]
        
        return {
            "filename": meme['filename'],
            "description": meme['description'],
            "similarity_score": float(results['distances'][0][0]) if 'distances' in results else 0.0
        }
    
    def _find_meme_with_llm(self, context: str) -> Dict:
        """Find meme using Hugging Face Inference Client to evaluate all descriptions"""
        # Prepare the prompt for the LLM
        system_prompt = """You are a meme expert. Your task is to find the most relevant meme for the given text.
Consider both the filename and description when making your selection.
Respond with ONLY the number of the meme (1-{total}).
If none are relevant, respond with "0".

For example, if the text is "I'm tired" and there's a meme about being exhausted, that would be relevant.
"""
        system_prompt = system_prompt.format(total=len(self.meme_df))
        
        # Add all memes to the prompt
        memes_text = "Available memes:\n"
        for idx, row in self.meme_df.iterrows():
            description = row['description'] if pd.notna(row['description']) else "No description available"
            memes_text += f"{idx+1}. {row['filename']}: {description}\n"
        
        user_prompt = f"Text: \"{context}\"\n\n{memes_text}"
        
        print("\n🤖 Debug: Sending prompt to Hugging Face Inference Client...")
        
        try:
            # Call Hugging Face Inference Client
            completion = self.client.chat.completions.create(
                model=self.llm_model_id,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                max_tokens=10,
                temperature=0.1,
            )
            
            # Extract the response
            generated_text = completion.choices[0].message.content
            print(f"🤖 Debug: API Response: {generated_text}")
            
            # Extract the meme number from the response
            import re
            numbers = re.findall(r'\d+', generated_text)
            print(f"🤖 Debug: Extracted numbers: {numbers}")
            
            if not numbers:
                print("🤖 Debug: No numbers found in response")
                return {"error": "No matching memes found"}
            
            meme_idx = int(numbers[-1]) - 1  # Convert to 0-based index
            print(f"🤖 Debug: Selected meme index: {meme_idx}")
            
            # Check if the index is valid
            if meme_idx < 0 or meme_idx >= len(self.meme_df):
                print(f"🤖 Debug: Invalid meme index: {meme_idx}, valid range: 0-{len(self.meme_df)-1}")
                return {"error": "No matching memes found"}
            
            # Get the meme
            meme = self.meme_df.iloc[meme_idx]
            print(f"🤖 Debug: Selected meme: {meme['filename']}")
            
            # Calculate similarity score for reference
            context_embedding = self.model.encode([context])[0]
            meme_embedding = self.model.encode([meme['description'] if pd.notna(meme['description']) else ""])[0]
            similarity = float(np.dot(context_embedding, meme_embedding) / (np.linalg.norm(context_embedding) * np.linalg.norm(meme_embedding)))
            
            return {
                "filename": meme['filename'],
                "description": meme['description'],
                "similarity_score": similarity,
                "llm_selected": True
            }
        except Exception as e:
            print(f"🤖 Debug: Error calling Hugging Face API: {e}")
            return {"error": f"Error processing LLM response: {str(e)}"}

# Example usage
if __name__ == "__main__":
    print("\n🎭 Meme Finder Demo")
    print("=" * 50)
    print("\nInitializing...")
    
    try:
        # Get Hugging Face token from environment or user input
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            hf_token = input("Enter your Hugging Face token (or press Enter to continue without one): ").strip()
            if not hf_token:
                print("⚠️ Warning: No token provided. Some API calls may be rate-limited.")
        
        # Initialize the meme finder with LLM
        meme_finder = MemeFinder(use_llm=True, hf_token=hf_token)
        print("Ready! Enter your text and I'll find a relevant meme.")
        
        while True:
            context = input("\n🗨️  Enter text (or 'quit' to exit): ")
            if context.lower() == 'quit':
                break
                
            print("\n🔍 Searching...")
            result = meme_finder.find_relevant_meme(context)
            
            if "error" in result:
                print(f"\n❌ {result['error']}")
            else:
                print("\n✨ Found meme:")
                print(f"📁 Filename: {result.get('filename', 'Unknown')}")
                print(f"📝 Description: {result.get('description', 'No description')}")
                print(f"📊 Relevance: {result.get('similarity_score', 0.0):.2f}")
                if result.get('llm_selected', False):
                    print("🤖 Selected by AI")
        
        print("\n👋 Thanks for using the Meme Finder!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}") 