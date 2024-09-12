import requests
import json
Question="A customer placed an order for 8 copies of  a book. As Rachel was busy she did not write the title down and she could only remember the title ended with the word ‘students’ and there were  6  to 10 copies of that title  in stock.   When Rachel executed the SQL statement below to find the distributor’s name and contact number, her result showed many duplicate rows. Show Rachel how to remove the duplicate rows the above SQL statement. Write another SQL statement that would solve her predicament of fulfilling the order for the customer.   "
Suggested_Answer ="SELECT DISTINCT B.title, D.distributor_name, PD.contact_number  FROM book B  INNER JOIN publisher_has_distributor PD ON PD.publisher_id = B.publisher_id  INNER JOIN distributor D ON D.distributor_id = PD.distributor_id  WHERE B.title LIKE '%students';"
User_Answer = ""

prompt= ( f"Question: {Question},\n" 
    f"Suggested Answer: {Suggested_Answer},\n" +
    f"User Answer: {User_Answer},\n\n" +
    "Evaluate the user's SQL answer based on the following criteria and be strict with it:\n"
    "1. If the user's answer is correct synthetically or have the same output as the suggested answer , return a score of 2.\n"
    "2. If the user's answer is an attempt but has errors or is partially correct, return a score of 1.\n"
    "3. If the user's answer does not have any text written in the string, return a score of 0.\n\n"
    "Only return the score (2, 1, or 0) without any additional text."  )


response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": f"Bearer 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",

  },
  data=json.dumps({
    "model": "nousresearch/hermes-3-llama-3.1-405b", # Optional
    "messages": [
      { "role": "user", "content":  prompt }
    ]  
  })
)
response_data = response.json()
output_content = response_data['choices'][0]['message']['content']
print("You have scored " + output_content + " marks.")