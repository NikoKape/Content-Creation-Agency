from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from datetime import datetime

class ScriptEditor(BaseTool):
    """
    Writes and edits scripts in Markdown format and saves them locally.
    """
    content: str = Field(..., description="The script content in Markdown format")
    title: str = Field(..., description="The title of the script")
    
    def run(self):
        """
        Saves the script to a local file and returns the file path
        """
        # Create scripts directory if it doesn't exist
        scripts_dir = "scripts"
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
            
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scripts_dir}/{timestamp}_{self.title.replace(' ', '_')}.md"
        
        # Write content to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.content)
            
        return f"Script saved to {filename}"

if __name__ == "__main__":
    tool = ScriptEditor(
        title="Test Script",
        content="# Test Script\n\nThis is a test script."
    )
    print(tool.run()) 