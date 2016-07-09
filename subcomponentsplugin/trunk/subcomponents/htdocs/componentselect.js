/*
 * Copyright 2006, John Drinkwater <john@nextraweb.com>
 * Distributed under the terms of the MIT License.
 * Please note, this script isn't as DOM friendly as I would like, 
 * but IE, as always, has problems with <select> and <option>s
 * Version 1j, from http://ezri.nextraweb.com/examples/js/haiku/rev1j/componentselect.js
 * Thanks to wkornew & tic
 */

/*
 * Maintained by Niels Sascha Reedijk <niels.reedijk@gmail.com>
 * Copyright 2012.
*/

/*
	take the current selection, and make a haiku/component
 */
function updateSelection( set, level ) {
	
	var text, i, component = '';
	for ( i = 1; i <= level + 1 ; i++ ) { 
		if ( componentSelector[ set ][ i ] && componentSelector[ set ][ i ].selectedIndex != -1 ) {
			text = componentSelector[ set ][ i ].options[ componentSelector[ set ][ i ].selectedIndex ].text;
			if ( text != '' )
				component += text + '/';
		}
	}
	hiddenComponent[ set ].value = component.substring( 0, component.length - 1 );
}

/*
	The user has changed the selected component
 */
function selectComponent( e ) {

	// because browsers never make it easy (IE)..
	var caller, remover;
	if ( !e ) e = window.event;
	if ( e.target ) caller = e.target; else if ( e.srcElement ) caller = e.srcElement;
	if ( caller.nodeType == 3 ) // defeat Safari bug
		caller = caller.parentNode;
	var level = caller.stage, set = caller.set, onlyLeafs = caller.allowleafs;

	// bomb out if this is a last choice
	if ( level >= maxBranches ) {
		updateSelection( set, level ); 
		return;
	}

	// remove any <select>s to the right of us
	for ( i = maxBranches; i > level; i-- ) {
		if ( null != ( remover = componentSelector[ set ][ i ] ) ) {
			remover.selectedIndex = -1;
			if ( remover.parentNode )
				 remover.parentNode.removeChild( remover );
		}
	}
	// check if the user back–pedalled to a non option ( we no longer have '' choices )
    var parentChoices = Array()
	var parentChoice = componentSelector[ set ][ level ].options[ componentSelector[ set ][ level ].selectedIndex ].text;
    for(k=0; k<level; k++) {
        parentChoices[k] = componentSelector[ set ][ k+1 ].options[ componentSelector[ set ][ k+1 ].selectedIndex ].text; // we need to examine more than just one parent
    }
	if ( parentChoice == '' ) {
		updateSelection( set, level ); 
		return;
	}

	var choice, superChoice, shortLeaf = false, previous = 's33d', p = 0, recursive = false, currentSelector = componentSelector[ set ][ level + 1 ];
	// empty the choice
	currentSelector.options.length = 0;
	previous = currentSelector.options[ p++ ] = new Option( );
 
	// Populate the choice 
	for ( i = 0; i < componentList.length ; i++ ) {
		choice = componentList[ i ][ level ]; 
		superChoice = componentList[ i ][ level - 1 ]; 
       
        // more extensive check: all parent components are compared to all super components:
        var isOK=true;
        for (l=1;l<level;++l) {
            if ( componentList[i][l-1] != parentChoices[l-1] ) {
                isOK = false;
            }
        }

		if ( superChoice == parentChoice ) {
			if ( previous != choice && choice != null ) {
			
				previous = choice;

                // for the actual adding of the option, the extensive check's
                // result is used:
                if(isOK) {
                    currentSelector.options[ p++ ] = new Option( choice, choice );
                }
			}
			if ( componentList[ i ][ level + 1 ] != null ) 
				recursive = true;
			if ( choice == null )
				shortLeaf = true;
		}
	}
	currentSelector.selectedIndex = 0; // Konq. has fits without

	// shortLeaf is true when we have a stump with leafs further on
	if ( currentSelector.options.length > 0 ) {
		if ( !( shortLeaf || !onlyLeafs) || previous == currentSelector.options[ 0 ]  ) {
			currentSelector.options[ 0 ] = null;
		}
	}

	// avoid cases where there are no options, ie, we have selected a leaf
	if ( currentSelector.options.length < ( onlyLeafs ? 1 : 2 ) ) {
		updateSelection( set, level ); 
		return;
	}

	// We're done, add it back to the page
	var parent = caller.parentNode;
	var sibling = caller.nextSibling;
	if ( sibling != null )
		parent.insertBefore( currentSelector, sibling );
	else
		parent.appendChild( currentSelector );

	// does this branch continue?
	if ( recursive ) {
		var event = { target : currentSelector };
		selectComponent( event ); // My Konq was being funny with anon {}
	} else 
		updateSelection( set, level ); 
}



/*
	This function deletes the <select> box, replaces it with a hidden input box, 
	and as many <select>s as the first/selected component had parts: this new element has an 
	event that triggers on change, to add or remove <select> boxes
	original: the <select> field that is to be replaced
	set: support multiple component fields, can leave null for autoincrement
	onlyLeafs: add leafs that contain '', so users can pick super components
 */
