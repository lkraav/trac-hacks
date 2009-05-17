package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.util.ResourceBundle;

import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IAction;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.action.MenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.IActionBars;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchActionConstants;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.actions.ActionFactory;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.ide.IDEActionFactory;
import org.eclipse.ui.part.MultiPageEditorActionBarContributor;
import org.eclipse.ui.texteditor.ITextEditor;
import org.eclipse.ui.texteditor.ITextEditorActionConstants;
import org.eclipse.ui.texteditor.ITextEditorActionDefinitionIds;
import org.eclipse.ui.texteditor.RetargetTextEditorAction;

/**
 * Manages the installation/deinstallation of global actions for multi-page
 * editors. Responsible for the redirection of global actions to the active
 * editor. Multi-page contributor replaces the contributors for the individual
 * editors in the multi-page editor.
 */
public class WikiEditorContributor extends MultiPageEditorActionBarContributor {
	private IEditorPart activeEditorPart;

	private Action sampleAction;

	private RetargetTextEditorAction contentAssist;

	public static final String CONTENTASSIST_ACTION = "mm.eclipse.trac.editors.ContentAssist";

	/**
	 * Creates a multi-page contributor.
	 */
	public WikiEditorContributor() {
		super();
		contentAssist = new RetargetTextEditorAction(
				ResourceBundle.getBundle( this.getClass().getPackage().getName() + ".WikiEditorMessages" ), 
				"ContentAssistProposal.");
		String commandId = ITextEditorActionDefinitionIds.CONTENT_ASSIST_PROPOSALS;
		contentAssist.setActionDefinitionId(commandId);

		createActions();
	}

	/**
	 * Returns the action registed with the given text editor.
	 * 
	 * @return IAction or null if editor is null.
	 */
	protected IAction getAction(ITextEditor editor, String actionID) {
		return (editor == null ? null : editor.getAction(actionID));
	}

	public void setActivePage(IEditorPart part) {
		if (activeEditorPart == part)
			return;

		activeEditorPart = part;

		IActionBars actionBars = getActionBars();
		if (actionBars != null) {

			ITextEditor editor = (part instanceof ITextEditor) ? (ITextEditor) part
					: null;

			actionBars.setGlobalActionHandler(ActionFactory.DELETE.getId(),
					getAction(editor, ITextEditorActionConstants.DELETE));
			actionBars.setGlobalActionHandler(ActionFactory.UNDO.getId(),
					getAction(editor, ITextEditorActionConstants.UNDO));
			actionBars.setGlobalActionHandler(ActionFactory.REDO.getId(),
					getAction(editor, ITextEditorActionConstants.REDO));
			actionBars.setGlobalActionHandler(ActionFactory.CUT.getId(),
					getAction(editor, ITextEditorActionConstants.CUT));
			actionBars.setGlobalActionHandler(ActionFactory.COPY.getId(),
					getAction(editor, ITextEditorActionConstants.COPY));
			actionBars.setGlobalActionHandler(ActionFactory.PASTE.getId(),
					getAction(editor, ITextEditorActionConstants.PASTE));
			actionBars.setGlobalActionHandler(ActionFactory.SELECT_ALL.getId(),
					getAction(editor, ITextEditorActionConstants.SELECT_ALL));
			actionBars.setGlobalActionHandler(ActionFactory.FIND.getId(),
					getAction(editor, ITextEditorActionConstants.FIND));
			actionBars.setGlobalActionHandler(
					IDEActionFactory.BOOKMARK.getId(), getAction(editor,
							IDEActionFactory.BOOKMARK.getId()));
			actionBars.updateActionBars();
		}
	}

	private void createActions() {
		sampleAction = new Action() {
			public void run() {
				MessageDialog.openInformation(null, "Trac Plug-in",
						"Sample Action Executed");
			}
		};
		sampleAction.setText("Sample Action");
		sampleAction.setToolTipText("Sample Action tool tip");
		sampleAction.setImageDescriptor(PlatformUI.getWorkbench()
				.getSharedImages().getImageDescriptor(
						IDE.SharedImages.IMG_OBJS_TASK_TSK));
	}

	public void contributeToMenu(IMenuManager manager) {
		IMenuManager menu = new MenuManager("&Trac");
		manager.prependToGroup(IWorkbenchActionConstants.MB_ADDITIONS, menu);

		menu.add(sampleAction);
		menu.add(contentAssist);
	}

	public void contributeToToolBar(IToolBarManager manager) {
		manager.add(new Separator());
		manager.add(sampleAction);
		manager.add(contentAssist);
	}
}
