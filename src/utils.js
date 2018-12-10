/**
 * @return {string}
 */
const GetKeyByValue = function(object, value) {
    return Object.keys(object).find(key => object[key] === value);
};