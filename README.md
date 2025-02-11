# README

## Overview
This project generates a structured roadmap using a language model (LLM) and refines it interactively through a graph-based approach. The final roadmap is parsed into structured stages.

## Features
- Uses OpenAI's API to generate a roadmap based on user input.
- Refines the roadmap through an interactive graph-building process.
- Parses the generated roadmap into structured stages.

## Installation

### 1. Clone the Repository
```sh
git clone <repository_url>
cd <repository_directory>
```

### 2. Set Up a Virtual Environment (Optional but Recommended)
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
Ensure you have the required dependencies installed:
```sh
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
This script requires an **OpenAI API Key** to function.

- Create a `.env` file in the root directory:
  ```sh
  touch .env
  ```
- Add the following line to the `.env` file:
  ```env
  OPENAI_API_KEY=your_openai_api_key_here
  ```
  Alternatively, you can manually export the key in your terminal:
  ```sh
  export OPENAI_API_KEY=your_openai_api_key_here
  ```

## Usage

Run the main script:
```sh
python main.py
```

### How It Works
1. **Start the Graph Process**: Initializes the roadmap refinement process.
2. **Build the Graph**: Constructs a roadmap graph based on user interactions.
3. **Refine the Prompt**: The user interacts to refine and shape the final roadmap prompt.
4. **Generate the Roadmap**: Uses OpenAI's model to create a roadmap.
5. **Parse the Stages**: Extracts structured roadmap stages from the generated text.

## File Descriptions
- **main.py** - The entry point of the application.
- **parse_text.py** - Contains `parse_stages()` function to process the roadmap output.
- **roadmap.py** - Contains `create_roadmap()` function to generate a roadmap using OpenAI's API.
- **refine_prompt.py** - Handles the interactive graph-based roadmap refinement.

## Troubleshooting
- If you get an API error, check your OpenAI API key in `.env`.
- Ensure all dependencies are installed using `pip install -r requirements.txt`.
- If the script fails, try running it in debug mode:
  ```sh
  python -m pdb main.py
  ```

## License
This project is licensed under the MIT License. See `LICENSE` for details.

