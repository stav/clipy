u
/**
 * Utility functions
 *
 * Inject global namespace: u
 */
=(function(){"use strict";

// http://www.ecma-international.org/ecma-262/5.1/#sec-8.6.2

    function _is ( o, type ){
        return Boolean( Object.prototype.toString.call( o ) === type )
    }

    /**
     * Do we have an Object?
     */
    function isObject ( o ){
        return _is( o, '[object Object]')
    }

    /**
     * Do we have a String?
     */
    function isString ( o ){
        return _is( o, '[object String]')
    }

    /**
     * Do we have a Number?
     */
    function isNumber ( o ) {
        return isNaN( o ) ? false : _is( o, '[object Number]')
    }

    /**
     * Do we have a Date?
     */
    function isDate ( o ){
        return _is( o, '[object Date]')
    }

    /**
     * Do we have a valid Date?
     */
    function isValidDate ( o ) {
        return u.isDate( o ) && o.isValid()
    }

    /**
     * Do we have an Array?
     */
    function isArray ( o ){
        return _is( o, '[object Array]')
    }

    /**
     * Convert to Array
     */
    function toArray ( o ){
        // Wrap objects and strings in an Array
        if ( isObject( o ) || isString( o ) )
            return [ o ];

        // probably some iterable
        return [].slice.call( o )
    }

    /**
     * Check if the given thing is non-empty
     */
    function isFilled ( o ) {
        return Boolean( o && Object.keys( o ).length )
    }

    /**
     * Extend the first parameter with all the properties from the second
     */
    function extend ( target, source ){
        for ( var o of toArray( source ) ) {
            Object.assign( target, o )
        }
    }

    /**
     * Return the first element in an array
     */
    function first ( array ){
        if ( u.isFilled( array ))
            return array[0]
    }

    /**
     * Determine the type of object provided: Date, Array, String, etc.
     */
    function type ( o ){
        var
            type = Object.prototype.toString.call( o ),
            matches = new RegExp("\\[object (\\w+)\\]").exec(type);

        return matches && matches.length === 2 ? matches[1] : 'Unknown'
    }

    return {

        isArray:     isArray,
        isDate:      isDate,
        isFilled:    isFilled,
        isNumber:    isNumber,
        isObject:    isObject,
        isString:    isString,
        isValidDate: isValidDate,

        toArray:     toArray,

        extend:      extend,
        first:       first,
        type:        type,
    }

}())
