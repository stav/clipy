es
/**
 * EatUp Tools - Ecmascript utilities
 *
 * Inject global namespace: es
 */
=(function(){"use strict";

/*
 * Sane object property iteration
 *
 * http://exploringjs.com/es6/ch_iteration.html#objectEntries
 *
 * const obj = { first: 'Jane', last: 'Doe' };
 * for (const [key,value] of objectEntries(obj)) {
 *     console.log(`${key}: ${value}`);
 * }
 */
function objectEntries( obj )
{
    let index = 0;

    // In ES6, you can use strings or symbols as property keys,
    // Reflect.ownKeys() retrieves both
    const propKeys = Reflect.ownKeys(obj).filter(function(o){return o!=='length'});

    return {
        [Symbol.iterator]() {
            return this;
        },
        next() {
            if (index < propKeys.length) {
                const key = propKeys[index];
                index++;
                return { value: [key, obj[key]] };
            } else {
                return { done: true };
            }
        }
    };
}

// Interception debugging
// http://exploringjs.com/es6/ch_proxies.html#_intercepting-method-calls
function traceMethodCalls(obj) {
    const handler = {
        get(target, propKey, receiver) {
            const origMethod = target[propKey];
            // console.log(origMethod, origMethod.name, origMethod.name === 'get')
            if ( typeof origMethod === 'function' ){
                return function (...args) {
                    const result = origMethod.apply(this, args);
                    console.log('>________________________________________')
                    console.log(`${target.constructor.name}.${propKey}()`, args, result)
                    console.log(target)
                    return result
                }
            }
            return origMethod
        }
    };
    // return obj  // Uncomment this to disable Proxy use globally
    return new Proxy(obj, handler)
}

/////////////////////////////////////////////////////////////////////////////
// Declare Public interface

return {
    objectEntries:    objectEntries,
    traceMethodCalls: traceMethodCalls
}

}())
