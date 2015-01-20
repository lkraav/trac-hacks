package org.trachacks.wikieditor.eclipse.plugin;

import java.io.File;

import org.eclipse.core.net.proxy.IProxyService;
import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.ui.plugin.AbstractUIPlugin;
import org.osgi.framework.BundleContext;
import org.osgi.util.tracker.ServiceTracker;
import org.trachacks.wikieditor.service.ServiceFactory;

/**
 * The activator class controls the plug-in life cycle
 */
public class Activator extends AbstractUIPlugin {

	// The plug-in ID
	public static final String PLUGIN_ID = "org.trachacks.wikieditor.eclipse.plugin"; //$NON-NLS-1$

	// The shared instance
	private static Activator plugin;
	
	private ServiceTracker tracker;
	
	/**
	 * The constructor
	 */
	public Activator() {
	}

	/*
	 * (non-Javadoc)
	 * @see org.eclipse.ui.plugin.AbstractUIPlugin#start(org.osgi.framework.BundleContext)
	 */
	public void start(BundleContext context) throws Exception {
		super.start(context);
		plugin = this;
		
        tracker = new ServiceTracker(getBundle().getBundleContext(), IProxyService.class.getName(), null);
        tracker.open();

		File cacheFolder = getStateLocation().append("wiki-cache") .toFile(); //$NON-NLS-1$
		cacheFolder.mkdirs();
		ServiceFactory.setCacheFolder(cacheFolder);
	}

	/*
	 * (non-Javadoc)
	 * @see org.eclipse.ui.plugin.AbstractUIPlugin#stop(org.osgi.framework.BundleContext)
	 */
	public void stop(BundleContext context) throws Exception {
		plugin = null;
		tracker.close();
		ServiceFactory.setCacheFolder(null);
		super.stop(context);
	}

	/**
	 * Returns the shared instance
	 *
	 * @return the shared instance
	 */
	public static Activator getDefault() {
		return plugin;
	}

	/**
	 * Returns an image descriptor for the image file at the given
	 * plug-in relative path
	 *
	 * @param path the path
	 * @return the image descriptor
	 */
	public static ImageDescriptor getImageDescriptor(String path) {
		return imageDescriptorFromPlugin(PLUGIN_ID, path);
	}
	
    public IProxyService getProxyService() {
		return (IProxyService) tracker.getService();
	}

}
