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
            # result = ('\n    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); margin-top: 1em;">\n      <iframe src="https://drive.google.com/file/d/1UZnhmGHeyxAd1I_Hgmdq8IIT5co8Yflx/preview"\n      style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"\n      frameborder="0" allow="autoplay" allowfullscreen>\n      </iframe>\n    </div>\n    ', "This meme perfectly captures a person running away from trouble with an over-the-top coach-like commentary cheering them on.  It's a classic example of someone being chased by chaos with a motivational twist.  The dramatic tone and the man's obvious attempt to escape is in stark contrast to the commentator's seemingly oblivious or unintentional encouragement.")
            return result
        except Exception as e:
            print(f"Error calling Gradio API: {e}")
            return None 

if __name__ == "__main__":
    agent = GradioMemeAgent()
    result = agent.find_relevant_meme("a man running")
    print(result)