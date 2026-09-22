from pathlib import Path
from ollama import chat


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

selected_files = [
    ##Use only the files that are relevant to the question.

]


context = ""

## Write a for loop to go through all the files in selected_files and read their contents into the context variable.


## Call Qwen with the student's question and the context you created above.



print(
    "Context characters:",
    len(context)
)
print(response.message.content)