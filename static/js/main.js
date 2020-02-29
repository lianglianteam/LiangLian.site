$(function () {
      $('[data-toggle="tooltip"]').tooltip();
});

function fix_the_nav() {
    if(window.location.hash){
            var target = $(location.hash);
            $("body,html").scrollTop(target.offset().top-100);
    }
}

function show_preview(id, url) {
    var btn = $('#preview-button-'+id);
    btn.attr('disabled', true);

    var node_before = document.getElementById('preview-button-'+id);
    var node_preview = document.createElement("iframe");
    node_preview.src = url;
    node_preview.width = "100%";
    node_preview.height = "500rem";
    node_preview.frameBorder = "0";
    node_preview.setAttribute('sandbox', 'allow-same-origin allow-scripts');
    node_preview.onload = function () {
        document.getElementById('preview-info-'+id).remove();
        btn.tooltip('dispose');
        btn.remove();
    };

    var info = document.createElement('span');
    info.className = "spinner-border spinner-border-sm ml-1";
    info.setAttribute("role", "status");
    info.id = 'preview-info-'+id;
    document.getElementById('preview-button-'+id).insertBefore(info, null);
    document.getElementById('answer-body-'+id).insertBefore(node_preview, node_before);
}

function list_motion(to) {
    var button = document.getElementById('zone');
    button.value = to;
    var input = document.getElementById('zone-input');
    input.value = to;
}

function jump_to_login() {
    var url = "/login?from_=" + encodeURI(location.href);
    location.href = url
}

function set_clipboard(text, obj) {
    var me = $(obj);
    let range = document.createRange();
    let tar = document.querySelector('#code');
    range.selectNodeContents(tar);
    let selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    if(document.execCommand(text)) {
        me.text('已复制');
    }else{
        me.text('复制失败');
    }
    selection.removeAllRanges();
}