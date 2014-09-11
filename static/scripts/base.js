$(function(){
    $.ajaxSetup({
        traditional: true
    });

    var current_shred = $("#current_shred");
    var degree = 0;

    function collect_data() {
        var data = $(".textarea-tags").textext()[0].hiddenInput().val();

        data = JSON.parse(data);
        if (data.length && !!degree) data.push("Поворот на " + degree + " градусов");
        return {
            "_id": $("#shred_id").val(),
            "tagging_start": $("#tagging_start").val(),
            "tags": data,
            "recognizable_chars": $("#rec-chars").val()
        };
    }

    function assign_hotkeys(elem) {
        elem
            .bind('keydown', 'alt+return', function(e) {
                $("a#save-button").click();
            })
            .bind('keydown', 'f1', function(e) {
                e.preventDefault();
                $('.popup-with-zoom-anim').click();
            })
            .bind('keydown', 'ctrl+g', rotate_cw)
            .bind('keydown', 'ctrl+h', rotate_ccw)
            .bind('keydown', 'ctrl+i', function(e) {
                e.preventDefault();
                $('a.btn-tools.info').click();
            });
    }

    function load_next(data) {
        degree = 0;
        current_shred.css("visibility", "visible").html(data);

        var tags_area = current_shred.find('.textarea-tags'),
            suggs = tags_area.data("suggestions"),
            auto_tags = tags_area.data("auto_tags");

        tags_area.textext({
            plugins: 'tags autocomplete suggestions prompt arrow',
            tagsItems: auto_tags,
            autocomplete: {
                dropdown: {
                    maxHeight : '200px'
                }
            },

            prompt: 'Укажите тэги',
            suggestions: suggs,
        }).bind('isTagAllowed', function(e, data){
            var formData = tags_area.textext()[0].hiddenInput().val();
                list = JSON.parse(formData);

            if (formData.length && list.indexOf(data.tag) >= 0) {
               data.result = false;
            }
        }).textext()[0].focusInput();


        assign_hotkeys(current_shred.find("textarea"));

        $("img.zoom-it").each(function() {
            $(this).image_zoomer({height: 130, width: 130, scale: 2});
        });

        $(".btn-tools").tooltip({"placement": "bottom"});

        $('#additional-info-link').magnificPopup({
            type: 'inline',

            fixedContentPos: false,
            fixedBgPos: true,
            overflowY: 'auto',
            closeBtnInside: true,
            preloader: false,

            midClick: true,
            removalDelay: 100,
            mainClass: 'my-mfp-zoom-in'
        });        
    }

    $(document.body)
        .on("click", "a#save-button", function(e) {
            e.preventDefault();
            form = collect_data();

            if (form["tags"].length === 0) {
                if (window.confirm("Вы не ввели тэгов для этого фрагмента. Пропустить его?")) {
                    current_shred.css("visibility", "hidden");

                    $.post(window.urls.skip, form, load_next);
                }
            } else {
                current_shred.css("visibility", "hidden");

                $.post(window.urls.next, form, load_next);
            }
        })
        .on("click", "a.btn-tools.cw", rotate_cw)
        .on("click", "a.btn-tools.ccw", rotate_ccw);

    $('.popup-with-zoom-anim').magnificPopup({
        type: 'inline',

        fixedContentPos: false,
        fixedBgPos: true,
        overflowY: 'auto',
        closeBtnInside: true,
        preloader: false,

        midClick: true,
        removalDelay: 100,
        mainClass: 'my-mfp-zoom-in'
    });

    if (window.user && current_shred.length) {
        $.get(window.urls.next, load_next);

        if (!$.cookie('help')) {
            $.cookie('help', '1', {
                expires: 365,
                path: '/'
            });
            $('.popup-with-zoom-anim').click();
        }
    }

    function rotate(val) {
        degree = (degree + val + 360) % 360;
        $(".shred-img")
            .data("angle", degree)
            .rotate({angle: degree});
    }
    
    function rotate_ccw(e) {
        e.preventDefault();
        rotate(-90);
    }

    function rotate_cw(e) {
        e.preventDefault();
        rotate(90);
    }

    var shreds_for_page = [];
    var name_for_page = "";
    var page = $("#checked-shreds");
    var select = $('#select-page');
    var pages = [];
    var name_for_page_forced = "";

    window.pages.forEach(function(e)
    {
        pages.push(e.split(','));
    });

    function layout_handler() {
        $(".container-fluid").css("margin-bottom", page.height() + 20 + "px");
        if (shreds_for_page.length > 0) {
            $("#controls-wrapper").show();
            if (!!name_for_page_forced) {
                select.find('option').each(function(i, e)
                {
                    if (e.value == name_for_page_forced) {
                        e.selected = true;
                    } else
                        e.selected = false;
                    e.disabled = true;
                });
            }
        } else {
            $("#controls-wrapper").hide();
        }
    }

    $(document.body).on("click", ".add-to-page", function(e) {
        e.preventDefault();
        var page_name = $(this).data().page;

        if (!!name_for_page_forced && !!page_name) {
            if (name_for_page_forced == page_name) return false;
            else {
                shreds_for_page = [];
                name_for_page = "";
                name_for_page_forced = "";
                page.empty();
            }
        }

        if (!!page_name) {
            pages.forEach(function(e)
            {
                if (e[0] == page_name) {
                    name_for_page_forced = name_for_page = page_name;
                    shreds_for_page = e.slice(1);
                    shreds_for_page.forEach(function(id){
                        page.append( "<a class='remove-from-page' data-id=" +
                            id + "><img src=" + $("a[data-id='" +
                                id + "']").data().img + "/></a>" );
                    });

                    return false;
                }
            })
            layout_handler();
        } else {
            if ($.inArray(id, shreds_for_page) == -1){
                var id = $(this).data().id;
                shreds_for_page.push(id);
                page.append( "<a class='remove-from-page' data-id="+
                    id + "><img src=" + $(this).data().img + "/></a>" );
                layout_handler();
            }
        }
    });

    $(document.body).on("click", ".remove-from-page", function(e) {
        e.preventDefault();
        var id = $(this).data().id;
        $(this).remove();
        shreds_for_page.splice($.inArray(id, shreds_for_page), 1);
        layout_handler();
    });

    $(document.body).on("change", "#select-page", function() {
        if ($("select#select-page").val() == "new-page") {
            $('.popup-with-zoom-anim').click();
        } else
            name_for_page = $("select#select-page").val();
    });

    $(document.body).on("click", "#set-page-name", function() {
        $('.mfp-close').click();
        var name = $('#page-name').val();

        name_for_page = name;
        select.find('option').each(function(i, e)
        {
           e.selected = false
        });

        select.append($("<option selected></option>")
            .attr("value", name)
            .text(name));
    });

    $(document.body).on("click", "#push-shreds-to-page", function() {
        var $form = $("<form></form>");
        $form.attr("action", "");
        $form.attr("method", "POST");
        $form.append('<input type="hidden" name="page-name" value="'+name_for_page+'" />');
        $form.append('<input type="hidden" name="shreds" value="'+shreds_for_page+'" />');
        $("body").append($form);
        $form.submit();
    });
});
