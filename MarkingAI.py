import os
import pandas as pd
import requests
from flask import Flask, request, render_template, send_file

app = Flask(__name__)



# Use absolute path for UPLOAD_FOLDER
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer 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",
    "Content-Type": "application/json"
}



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        studentans = request.files['studentans']
        suggestedans = request.files['suggestedans']
        
        if studentans.filename == '' or suggestedans.filename == '':
            return "No selected file", 400
        

        studentans_filename = (studentans.filename)
        suggestedans_filename = (suggestedans.filename)
            
        studentans_path = os.path.join(app.config['UPLOAD_FOLDER'], studentans_filename)
        suggestedans_path = os.path.join(app.config['UPLOAD_FOLDER'], suggestedans_filename)   
        studentans.save(studentans_path)
        suggestedans.save(suggestedans_path)

        # Process the uploaded Excel files
        stdans = pd.read_excel(studentans_path)
        suggestans = pd.read_excel(suggestedans_path)
            
        processed_df = process_and_mark_answers(stdans, suggestans)

  
        output_filename = "marked_" + studentans_filename
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
       
        processed_df.to_excel(output_filepath, index=False)

    
        return send_file(output_filepath, as_attachment=True)
           
    return render_template('testform.html')

def process_and_mark_answers(stdans, suggestans):
    question_columns = [col for col in stdans.columns if col.startswith('Q')]
    
    for col in question_columns:
        stdans[f'{col}_Mark'] = 0  

    for index, row in stdans.iterrows():
        student_name = row['Name']
        for col in question_columns:
            answer = row[col]
            question_index = question_columns.index(col)
            suggested_answer = suggestans.iloc[0, question_index]
            
            prompt= ( 
    f"Suggested Answer: {suggested_answer},\n" 
    f"User Answer: {answer},\n\n" 
    "Evaluate the user's SQL answer based on the following criteria and be strict with it:\n"
    "1. If the user's answer is correct synthetically or have the same output as the suggested answer , return a score of 2.\n"
    "2. If the user's answer is an attempt but has errors or is partially correct, return a score of 1.\n"
    "3. If the user's answer does not have any text written in the string, return a score of 0.\n"
    "4. If there is a comment, follow it when marking\n\n"
    "Only return the score (2, 1, or 0) without any additional text."  )
            payload = {
                "model": "nousresearch/hermes-3-llama-3.1-405b",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            try:
                response = requests.post(URL, json=payload, headers=HEADERS)
                result = response.json()
                mark = int(result['choices'][0]['message']['content'].strip())
                stdans.at[index, f'{col}_Mark'] = mark
            except Exception as e:
                stdans.at[index, f'{col}_Mark'] = -1  

    mark_columns = [col for col in stdans.columns if col.endswith('_Mark')]
    stdans['Total Mark'] = stdans[mark_columns].sum(axis=1)
    return stdans

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)