#@+leo-ver=5-thin
#@+node:ekr.20090701111504.5294: * @file contextmenu.py
#@+<< docstring >>
#@+node:ville.20090630210947.5460: ** << docstring >>
''' Defines various useful actions for context menus (Qt only).

Examples are:

- Edit in $EDITOR
- Edit @thin node in $EDITOR (remember to do "refresh" after this!)
- Refresh @thin node from disk (e.g. after editing it in external editor)
- Go to clone

A ``context-menu-open`` command is defined to allow opening the
tree context menu from the keyboard.

Here's an example on how to implement your own context menu items 
in your plugins::

    def nextclone_rclick(c,p, menu):
        """ Go to next clone """

        # only show the item if you are on a clone
        # this is what makes this "context sensitive"
        if not p.isCloned():
            return    

        def nextclone_rclick_cb():
            c.goToNextClone()

        # 'menu' is a QMenu instance that was created by Leo 
        # in response to right click on tree item

        action = menu.addAction("Go to clone")
        action.connect(action, QtCore.SIGNAL("triggered()"), nextclone_rclick_cb)

And call this in your plugin *once*::

    g.tree_popup_handlers.append(nextclone_rclick)    

'''
#@-<< docstring >>

__version__ = '0.0'
#@+<< version history >>
#@+node:ville.20090630210947.5461: ** << version history >>
#@@killcolor
#@+at
# 
# 0.1 Ville M. Vainio first version
# 
#@-<< version history >>

#@+<< imports >>
#@+node:ville.20090630210947.5462: ** << imports >>
from leo.core.leoQt import QtCore
    # Crashes pylint.

import os
import subprocess

import leo.core.leoGlobals as g
g.assertUi('qt')

#@-<< imports >>

#@+others
#@+node:ville.20090630210947.10190: ** globals
# print "Importing contextmenu"
inited = False
#@+node:ville.20110428163751.7685: ** guess_file_type
def guess_file_type(fname):
    base, ext = os.path.splitext(fname)
    ext = ext.lower()
    
    if ext in ['.txt']:
        return "@edit"
    return "@auto"
        
            
