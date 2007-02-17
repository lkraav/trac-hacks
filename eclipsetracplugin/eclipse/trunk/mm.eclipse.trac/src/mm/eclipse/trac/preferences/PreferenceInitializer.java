package mm.eclipse.trac.preferences;

import mm.eclipse.trac.Activator;

import org.eclipse.core.runtime.preferences.AbstractPreferenceInitializer;
import org.eclipse.jface.preference.IPreferenceStore;

/**
 * Class used to initialize default preference values.
 */
public class PreferenceInitializer extends AbstractPreferenceInitializer
{
    
    /*
     * (non-Javadoc)
     * 
     * @see org.eclipse.core.runtime.preferences.AbstractPreferenceInitializer#initializeDefaultPreferences()
     */
    public void initializeDefaultPreferences()
    {
        IPreferenceStore store = Activator.getDefault().getPreferenceStore();
        store.setDefault( Preferences.ServerURL, "http://localhost/trac/xmlrpc" );
        store.setDefault( Preferences.Username, "" );
        store.setDefault( Preferences.Password, "" );
    }
    
}
