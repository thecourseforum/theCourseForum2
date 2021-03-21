
const showOld = () => {
    $("#hide-btn").removeClass("active");
    $("#show-btn").addClass("active");

    $(".new").addClass("hide");
    $(".old").addClass("shown");

    $(".last-taught").addClass("shown");
};

const hideOld = () => {
    $("#hide-btn").addClass("active");
    $("#show-btn").removeClass("active");

    $(".new").removeClass("hide");
    $(".old").removeClass("shown");

    $(".last-taught").removeClass("shown");
};

export { showOld, hideOld };
