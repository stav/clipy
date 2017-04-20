clui
/**
 * Clipy Tools - User Interface
 *
 * Inject global namespace: clui
 */
=(function(){"use strict";

  /////////////////////////////////////////////////////////////////////////////
  // Public Functions

  /**
   * Request a video inquiry for the particulars like title, duration and description
   *
   * We get back JSON in the response and convert it to an object then load it into the the cache
   * and then insert a display panel for it.
   */
  function inquire() {
    let
      video = document.getElementById('input-video').value,
      url = '/api/test?video=' + video,
      _;

    http.get( url )
    .then( json.parse  )
    .then( _inload     )
    .then( _insert     )
    .fail( console.log )
  }

  /**
   * Get the goods
   */
  function download() {
    console.log('NotImplemented Error')
  }

  /**
   * Remove all panels
   */
  function clear() {
    let
      old_panels = document.getElementById('panels'),
      new_panels = document.createElement('ol'),
      contaniner = document.getElementById('panels-container'),
      _;

    old_panels.remove()
    new_panels.setAttribute('id', 'panels')
    contaniner.appendChild( new_panels )
  }

  /////////////////////////////////////////////////////////////////////////////
  // Private Functions

  /**
   * Surround the given value with corresponding html
   */
  function _markup_value( o ) {
    if ( u.isArray( o )) {
      let
        list = document.createElement('ul'),
        _;
      for ( let i = 0; i < o.length; i++ ) {
        const
          item = document.createElement('li'),
          text = document.createTextNode( o[i] );
        item.appendChild( text )
        list.appendChild( item )
      }
      return list
    }
    return document.createTextNode( o )
  }

  /**
   * Load the data into the cache
   */
  function _inload( data ) {
    if ( 'error' in data ) {
      console.log(data.error)
      console.log(data)
      return
    }

    console.log('clipy_cache:')
    console.log(clipy_cache)
    console.log('loding:')
    console.log(data)
    clipy_cache[ clipy_index++ ] = data;

    return data; // chaining
  }

  /**
   * Display the data summary in a new panel
   */
  function _insert( data ) {
    let
      text = document.createTextNode( data.title ),
      panel = document.createElement('li'),
      panels = document.getElementById('panels'),
      _;

    panel.setAttribute('class', 'panel')
    panel.appendChild( text )
    panels.appendChild( panel )

    return data; // chaining
  }

  /**
   * Display the data detail in a new panel
   */
  function _detail( data ) {
    let
      list = document.createElement('dl'),
      panel = document.createElement('div'),
      panels = document.getElementById('panels'),
      _;

    for (const [key,value] of es.objectEntries( data )) {
      const
        term = document.createElement('dt'),
        item = document.createElement('dd');
      term.appendChild( document.createTextNode( key ))
      item.appendChild( _markup_value( value ))
      // console.log(`${key}: ${value}`);
      list.appendChild( term )
      list.appendChild( item )
    }

    panel.setAttribute('class', 'panel')
    panel.appendChild( list )
    panels.appendChild( panel )
    // document.body.insertBefore(panel, currentDiv);

    return data; // chaining
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    download: download,
    inquire: inquire,
    clear: clear,
  }

}())
