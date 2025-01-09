The function of this code is to add a pipe to openwebui through the perplexica API
You can refer to the API documentation of perplexica and then configure it on the function page of openwebui
This is the API documentation for perplexica：
https://github.com/ItzCrazyKns/Perplexica/blob/master/docs/API/SEARCH.md

You can directly install my code on the openwebui official website:

https://openwebui.com/f/gwaanl/perplexica_pipe


![image](https://github.com/user-attachments/assets/33345bfe-601c-4153-9bba-570c626f2412)

You need to configure perplexica first, using the port of perplexica-backend
Find the installed perplexica pipe in the function settings of the admin settings in openwebui, and configure it according to the perplexica API settings

![image](https://github.com/user-attachments/assets/ef4f8458-fbd8-49db-b98e-b827ceef34d9)

![image](https://github.com/user-attachments/assets/d50dda3c-8aec-407a-be80-f5c19696234e)


Then it will be displayed as a model in the model, showing what the current search mode is. You can copy the configuration for multiple perplexica pipes and choose different searches

![image](https://github.com/user-attachments/assets/d654c79f-557a-463a-b84c-8f1c0ec8f584)


----

Version 0.3.3 has a bug that prevents openwebui from starting. If you updated to 0.3.3 and are experiencing startup failures with openwebui, please use the method below to restore it. I will update the code in a future version to resolve this issue.

I checked the log file and found that the error occurred during the validation process of the Valves class. It seems the customOpenAIBaseURL and customOpenAIKey fields were None instead of valid strings.

I found the problem. You need to locate the file "/app/backend/open_webui/functions.py" within your docker container.  Then, insert the following code snippet between lines 63 and 64.

After adding the code, save the file and restart the openwebui docker container. Once restarted, refresh the webpage and it should launch successfully. 

You can then go into the administrator settings and delete the pipe file.  Afterward, remove the code you added to "/app/backend/open_webui/functions.py".

I will update the pipe script shortly, or you can use version 0.3.2 for now. I'll let you know when the update is ready.


![42d61c66c966795bac602a6035b7e60](https://github.com/user-attachments/assets/daf77fd3-32a5-4967-a883-ce8a0b3d3f5b)
![4a41afbc84d77ad219fa65255fca84f](https://github.com/user-attachments/assets/140dbdda-b329-42eb-b886-f478e6297f40)

```
        if valves is None:
            valves = {}
        if 'customOpenAIBaseURL' not in valves or not isinstance(valves['customOpenAIBaseURL'], str):
            valves['customOpenAIBaseURL'] = 'https://api.xxxxx.com/v1'  
        if 'customOpenAIKey' not in valves or not isinstance(valves['customOpenAIKey'], str):
            valves['customOpenAIKey'] = 'sk-xxxxxxxxxxx' 
```