#@+node:ville.20090630210947.5465: ** openwith_rclick
def openwith_rclick(c,p, menu):
    """
    Show "Edit with" in context menu for external file root nodes (@thin, @auto...) 

    This looks like "Edit contextmenu.py in scite"

    """
    # define callbacks 
    #@+others
    #@+node:ekr.20140613141207.17666: *3* openwith_rclick_cb
    def openwith_rclick_cb():
        
        #print "Editing", path, fname        
        if editor:
            cmd = '%s "%s"' % (editor, absp)
            g.es('Edit: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True)
    #@+node:ekr.20140613141207.17667: *3* openfolder_rclick_cb
    def openfolder_rclick_cb():

        g.os_startfile(path)

    #@+node:ekr.20140613141207.17668: *3* create_rclick_cb
    def create_rclick_cb():

        os.makedirs(absp)
        g.es("Created " + absp)
    #@+node:ekr.20140613141207.17669: *3* importfiles_rclick_cb
    def importfiles_rclick_cb():
        
        def shorten(pth, prefix):
            if not pth.startswith(prefix):
                return pth
            return pth[len(prefix):]
        
        aList = g.get_directives_dict_list(p)
        path = c.scanAtPathDirectives(aList) + "/"
        table = [
            ("All files","*"),
            ("Python files","*.py"),
        ]
        fnames = g.app.gui.runOpenFileDialog(
            title = "Import files",filetypes = table, 
            defaultextension = '.notused',
            multiple=True, startpath = path)
        adds = [guess_file_type(pth) + " " + shorten(pth, path) for pth in fnames]
        for a in adds:
            chi = p.insertAsLastChild()
            chi.h = a
        c.readAtFileNodes()
    #@-others
    h = p.h
    parts = h.split(None, 1)
    if len(parts) < 2:
        return
    fname = None        
    # argh, we need g.getAbsFileName(c,p)
    head, bname = parts
    fname = p.anyAtFileNodeName()
    if not fname and head != "@path":
        return
    path = g.scanAllAtPathDirectives(c,p)
    editor = g.guessExternalEditor()
    # g.trace(repr(path),repr(fname))
    absp = g.os_path_finalize_join(path, fname)
    exists = os.path.exists(absp)
    if not exists and head == "@path":
        action = menu.addAction("Create dir " + absp + "/" )
        action.triggered.connect(create_rclick_cb)
    if exists and head == "@path":
        action = menu.addAction("Import files")
        action.triggered.connect(importfiles_rclick_cb)
    if editor and exists and head != "@path":
        action = menu.addAction("Edit " + bname + " in " + os.path.basename(editor))
        action.triggered.connect(openwith_rclick_cb)
    action = menu.addAction("Open " + path)
    action.triggered.connect(openfolder_rclick_cb)
#@+node:ville.20090630221949.5462: ** refresh_rclick
def refresh_rclick(c,p, menu):
    
    # define callback.
    #@+others
    #@+node:ekr.20140613141207.17671: *3* refresh_rclick_cb
    def refresh_rclick_cb():
        
        # Try to fix bug 1090950 refresh from disk: cut node ressurection.
        # This doesn't work--seems safer than previous code.
        at = c.atFileCommands
        p = c.p
        fn = p.anyAtFileNodeName()
        if fn:
            c.recreateGnxDict()
            i = g.skip_id(p.h,0,chars='@')
            word=p.h[0:i]
            if word == '@auto':
                p.deleteAllChildren()
                at.readOneAtAutoNode(fn,p)
            elif word in ('@thin','@file'):
                p.deleteAllChildren()
                at.read(p,force=True)
            elif word == '@shadow ':
                p.deleteAllChildren()
                at.read(p,force=True,atShadow=True)
            elif word == '@edit':
                p.deleteAllChildren()
                at.readOneAtEditNode(fn,p)
            else:
                g.trace('unknown:',word)
            c.redraw()
    #@-others
    split = p.h.split(None,1)
    if len(split) >= 2 and p.anyAtFileNodeName():
        typ = split[0]        
        action = menu.addAction("Refresh from disk")
        action.triggered.connect(refresh_rclick_cb)
        # action.connect(action, Qt.SIGNAL("triggered()"), refresh_rclick_cb)
#@+node:ville.20090701110830.10215: ** editnode_rclick
def editnode_rclick(c,p, menu):
    """ Provide "edit in EDITOR" context menu item """

    editor = g.guessExternalEditor()
    if editor:
        
        def editnode_rclick_cb():
            d = {'kind':'subprocess.Popen','args':[editor],'ext':None}
            c.openWith(d=d)
      
        action = menu.addAction("Edit in " + editor)
        action.triggered.connect(editnode_rclick_cb)
        # action.connect(action, Qt.SIGNAL("triggered()"), editnode_rclick_cb)
#@+node:ville.20090702171015.5480: ** nextclone_rclick
def nextclone_rclick(c,p, menu):
    """ Go to next clone """

    if p.isCloned():

        def nextclone_rclick_cb():
            c.goToNextClone()
    
        action = menu.addAction("Go to clone")
        action.triggered.connect(nextclone_rclick_cb)
        # action.connect(action, Qt.SIGNAL("triggered()"), nextclone_rclick_cb)
#@+node:ville.20090719202132.5248: ** marknodes_rclick
def marknodes_rclick(c,p, menu):
    """ Mark selected nodes """
    pl = c.getSelectedPositions()
    if any(not p.isMarked() for p in pl):
        def marknodes_rclick_cb():
            for p in pl:
                p.v.setMarked()
            c.redraw_after_icons_changed()      
        action = menu.addAction("Mark")
        action.triggered.connect(marknodes_rclick_cb)
        # markaction.connect(action, Qt.SIGNAL("triggered()"), marknodes_rclick_cb)
    if any(p.isMarked() for p in pl):
        def unmarknodes_rclick_cb():
            for p in pl:
                p.v.clearMarked()
            c.redraw_after_icons_changed()                        
        action = menu.addAction("Unmark")
        action.triggered.connect(unmarknodes_rclick_cb)
        # unmarkaction.connect(action, Qt.SIGNAL("triggered()"), unmarknodes_rclick_cb)
#@+node:ekr.20120311191905.9900: ** openurl_rclick
def openurl_rclick(c,p, menu):
    """ open an url """
    
    url = g.getUrlFromNode(p)
    if url:

        def openurl_rclick_cb():
            if not g.doHook("@url1",c=c,p=p,v=p,url=url):
                g.handleUrl(url,c=c,p=p)
            g.doHook("@url2",c=c,p=p,v=p)
    
        action = menu.addAction("Open URL")
        action.triggered.connect(openurl_rclick_cb)
        # action.connect(action,Qt.SIGNAL("triggered()"),openurl_rclick_cb)
#@+node:tbrown.20091203121808.15818: ** deletenodes_rclick
def deletenodes_rclick(c,p, menu):
    """ Delete selected nodes """

    u = c.undoer
    pl = c.getSelectedPositions()
    undoType = 'Delete Node'
    if len(pl) > 1:
        undoType += 's'
    current = p.copy()
    #@+<< define deletenodes_rclick_cb >>
    #@+node:ekr.20140613141207.17673: *3* << define deletenodes_rclick_cb >>
    def deletenodes_rclick_cb():
        
        if len(pl) == 1:
            # sometimes this may leave the selected node in a more
            # convenient place than the generalized case below
            c.deleteOutline()  # handles undo, redraw, etc.
            return
        c.endEditing()
        cull = []
        # try and find the best node to select when this is done
        nextviz = []
        tmp = pl[0].copy().moveToVisBack(c)
        if tmp:
            nextviz.append(tmp.v)
        tmp = pl[-1].copy().moveToVisNext(c)
        if tmp:
            nextviz.append(tmp.v)
        for nd in pl:
            cull.append((nd.v, nd.parent().v or None))
        u.beforeChangeGroup(current,undoType)
        for v, vp in cull:
            for pos in c.vnode2allPositions(v):
                if c.positionExists(pos) and pos.parent().v == vp:
                    bunch = u.beforeDeleteNode(pos)
                    pos.doDelete()
                    u.afterDeleteNode(pos,undoType,bunch)
                    c.setChanged(True)
                    break
        u.afterChangeGroup(current,undoType)
        # move to a node that still exists
        for v in nextviz:
            pos = c.vnode2position(v)
            if c.positionExists(pos):
                c.selectPosition(pos)
                break
        else:
            # c.selectPosition(c.allNodes_iter().next())
            c.selectPosition(c.rootPosition())
        c.redraw()         
    #@-<< define deletenodes_rclick_cb >>
    action = menu.addAction("Delete")
    action.triggered.connect(deletenodes_rclick_cb)
    # action.connect(action, Qt.SIGNAL("triggered()"), deletenodes_rclick_cb)
#@+node:ville.20091008192104.7691: ** configuredcommands_rclick
def configuredcommands_rclick(c,p, menu):
    """ Provide "edit in EDITOR" context menu item """
    config = c.config.getData('contextmenu_commands')
    if config:
        cmds = [el.split(None,1) for el in config]
        for cmd, desc in cmds:
            desc = desc.strip()
            action = menu.addAction(desc)
            #action.setToolTip(cmd)
            def create_callback(cm):
                return lambda: c.k.simulateCommand(cm)
            configcmd_rclick_cb = create_callback(cmd)
            action.triggered.connect(configcmd_rclick_cb)
            # action.connect(action,Qt.SIGNAL("triggered()"), configcmd_rclick_cb)
#@+node:ville.20090630210947.10189: ** install_handlers
def install_handlers():
    """ Install all the wanted handlers (menu creators) """

    hnd = [
        openwith_rclick, refresh_rclick, editnode_rclick,
        nextclone_rclick, marknodes_rclick,
        configuredcommands_rclick, deletenodes_rclick,
        openurl_rclick]

    g.tree_popup_handlers.extend(hnd)
    g.registerHandler("idle", editnode_on_idle)

    # just for kicks, the @commands

    #@+<< Add commands >>
    #@+node:ville.20090701224704.9805: *3* << Add commands >>
    # cm is 'contextmenu' prefix
    @g.command('cm-external-editor')
    def cm_external_editor_f(event):    
        """ Open node in external editor 

        Set LEO_EDITOR/EDITOR environment variable to get the editor you want.
        """
        c = event['c']
        pos = c.currentPosition()
        editor = g.guessExternalEditor()

        # c.openWith(data = ('subprocess.Popen', editor, None))
        d = {'kind':'subprocess.Popen','args':[editor],'ext':None}
        c.openWith(d=d)








    #@-<< Add commands >>


#@+node:ville.20090701142447.5473: ** editnode_on_idle
# frame.OnOpenWith creates the dict with the following entries:
# "body", "c", "encoding", "f", "path", "time" and "p".

def editnode_on_idle (tag,keywords):

    a = g.app
    if a.killed: return
    # g.trace('open with plugin')
    for dict in a.openWithFiles:
        path = dict.get("path")
        c = dict.get("c")
        encoding = dict.get("encoding",None)
        p = dict.get("p")
        old_body = dict.get("body")
        if path and os.path.exists(path):
            try:
                time = os.path.getmtime(path)
                # g.trace(path,time,dict.get('time'))
                if time and time != dict.get("time"):
                    dict["time"] = time # inhibit endless dialog loop.
                    # The file has changed.
                    #@+<< set s to the file text >>
                    #@+node:ville.20090701142447.5474: *3* << set s to the file text >>
                    try:
                        # Update v from the changed temp file.
                        f=open(path)
                        s=f.read()
                        f.close()
                    except:
                        g.es("can not open " + g.shortFileName(path))
                        break
                    #@-<< set s to the file text >>
                    #@+<< update p's body text >>
                    #@+node:ville.20090701142447.5475: *3* << update p's body text >>
                    # Convert body and s to whatever encoding is in effect.
                    body = p.b
                    body = g.toEncodedString(body,encoding,reportErrors=True)
                    s = g.toEncodedString(s,encoding,reportErrors=True)

                    conflict = body != old_body and body != s

                    # Set update if we should update the outline from the file.
                    if conflict:
                        # 2012/02/04: Don't raise dialog for files opened with vim.py, xemacs.py, etc.
                        paths = [z.get('path') for z in g.app.openWithFiles]
                        if path in paths:
                            update = True
                        else:
                            # See how the user wants to resolve the conflict.
                            g.error("conflict in " + g.shortFileName(path))
                            message = "Replace changed outline with external changes?"
                            result = g.app.gui.runAskYesNoDialog(c,"Conflict!",message)
                            update = result.lower() == "yes"
                    else:
                        update = s != body

                    if update:
                        g.blue("updated from: " + g.shortFileName(path))
                        s = g.toUnicode(s,encoding=encoding)
                        c.setBodyString(p,s)
                        #TL - 7/2/08 Converted to configurable 'goto node...'
                        if c.config.getBool('open_with_goto_node_on_update'):
                            c.selectPosition(p)
                        dict["body"] = s
                        # A patch by Terry Brown.
                        if c.config.getBool('open_with_save_on_update'):
                            c.save()
                    elif conflict:
                        g.blue("not updated from: " + g.shortFileName(path))
                    #@-<< update p's body text >>
            except Exception:
                # g.es_exception()
                pass
#@+node:ville.20090630210947.5463: ** init
def init ():
    global inited
    # print "contextmenu init()"
    if g.app.gui.guiName() != "qt":
        return False

    g.plugin_signon(__name__)
    # just run once
    if inited:
        return True

    inited= True
    install_handlers()        

    return True
#@+node:tbrown.20121123075838.19937: ** context_menu_open
@g.command('context-menu-open')
def context_menu_open(event):
    """Provide a command for key binding to open the context menu"""
    if 'c' in event:
        event['c'].frame.tree.onContextMenu(QtCore.QPoint(0,0))
#@-others
#@-leo
