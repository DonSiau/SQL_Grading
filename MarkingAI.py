import os
import pandas as pd
import requests
from flask import Flask, request, render_template, send_file
import time
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

        # Request for the uploaded file
        studentans = request.files['studentans']
        suggestedans = request.files['suggestedans']
        
        if studentans.filename == '' or suggestedans.filename == '':
            return "No selected file", 400
        
        # Save the file requested into a holder
        studentans_filename = (studentans.filename)
        suggestedans_filename = (suggestedans.filename)
            
        studentans_path = os.path.join(app.config['UPLOAD_FOLDER'], studentans_filename)
        suggestedans_path = os.path.join(app.config['UPLOAD_FOLDER'], suggestedans_filename)   
        studentans.save(studentans_path)
        suggestedans.save(suggestedans_path)

        # Process the uploaded Excel files
        stdans = pd.read_excel(studentans_path)
        suggestans = pd.read_excel(suggestedans_path)
        
        #Run the marking AI 
        processed_df = process_and_mark_answers(stdans, suggestans)

        #Create a file with the marked infront
        output_filename = "marked_" + studentans_filename
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
        # Change the file into excel sheet
        processed_df.to_excel(output_filepath, index=False)

        # Return the marked version of the Excel sheet
        return send_file(output_filepath, as_attachment=True)
           
    return render_template('testform.html')

# Codes to run the AI process
def process_and_mark_answers(stdans, suggestans):

    #Find columns that has the questions
    question_columns = [col for col in stdans.columns if col.startswith('Q')]

    #Add timestamp, student class and name column into the marked data
    submissionData_columns = ['Timestamp', 'Enter your class', 'Enter your ID']

    #Create Column for marks
    for col in question_columns:
        stdans[f'{col}_Mark'] = 0  


    for index, row in stdans.iterrows():
        timestamp = row['Timestamp']
        student_class = row['Enter your class']
        student_ID=row['Enter your ID']
        for col in question_columns:
            #Extract students answers  out
            answer = row[col]

            #Extract the question out
            question_index = question_columns.index(col)

            #Extract the suggested answers from the suggested answers excel sheet
            suggested_answer = suggestans.iloc[0, question_index]
            
            #Prompt for the AI to check the answers
            prompt= ( 
    f"Suggested Answer: {suggested_answer},\n" 
    f"User Answer: {answer},\n\n" 
    "Evaluate the user's SQL answer based on the following criteria and be strict with it:\n"
    "1. If the user's answer is correct synthetically and has the same output as the suggested answer , return a score of 2.\n"
    "2. If the user's answer is an attempt but has errors or is partially correct, return a score of 1.\n"
    "3. If the user's answer does not have any text written in the string, return a score of 0.\n"
    "4. If there is a comment, follow it when marking\n\n"
    "5. If there are multiple queries in the suggested answer, then the user's answers should include those queries (whilst following the other rules of course)"
    "Only return the score (2, 1, or 0) without any additional text."  )
            
            #Run the AI
            payload = {
                "model": "nousresearch/hermes-3-llama-3.1-405b", #make sure to use an instruct model, not a chat model
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            retries=3
            delay=2

            #Let the AI do multiple runs to ensure everything is marked and if there is an error there will be a -1
            for attempt in range(retries):
              try:
                  response = requests.post(URL, json=payload, headers=HEADERS)
                  result = response.json()
                  mark = int(result['choices'][0]['message']['content'].strip())
                  stdans.at[index, f'{col}_Mark'] = mark
                  break
              except Exception as e:
                  if attempt < retries - 1:  
                        time.sleep(delay) 
                  stdans.at[index, f'{col}_Mark'] = -1  
    spacer_col = 'marked->'
    stdans[spacer_col] = ''
    mark_columns = [col for col in stdans.columns if col.endswith('_Mark')]
    #Adding of the marks to get the total mark
    stdans['total_marks'] = stdans[mark_columns].sum(axis=1)  

    #Renaming of the columns
    stdans = stdans.rename(columns={'Timestamp':'Timestamp', 'Enter your class':'Class', 'Enter your ID':'ID'})

    #Return of the final data
    submissionData_columns = ['Timestamp', 'Class', 'ID']

    stdans = stdans[submissionData_columns+question_columns + [spacer_col] + mark_columns + ['total_marks']]
    return stdans

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)