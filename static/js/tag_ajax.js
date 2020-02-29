function follow(id) {
    $.ajax({
        url: "",
        type: "get",
        data: {id: id},
        success: function(response) {
            $("").html(response);
        },
        error: function(xhr) {
        //Do Something to handle error
        }
    });
    //$.post('tag-'+id.toString())
}