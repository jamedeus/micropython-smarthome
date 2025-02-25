const sleep = (ms) => {
    return new Promise((resolve) => setTimeout(resolve, ms));
};

// Takes 2 numbers (int, float, or string) and returns average
const average = (a, b) => {
    try {
        return parseInt((parseFloat(a) + parseFloat(b)) / 2);
    } catch(err) {
        /* istanbul ignore next */
        console.log(err);
    }
};

// Takes string, returns with first character of each word capitalized
const toTitle = (str) => {
    return str.replace(/\w\S*/g, (txt) => {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
};

const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func(...args);
        }, wait);
    };
};

// Takes number, input range, and output range
// Returns number scaled to output range
// Example: Returns 70 if x=700, inMin=1, inMax=1000, outMin=1, outMax=100
const scaleToRange = (x, inMin, inMax, outMin, outMax) => {
    return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin;
};

export { sleep, average, toTitle, debounce, scaleToRange };
