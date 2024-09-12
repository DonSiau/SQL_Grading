from flask import Flask, request, render_template, send_file
import pandas as pd
import openpyxl
import os
import requests

app = Flask(__name__)

# Replace with your actual LLM API URL and headers
URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer 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",
    "Content-Type": "application/json"
}

@app.route('/', methods=['POST'])
def index():
    if request.method == 'POST':
        
        studentans = request.files['studentans']
        studentans = os.path.join("uploads", studentans.filename)
        studentans.save(studentans)

        suggestedans = request.files['suggestedans']
        suggestedans = os.path.join("uploads", suggestedans.filename)
        suggestedans.save(suggestedans)


            # Process the uploaded Excel file
        stdans = pd.read_excel(studentans)
        suggestans = pd.read_csv(suggestedans)
        processed_df = process_and_mark_answers(stdans, suggestans)
        
        keys = suggestedans.iloc[0]  # First row (index 0)
        values = suggestedans.iloc[1]  # Second row (index 1)

        # Create a dictionary by zipping the keys and values together
        key_value_pairs = dict(zip(keys, values))

        print(key_value_pairs)

        # Save the new Excel file
        output_filename = "marked_" + file.filename
        output_filepath = os.path.join("uploads", output_filename)
        processed_df.to_excel(output_filepath, index=False)

        # Send the new Excel file to the user
        return send_file(output_filepath, as_attachment=True)

    return render_template('upload.html')

def process_and_mark_answers(stdans, suggestans):
    # Remove or modify answers in the DataFrame
    answers = stdans["Answer"]  # Assuming there is a column named "Answer"
    

    Suggested_Answer = suggestans["Suggested_Answer"]

    prompt= ( 
    f"Suggested Answer: {Suggested_Answer},\n" 
    f"User Answer: {answers},\n\n" 
    "Evaluate the user's SQL answer based on the following criteria and be strict with it:\n"
    "1. If the user's answer is correct synthetically or have the same output as the suggested answer , return a score of 2.\n"
    "2. If the user's answer is an attempt but has errors or is partially correct, return a score of 1.\n"
    "3. If the user's answer does not have any text written in the string, return a score of 0.\n\n"
    "Only return the score (2, 1, or 0) without any additional text."  )
    
    marks = []
    for answer in answers:
        # Prepare the payload for the LLM
        payload = {
            "model": "nousresearch/hermes-3-llama-3.1-405b", # Optional
    "messages": [
      { "role": "user", "content":  prompt }
    ]  
        }
        response = requests.post(URL, json=payload, headers=HEADERS)
        result = response.json()

        # Extract the mark from the LLM response
        mark = result.get("mark", "N/A")  # Assume "mark" is returned in the response
        marks.append(mark)

    # Add the marks to the DataFrame
    df["Mark"] = marks
    return df

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
