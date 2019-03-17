# vaccine_chrome_extension
## Getting Started
load the extension in Google chrome extension under developer mode
### Installing
open one terminal to start bert server :
```
bert-serving-start -model_dir=(to be inserted: filepath to the model_dir in your computer ) -http_port 8001
```
example
```
bert-serving-start -model_dir=/Users/meishiyuan/Documents/bert-as-service/english -http_port 8001
```
open another terminal to start python server:
```
python3 endpoint.py
```
### TODO
Highlight the text in the web browser and create another function to instantly give the matched fact. 
