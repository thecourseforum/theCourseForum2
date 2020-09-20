
const showOld = () => {
    $("#hide-btn").removeClass("active");
    $("#show-btn").addClass("active");

    $(".old").addClass("shown");
};

const hideOld = () => {
    $("#hide-btn").addClass("active");
    $("#show-btn").removeClass("active");

    $(".old").removeClass("shown");
};

export { showOld, hideOld };
