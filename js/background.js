var seltext = null;

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse)
{
  switch(request.message)
	{
		case 'setText':
			window.seltext = request.data
      console.log(window.seltext);
		break;

		default:
			sendResponse({data: 'Invalid arguments'});
		break;
	}
});

var test = {
    "id": 123,
    "is_tokenized": false
};
console.log(window.seltext+"aaa");

var twosentence = {
}
function savetext(info,tab)
{
    var jax = new XMLHttpRequest();
    jax.open("POST","http://0.0.0.0:8001/encode");
    jax.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    test["texts"] = [window.seltext];
    twosentence["sentence1"] = window.seltext;
    console.log(test);
    jax.send(JSON.stringify(test));
    jax.onreadystatechange = function() { if(jax.readyState==4) {
      display_result(jax.response);
}
}
}
function display_result(json_result){
  var jax_to_endpoint = new XMLHttpRequest();
  jax_to_endpoint.open("POST","http://127.0.0.1:5000/receive");
  jax_to_endpoint.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  jax_to_endpoint.send(json_result);
  jax_to_endpoint.onreadystatechange = function() {
    if(jax_to_endpoint.readyState==4)
    { message = JSON.parse(jax_to_endpoint.response).message;
      console.log(message);
      send_check(message);
    }}

}

function send_check(message){
  twosentence["sentence2"] = message;
  console.log(twosentence);
  var jax_to_check = new XMLHttpRequest();
  jax_to_check.open("POST","http://127.0.0.1:5000/check");
  jax_to_check.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  jax_to_check.send(JSON.stringify(twosentence));
  jax_to_check.onreadystatechange = function() { if(jax_to_check.readyState==4) {
    alert(JSON.parse(jax_to_check.response).message);}}
}

var contexts = ["selection"];
for (var i = 0; i < contexts.length; i++)
{
    var context = contexts[i];
    console.log("context");
    console.log(window.getSelection().toString());
    chrome.contextMenus.create({
      "id":"send_to_server",
      "title": "Send to Server", "contexts":[context]});
    chrome.contextMenus.onClicked.addListener(function(info, tab) {
      if (info.menuItemId == "send_to_server") {
          savetext(info, tab);
      }
  });
}
