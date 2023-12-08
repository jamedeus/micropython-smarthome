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

export { sleep, average };