function reduceComponents( original, set, onlyLeafs ) {
	
	// check support, else block js method
	if ( !document.createElement || !original )
		return; 
	if ( set == null ) set = window.components++;
	if ( onlyLeafs == null ) onlyLeafs = true;

	var i, p, j, sibling = original, parent = original.parentNode;
	// we assume the options never change between reduceComponents calls
	if ( componentList.length == 0 ) {
		for ( i = 0; i < original.options.length; i++ ) {
			componentList[ i ] = original.options[ i ].text.split( '/' );
			maxBranches = ( maxBranches < componentList[ i ].length ? componentList[ i ].length : maxBranches );
		}
		componentList.sort(); // so Trac can be lazy
	}

	componentSelector[ set ] = new Array();

	// create some replacement dropdowns
	for ( i = 1; i <= maxBranches; i++ ) {
		componentSelector[ set ][ i ] = document.createElement( 'SELECT' );
		componentSelector[ set ][ i ].id = 'component-selector-' + set + '-' + i;
		componentSelector[ set ][ i ].className = 'haikucomponent';
		componentSelector[ set ][ i ].stage = i;
		componentSelector[ set ][ i ].set = set;
		componentSelector[ set ][ i ].allowleafs = onlyLeafs;
		addEvent( componentSelector[ set ][ i ], 'change', selectComponent );
	}

	// Setup the field to submit
	var currentSelector = componentSelector[ set ][ 1 ];
			hiddenComponent[ set ] = document.createElement( 'INPUT' );
			hiddenComponent[ set ].id = original.id;
			hiddenComponent[ set ].name = original.name;
			hiddenComponent[ set ].type = 'hidden';	

	// Take currently selected option, or the first
	if ( !original.options ) return; // because Opera is buggy
	if ( original.selectedIndex == -1 ) original.selectedIndex = 0;
	// Query adds '' at the start
	if ( onlyLeafs && original.options[ original.selectedIndex ].text == '' && original.selectedIndex == 0 ) original.selectedIndex = 1;
	hiddenComponent[ set ].value = original.options[ original.selectedIndex ].text;
	subItems		  = hiddenComponent[ set ].value.split( '/' );
	var previous = 's33d', shortLeaf = false;
	// Populate choice(s)	
	for ( i = 0; i < subItems.length + 1; i++ ) {

		p = 0;
		currentSelector = componentSelector[ set ][ i + 1 ];
		if ( !currentSelector )
			continue;
		
		previous = currentSelector.options[ p++ ] = new Option( );
		for( j = 0; j < componentList.length ; j++ ) {

			choice = componentList[ j ][ i ];

            // go through whole path - all subcomponents must match:
            isOK=true;
            for (k=0; k <= i-1 ; ++k) {
                if(componentList[j][k] != subItems[k]) {
                    isOK=false;
                    break;
                }
            }

            // old:
            // (this only checks the last subcomponent)
			//if ( componentList[ j ][ i - 1 ] == subItems[ i - 1 ] /*|| typeof subItems[ i - 1 ] == 'undefined'*/ ) 
            // new:
            if (isOK)
            {

				if ( previous != choice && choice != null && choice != '' ) {
					previous = choice;					
					currentSelector.options[ p++ ] = new Option( choice, choice );
					if ( choice == subItems[ i ] )
						currentSelector.selectedIndex = p - 1;
				}
				if ( choice == null )
					shortLeaf = true;
			}

		}
		// Special case(s) for supercomponents: we have children, but! we dont have a child ourselves
		if ( currentSelector.options.length > 0 ) {
			if ( !( subItems[ i ] == null || shortLeaf || !onlyLeafs ) || previous == currentSelector.options[ 0 ] ) {
				currentSelector.options[ 0 ] = null;
			}
		}

		if ( currentSelector.options.length < ( onlyLeafs ? 1 : 2 ) )
			continue;

		// insert into page
		if ( sibling != null )
			parent.insertBefore( currentSelector, sibling );
		else
			parent.appendChild( currentSelector );
	}
	parent.replaceChild( hiddenComponent[ set ], original );
}

window.componentList = new Array( );
window.components = 0;
window.componentSelector = new Array( );
window.hiddenComponent = new Array( );
window.maxBranches = 0;

/*
  We hook into the query page with this attached to the filter <select>
  We should be called after the component has been created if the browser
  follows the DOM way of thinking
 */
function convertQueryComponent() {
	jQuery('tr.component td.filter select').each(function () {
		if (this.name.match(/[0-9]+_component/g) )
			reduceComponents(this, null, true)
	});
}

function convertBatchModifyComponent() {
	jQuery('#batchmod_component td.batchmod_property select').each(function () {
		if (this.name == "batchmod_value_component")
			reduceComponents(this, null, true);
	});
}

function initialiseComponents() { 

	if ( jQuery( '[id^=add_filter_]' ).length )
		jQuery( '[id^=add_filter_]' ).change( convertQueryComponent );
	
	if ( jQuery('#add_batchmod_field').length )
		jQuery( '#add_batchmod_field').change(convertBatchModifyComponent );

	var comps = jQuery( 'tr.component td.filter select' );
	if ( comps.length > 0 ) {
		// For the query page
		for (var i = 0; i < comps.length; i++)
			reduceComponents( comps[i], null, true );
	}
	
	// Interestingly, Opera picks up .names in getElementById(), hence it being at the end now
	if ( jQuery( '#field-component' ) )
		reduceComponents( jQuery( '#field-component' )[0], null, true ); // For the new ticket page

	// now we need to query any radio groups for Mozilla breakage: http://www.quirksmode.org/js/tests/moz_radios.html
	var brokMoz = jQuery('input[type="radio"]');
	if ( brokMoz.length > 0 ) {
		for (var i = 0; i < brokMoz.length; i++)
			{ if (brokMoz[i]) brokMoz[i].checked = brokMoz[i].defaultChecked; }
	}
}

jQuery(document).ready(initialiseComponents);
