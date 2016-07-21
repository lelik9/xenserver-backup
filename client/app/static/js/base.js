/**
 * Created by Alex on 14.07.2016.
 */
function request(url, type, data, on_start, on_complete){
    $.ajax({
        url: url,
        type: type,
        data: data,
        dataType:'json',
        start: on_start,
        complete: on_complete
    });
}

function onSuccess(data) {
    var res = data['responseJSON'];
    $.notify(res['result'], res['type']);
}