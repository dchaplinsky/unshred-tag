$(function(){
    $('.shreds-list-wrapper').jscroll({
        nextSelector: 'a.next-page:last',
        contentSelector: 'div.shreds-list',
        callback: init_tooltips
    });

    var page_toolbar = $("#page-wrapper"),  // Toolbar at the bottom of the page
        page_workspace = $("#checked-shreds"), // Scrollable list of shreds
        page_controls_form = $("#controls-wrapper"); // Controls


    function init_tooltips() {
        $(".shred .btn").tooltip({"placement": "bottom"});
    }

    init_tooltips();

    function load_page_controls(data) {
        page_controls_form.html(data);
        page_controls_form.find("form").on("submit", submit_page_form);

        page_controls_form.find("#page-id").on("change", function() {
            var val = $(this).val();

            $("#page-name").toggle(val == "").focus();

            page_controls_form
                .find(".shreds-preview")
                .hide()

            if (val != "") {
                $("#page-" + val).show();
            }
        }).change();  // To invoke handler above and display first preview
    }

    function submit_page_form(e) {
        var form = $(this);
        e.preventDefault();

        var ids = page_workspace.find("img").map(function() {
                    return $(this).data("id");
                }).get(),
            page_name,
            params = {};

        params.page_id = form.find("select[name=page_id]").val();
        if (!params.page_id) {
            page_name = form.find("input[name=page_name]").val();
            params.page_name = page_name;
        } else {
            page_name = form.find("select[name=page_id] option:selected")
                            .data("name");
        }

        if ($.trim(page_name) == "" && !params.page_id) {
            return;
        }

        params.shreds = ids;

        $.post(window.urls.pages, params, function() {
            var shreds_in_list = $(".container-fluid").find(".shred");
            page_workspace.find("img").remove();
            update_page_toolbar();

            $.each(ids, function(i, id) {
                shred_pages = shreds_in_list
                    .filter("[data-id='" + id +"']")
                    .closest(".thumbnail").find(".shred-pages");

                if (!shred_pages.filter("[data-name='" + page_name + "']").length) {
                    shred_pages
                        .append($('<span class="label label-warning">')
                                .html(page_name)
                                .attr("data-name", page_name));
                }
            });
            
        });
    }

    function update_page_toolbar() {
        if (page_workspace.find("img").length) {
            if (page_toolbar.is(":hidden")) {
                $(".container-fluid").css("margin-bottom",
                                          (page_workspace.height() + 20) + "px");

                page_toolbar.show();
                
                page_controls_form.html("");
                $.get(window.urls.pages, load_page_controls);
            }
        } else {
            $(".container-fluid").css("margin-bottom", "20px");

            page_toolbar.hide();
        }
    }

    $(document.body).on("click", ".add-to-page", function(e) {
        e.preventDefault();

        var el = $(this).closest(".shred"),
            id = el.data("id");

        if (page_workspace.find("img[data-id='" + id + "']").length) {
            return;
        }

        page_workspace.append(
            $('<img class="remove-from-page"/>')
                .attr("src", el.data("img"))
                .attr("data-id", id)
        );

        update_page_toolbar();
    }).on("click", ".remove-from-page", function(e) {
        e.preventDefault();
        $(this).remove();

        update_page_toolbar();
    });

    $(".shreds-list-wrapper").magnificPopup({
        delegate: 'a.edit-link',
        type: 'ajax',
        callbacks: {
            parseAjax: function(mfpResponse) {
                var content = $(mfpResponse.data);
                content = $('<div id="inline-shred" class="small-dialog">').append(content);
                content.find(".mastfoot").remove();
                mfpResponse.data = content;
            },
            ajaxContentAdded: function() {
                init_shred_stuff(this.content);
            }
        }
    });
});
