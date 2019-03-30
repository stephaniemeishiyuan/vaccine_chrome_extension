document.addEventListener('mouseup',function(event)
{
    var sel = window.getSelection().toString();
    chrome.runtime.sendMessage({'message':'setText','data': sel},function(response){});
})
