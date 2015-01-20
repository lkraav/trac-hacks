/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.nio.charset.Charset;
import java.util.Arrays;
import java.util.List;

import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.text.source.IVerticalRuler;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.mylyn.wikitext.core.parser.markup.MarkupLanguage;
import org.eclipse.mylyn.wikitext.ui.editor.WikiTextSourceEditor;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.CTabFolder;
import org.eclipse.swt.custom.CTabItem;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.events.SelectionListener;
import org.eclipse.swt.widgets.Composite;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class TracWikiMarkupEditor extends WikiTextSourceEditor {

	public static final String ID = TracWikiMarkupEditor.class.getName();

	private static final String UTF8 = "utf-8";
	public static final String DEFAULT_ENCODING = (Charset.isSupported(UTF8)) ? UTF8 : Charset.defaultCharset().displayName();
	
	private static final String TRACWIKI_MARKUP_LANGUAGE = "TracWiki";
	private static final List<String> WIKITEXT_TEST_CLASSNAMES = Arrays.asList("org.eclipse.mylyn.wikitext.core.WikiText", "org.eclipse.mylyn.wikitext.ui.WikiText");

	private CTabFolder tabFolder;
	private CTabItem sourceTab;	
	private CTabItem previewTab;
	private TracWikiPreview preview;

	
	public TracWikiMarkupEditor() {
		super();
		setDocumentProvider(new TracWikiDocumentProvider());
		setSourceViewerConfiguration(new TracMarkupSourceViewerConfiguration(getPreferenceStore()));
	}



	private MarkupLanguage getMarkupLanguage(String name) {
	    // Support for WikiText 2.0+ see
	    // http://help.eclipse.org/luna/topic/org.eclipse.mylyn.wikitext.help.ui/help/Upgrading-From-Mylyn-WikiText-1-x-to-2-x.html?cp=41_1_7_1#APIChangesin2.0
	    
	    Class wikiTextClass = null;
	    for (String className : WIKITEXT_TEST_CLASSNAMES) {
	        try {
	            wikiTextClass = getClass().forName(className);
	        } catch (ClassNotFoundException e1) {
	            // next
	        }
	        if (wikiTextClass != null) {
	            break;
	        }
	    }

	    if (wikiTextClass == null) {
                throw new RuntimeException("WikiText class not found in either " + WIKITEXT_TEST_CLASSNAMES);
	    }

	    try {
	        return (MarkupLanguage) wikiTextClass.getMethod("getMarkupLanguage", String.class).invoke(null, name);
	    } catch (Exception e) {
	        e.printStackTrace();
	        throw new RuntimeException(e);
	    }
	}

	@Override
	protected ISourceViewer createSourceViewer(Composite parent, IVerticalRuler ruler, int styles) {
		setMarkupLanguage(getMarkupLanguage(TRACWIKI_MARKUP_LANGUAGE));

		tabFolder = new CTabFolder(parent, SWT.BOTTOM);
		ISourceViewer viewer = super.createSourceViewer(tabFolder, ruler, styles);
		
		{
			sourceTab = new CTabItem(tabFolder, SWT.NONE);
			sourceTab.setText("Wiki Source");
			sourceTab.setToolTipText("Wiki Source");			
			sourceTab.setControl(viewer instanceof Viewer ? ((Viewer) viewer).getControl() : viewer.getTextWidget());
			tabFolder.setSelection(sourceTab);
		}
		
		{
			previewTab = new CTabItem(tabFolder, SWT.NONE);
			previewTab.setText("Preview");
			previewTab.setToolTipText("Preview");
			preview = new TracWikiPreview(tabFolder);
			previewTab.setControl(preview.getBrowser());

			tabFolder.addSelectionListener(new SelectionListener() {
				public void widgetDefaultSelected(SelectionEvent selectionevent) {
					widgetSelected(selectionevent);
				}

				public void widgetSelected(SelectionEvent selectionevent) {
					if (tabFolder.getSelection() == previewTab) {
						Page page = ((WikiEditorInput) getEditorInput()).getWikiPage();
						String editorText = getDocumentProvider().getDocument(getEditorInput()).get();					
						preview.showPreview(page, editorText);
					}
				}
			});
		}
		
		return viewer;
	}
	
}
