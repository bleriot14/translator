import requests
import json

def translate_text(text, source_lang, target_lang, server_url="http://localhost:8000"):
    """
    Sends a POST request to the translation server and returns the result.
    
    :param text: The text to translate
    :param source_lang: The source language code
    :param target_lang: The target language code
    :param server_url: The URL of the translation server (default: http://localhost:8000)
    :return: A dictionary containing the translation result and timing information
    """
    
    # Prepare the request data
    data = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }
    
    print(f"Sending request to {server_url}/translate/")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    # Send the POST request
    try:
        response = requests.post(f"{server_url}/translate/", json=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        print(f"Response content: {response.text}")
        response.raise_for_status()  # Raises an HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response content: {e.response.text}")
        return None
    
    # Parse and return the response
    try:
        result = response.json()
        return result
    except json.JSONDecodeError:
        print("Failed to decode the server response.")
        return None

def print_translation_result(result):
    """
    Prints the translation result in a formatted way.
    
    :param result: The translation result dictionary
    """
    if result:
        print("\nTranslation Result:")
        print(f"Original text: {result['original_text']}")
        print(f"Translated text: {result['translated_text']}")
        print(f"Source language: {result['source_lang']}")
        print(f"Target language: {result['target_lang']}")
        print(f"Total translation time: {result['total_time']:.2f} seconds")
        print(f"Input preparation time: {result['input_prep_time']:.2f} seconds")
        print(f"Translation time: {result['translation_time']:.2f} seconds")
        print(f"Decoding time: {result['decoding_time']:.2f} seconds")
    else:
        print("Translation failed.")

# Example usage
if __name__ == "__main__":
    # Example translation
    text_to_translate = "Hello, how are you?"
    source_language = "eng"
    target_language = "fra"
    
    result = translate_text(text_to_translate, source_language, target_language)
    print_translation_result(result)

    # You can add more translation examples here
    # For example:
    # result = translate_text("Python is a great programming language", "eng", "deu")
    # print_translation_result(result)