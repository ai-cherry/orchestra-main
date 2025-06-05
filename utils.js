// Live Collaboration Test - JavaScript
// Manus can see changes to this file instantly!

/**
 * Say hello to Manus AI via live collaboration
 * @returns {string} Greeting message
 */
function greetManus() {
    return "Hello Manus from JavaScript! Live collaboration is working! 🎉";
}

/**
 * Calculate factorial - changes visible to Manus in real-time
 * @param {number} n - Number to calculate factorial for
 * @returns {number} Factorial result
 */
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

/**
 * Live collaboration demo function
 */
function liveDemoFunction() {
    console.log(greetManus());
    
    // Test factorial calculations
    for (let i = 1; i <= 5; i++) {
        const result = factorial(i);
        console.log(`${i}! = ${result}`);
    }
    
    return "Live collaboration test complete!";
}

// Export for Node.js (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { greetManus, factorial, liveDemoFunction };
}

// Run demo
liveDemoFunction(); 