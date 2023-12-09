function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// Takes 2 numbers (int, float, or string) and returns average
function average(a, b) {
    try {
        return parseInt((parseFloat(a) + parseFloat(b)) / 2);
    } catch(err) {
        console.log(err);
    }
}

// Takes string, returns with first character of each word capitalized
function toTitle(str) {
    return str.replace(/\w\S*/g, function(txt){
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

export { sleep, average, toTitle };
