//<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.0/jquery.min.js"></script>
document.getElementById("btn-chat").addEventListener("click", check);

//test to debug

function check_test(){
  if(document.getElementById('input_text').value!=""){
    document.getElementById("btn-chat").style.backgroundColor = "yellow";}
  else{
    document.getElementById("btn-chat").style.backgroundColor = "green";}
}

const request = require('request');

//make json object to populate the request
var test = {
    "id": 123,
    "is_tokenized": false
};

//test["texts"] = [document.getElementById('input_text').value];
//test["texts"] = [document.getElementById("input_text").value];

//main function to check
function check(){

  //test whether input is null
  if (document.getElementById("input_text").value != ''){
    document.getElementById("btn-chat").style.backgroundColor = "yellow";
    test["texts"] = [document.getElementById("input_text").value];
  }
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    chrome.tabs.sendMessage(tabs[0].id, {command: "get-track"}, function(response) {
      request({
        url:'http://0.0.0.0:8001/encode',
        method: 'POST',
        json: test,
    }, function(err, res, body){
        calculate(body);
      });
    });
});
}

//function make a call to the app server - written in endpoint.py
function calculate(result){
  // ajax the JSON to the server
  //$.post("receiver", cars, function(){});
  request({
    url:'http://127.0.0.1:5000/receive',
    method: 'POST',
    json: result,
}, function(err, res, body){
  document.getElementById('output_block').value = body.message //populaye the output block
  });
}
