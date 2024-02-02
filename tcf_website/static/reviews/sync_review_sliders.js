/* Sync Review Rating Slider InputIds */
jQuery(($) => {
    const tuples = [
        ["#instructor_rating", "#instructor_rating2"],
        ["#enjoyability", "#enjoyability2"],
        ["#difficulty", "#difficulty2"],
        ["#recommendability", "#recommendability2"]
    ];

    tuples.forEach((tuple) => {
        const [rangeInputId, numberInputId] = tuple;
        // When the slider changes, so should the number, so propagate the new value.
        $(rangeInputId).change(() => $(numberInputId).val($(rangeInputId).val()));
        // and vice versa
        $(numberInputId).change(() => $(rangeInputId).val($(numberInputId).val()));
    });
});
