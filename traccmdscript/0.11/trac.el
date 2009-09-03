;; trac.el a simple wrapper around a command line trac tool
;; Nic Ferrier <nferrier@woome.com>

;; Todo:: 
;;
;; define derived mode from text-mode 
;;    with a keybinding of C-x C-w for save to trac
;;
;; delete the put buffer after the put has finished
;;    need another sentinel
;; 
;; setup a customizable variable for traccmd.py path.


;; Depends
;;
;; Nic's traccmd.py command line tool for trac
;;
;; xmlrpc interface for trac.

;; Usage
;; 
;; Login first with 
;;
;;   traccmd.py loginemacs
;;
;; or use an ini file to supply authentication details (see traccmd.py --help)
;;
;; To get a wiki page:
;;
;;   M-x trac-get <wikipagename>
;;
;; eg:
;;
;;   M-x trac-get releases
;;
;; gets the releases page


(defvar trac-page-meta '()
  "Used to store buffer local variable about each page")

(defun trac-get-sentinel (process signal)
  (cond
   ((equal signal "finished\n")
    (switch-to-buffer (buffer-name (process-buffer process)))
    (goto-char (point-min))
    (let ((meta-data (read (current-buffer))))
      (if (listp meta-data)
	  (progn
	    (goto-char (point-min))
	    (kill-sexp)
	    (kill-line)))
      (text-mode)
      ;; (auto-fill-mode)
      ;; Has to be set here because mode-sets trash them
      (make-local-variable 'trac-page-meta)
      (setq trac-page-meta meta-data))))
    )

(defun trac-save (page-meta)
  "Save the current trac buffer back to trac

Uses the page meta-data collected from the retrieval so expects
to use a buffer that was the result of that call."
  (interactive (list trac-page-meta))
  (if (not page-meta)
      (error "not in a trac page buffer!")
    (let ((page-name (plist-get
		      (plist-get page-meta :tracwikiproperties)
		      :name)))
      (let ((p (start-process-shell-command 
		"trac-wiki-put"
		(concat "*trac-wiki-put-channel-" page-name "*")
		"/home/nferrier/woome/sysops/dev/trac.py"
		"wikiput"
		page-name)))
	(process-send-region p (point-min) (point-max))
	(process-send-eof p)))))

(defun trac-get (page)
  "Get the wiki page specified into a buffer

The meta data associated with the page is removed from the page
content and made into a buffer local variable."
  (interactive "Mtrac page:")
  (let ((wiki-page-buffer-name (concat "*trac-wiki-channel-" page "*")))
    (if (get-buffer wiki-page-buffer-name)
	(with-current-buffer (get-buffer wiki-page-buffer-name)
	  (delete-region (point-min) (point-max))))
    (let ((p (start-process-shell-command 
	      "trac-wiki-get"
	      wiki-page-buffer-name
	      "~/trac.py"
	      "wiki"
	      page)))
      (set-process-sentinel p 'trac-get-sentinel)
      )))

;; End
