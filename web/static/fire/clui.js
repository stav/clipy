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
      url = '/api/inquire?video=' + video,
      _;

    http.get( url )
    .then( json.parse  )
    .then( _inload     )
    .then( _insert     )
    .fail( console.log )
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
   * Surround the given streams list with corresponding html
   */
  function _markup_streams( streams, vid ) {
    let
      list = document.createElement('ol'),
      _;

    for ( let i = 0; i < streams.length; i++ ) {
      const
        item = document.createElement('li'),
        text = document.createTextNode( streams[i] );

      item.setAttribute('class', 'stream')
      item.setAttribute('index', i + 1 )
      item.setAttribute('vid', vid )
      item.appendChild( text )
      item.addEventListener('click', _download, false)

      list.appendChild( item )
    }
    return list
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

    let index = clipy_index++;

    console.log('clipy_cache:')
    console.log(clipy_cache)
    console.log('loding:')
    console.log(data)
    console.log('index:')
    console.log(index)
    clipy_cache[ index ] = data;
    data['index'] = index;

    return data; // chaining
  }

  /**
   * Display the data summary in a new panel
   */
  function _insert( data ) {
    let
      text = document.createElement('span'),
      panel = document.createElement('li'),
      panels = document.getElementById('panels'),
      details = _get_details( data ),
      _;

    text.innerText = data.title;
    text.setAttribute('class', 'toggle')
    text.addEventListener('click', _toggle, false)

    panel.setAttribute('class', 'panel')
    panel.setAttribute('index', data.index )
    panel.setAttribute('title', data.vid )
    panel.setAttribute('vid', data.vid )
    panel.appendChild( text )
    panel.appendChild( details )
    panels.appendChild( panel )

    return data; // chaining
  }

  /**
   * Construct the video data details
   */
  function _get_details( data ) {
    let
      list = document.createElement('dl'),
      details = document.createElement('div'),
      _;

    for (const [key,val] of es.objectEntries( data )) {
      let value = key === 'streams' ? _markup_streams( val, data.vid ) : _markup_value( val );
      let term = document.createElement('dt'); term.appendChild( document.createTextNode( key ))
      let item = document.createElement('dd'); item.appendChild( value )
      // console.log(`${key}: ${value}`);
      list.appendChild( term )
      list.appendChild( item )
    }
    details.style.display = 'none';
    details.setAttribute('class', 'details')
    details.appendChild( list )

    return details
  }

  /**
   * Show / hide the video details
   */
  function _toggle( e ) {
    let
      style = e.target.parentElement.children[1].style;

    if ( style.display === 'none' )
      style.display = '';
    else
      style.display = 'none';
  }

  /**
   * Get the goods
   */
  function _download( e ) {
    let
      vid = e.target.attributes.vid.value,
      index = e.target.attributes.index.value,
      url = '/api/download?vid=' + vid + '&index=' + index,
      _;
    console.log( index )

    http.get( url )
    .then( json.parse  )
    .then( console.log )
    .fail( console.log )
  }

  /////////////////////////////////////////////////////////////////////////////
  // Declare Public interface

  return {
    inquire: inquire,
    clear: clear,
  }

}())
