$(function(){
    $.ajaxSetup({
        traditional: true
    });

    var current_shred = $("#current_shred"),
        angle = 0;

    var tags = $("#tags_list .label")
        .tooltip({"placement": "bottom", "html": true})
        .on("click", function(e) {
            e.preventDefault();

            var tags_input = $(".textarea-tags"),
                elem = $(this).closest("a");
            
            if (tags_input.length > 0) {
                tags_input.textext()[0].tags().addTags([elem.data("value")]);
            }
        });

    function collect_data(form) {
        var data = form.find(".textarea-tags").textext()[0].hiddenInput().val();

        data = JSON.parse(data);
        return {
            "_id": form.find("input[name=shred_id]").val(),
            "tagging_start": form.find("input[name=tagging_start]").val(),
            "tags": data,
            "edit": form.find("input[name=edit]").val(),
            "recognizable_chars": form.find("textarea[name=rec-chars]").val(),
            "angle": angle
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

        tags.filter("[data-hotkey]").each(function(){
            var tag = $(this),
                hk = tag.data("hotkey");

            elem.bind("keydown", hk, function() {
                tag.click();
            });
        });
    }

    function load_next(data) {
        current_shred.css("visibility", "visible").html(data);
        init_shred_stuff(current_shred);
    }

    /* http://xkcd.com/292/ */
    window.init_shred_stuff = function (shred) {
        var tags_area = shred.find('.textarea-tags'),
            suggs = tags_area.data("suggestions"),
            angle_input = shred.find("input[name=angle]"),
            auto_tags = tags_area.data("auto_tags") || [],
            existing_tags = tags_area.data("existing_tags") || [];

        if (angle_input.length > 0) {
            angle = parseInt(angle_input.val());
            // Set correct rotation
            rotate(0);
        } else {
            angle = 0;
        }

        tags_area.textext({
            plugins: 'tags autocomplete suggestions prompt arrow',
            tagsItems: existing_tags ? existing_tags : auto_tags,
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
        });

        if (tags_area.length) {
            tags_area.textext()[0].focusInput();
        }

        assign_hotkeys(shred.find("textarea"));

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
            var form = $(this).closest("form"),
                url = form.attr("action"),
                data;
            e.preventDefault();
            data = collect_data(form);

            if (data["edit"] == "1") {
                $.post(url, data, function(response) {
                    $.magnificPopup.close();

                    $(".container-fluid")
                        .find(".shred[data-id='" + data["_id"] +"']")
                        .parent()
                        .html(response);
                });
            } else {
                if (data["tags"].length === 0) {
                    if (window.confirm("Вы не ввели тэгов для этого фрагмента. Пропустить его?")) {
                        current_shred.css("visibility", "hidden");
    
                        $.post(window.urls.skip, data, load_next);
                    }
                } else {
                    current_shred.css("visibility", "hidden");
    
                    $.post(url, data, load_next);
                }
            }
        })
        .on("click", "a.btn-tools.cw", rotate_cw)
        .on("click", "a.btn-tools.ccw", rotate_ccw);

    assign_hotkeys($(document.body));

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
        angle = (angle + val + 360) % 360;
        $(".shred-img")
            .data("angle", angle)
            .rotate({angle: angle});
    }
    
    function rotate_ccw(e) {
        e.preventDefault();
        rotate(-90);
    }

    function rotate_cw(e) {
        e.preventDefault();
        rotate(90);
    }
});
