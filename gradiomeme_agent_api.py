from gradio_client import Client


class GradioMemeAgent:
    def __init__(self):
        """Initialize the Gradio client for meme finding."""
        self.client = Client("atlasia/moul_lmemes")
    
    def find_relevant_meme(self, user_input):
        """
        Find a relevant meme based on user input using the Gradio API.
        
        Args:
            user_input (str): The text input to find memes for
            
        Returns:
            dict: Result from the API containing meme information
        """
        try:
            result = self.client.predict(
                user_input=user_input,
                api_name="/query_memes"
            )
            print(f"Gradio API result: {result}")
            return result
        except Exception as e:
            print(f"Error calling Gradio API: {e}")
            return None 

if __name__ == "__main__":
    agent = GradioMemeAgent()
    result = agent.find_relevant_meme("a man running")
    print(result)